import os
import json
import re
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from rdflib import Graph
from app.models import models, schemas
from app.services import sparql_queries
from app.services.knowledge_graph_utils import build_graph_output_path, build_target_uri, load_ontology_graph
from openai import OpenAI


# Cache the graph so we don't load it on every request
_RDF_GRAPHS: dict[str, Graph] = {}


def get_graph(country_code: str | None = None) -> Graph:
    global _RDF_GRAPHS
    normalized_code = (country_code or "global").strip().lower()

    if normalized_code not in _RDF_GRAPHS:
        graph = Graph()
        graph_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "knowledge-graph"))
        ttl_path = os.environ.get("KG_OUTPUT_PATH")
        if not ttl_path:
            ttl_path = build_graph_output_path(normalized_code, graph_dir)
        if not os.path.exists(ttl_path) and normalized_code != "global":
            fallback = build_graph_output_path("ke", graph_dir)
            if os.path.exists(fallback):
                ttl_path = fallback
        if not os.path.exists(ttl_path):
            ttl_path = os.path.abspath(os.path.join(graph_dir, f"{normalized_code}_pilot.ttl"))
        if os.path.exists(ttl_path):
            print(f"Loading RDF Graph from {ttl_path}...")
            graph.parse(ttl_path, format="turtle")
        else:
            print(f"WARNING: Knowledge graph file not found at {ttl_path}")

        ontology_graph = load_ontology_graph(project_root=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
        if len(ontology_graph):
            graph += ontology_graph

        _RDF_GRAPHS[normalized_code] = graph

    return _RDF_GRAPHS[normalized_code]

def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9_]', '', text.lower().replace(" ", "_"))

def run_reasoning_and_recommendation(db: Session, location_id: int, hazard_type: str = "flood") -> schemas.RecommendationOut:
    location = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not location:
        raise ValueError(f"Location ID {location_id} not found")

    target_uri = build_target_uri(location.name, location.country_code)
    
    g = get_graph(location.country_code)
    
    # 1. Run Hazard Query
    q_haz = sparql_queries.GET_HAZARD_OBSERVATIONS.replace("{target_uri}", target_uri).replace("{hazard_type}", hazard_type)
    haz_results = g.query(q_haz)
    
    hazards_found = []
    highest_status = "normal"
    status_weights = {"normal": 0, "warning": 1, "critical": 2}
    
    for row in haz_results:
        val, unit, status, dt, src = row
        status_str = str(status)
        hazards_found.append({
            "value": float(val), "unit": str(unit), "status": status_str, "date": str(dt), "source": str(src)
        })
        if status_weights.get(status_str, 0) > status_weights.get(highest_status, 0):
            highest_status = status_str

    # 2. Run Exposure Query
    q_exp = sparql_queries.GET_EXPOSED_ASSETS.replace("{target_uri}", target_uri)
    exp_results = g.query(q_exp)
    
    assets_found = []
    total_population_at_risk = 0
    for row in exp_results:
        name, a_type, pop, val = row
        pop_val = int(pop) if pop else 0
        total_population_at_risk += pop_val
        assets_found.append({
            "name": str(name), "type": str(a_type), "population": pop_val, "value_usd": float(val) if val else 0.0
        })

    # 3. Run Vulnerability Query
    q_vuln = sparql_queries.GET_VULNERABILITY_INDICATORS.replace("{target_uri}", target_uri)
    vuln_results = g.query(q_vuln)
    
    vuln_found = []
    for row in vuln_results:
        ind, val, unit = row
        vuln_found.append({"indicator": str(ind), "value": float(val), "unit": str(unit)})

    # 4. Run Early Actions Query
    q_acts = sparql_queries.GET_EARLY_ACTIONS.replace("{hazard_type}", hazard_type)
    acts_results = g.query(q_acts)
    
    actions_found = []
    for row in acts_results:
        name, desc = row
        actions_found.append({"action": str(name), "description": str(desc)})

    # 5. Synthesize Recommendation & Reasoning Chain
    reasoning_chain = {
        "target_location": location.name,
        "target_uri": target_uri,
        "hazard_status": highest_status,
        "hazard_evidence": hazards_found,
        "exposure_evidence": {
            "total_assets": len(assets_found), 
            "population_at_risk": total_population_at_risk, 
            "assets": assets_found
        },
        "vulnerability_evidence": vuln_found,
        "mitigation_actions": actions_found
    }

    if highest_status == "critical":
        acts_str = ", ".join([a['action'] for a in actions_found[:3]])
        rec_text = f"CRITICAL {hazard_type.upper()} ALERT for {location.name}. Immediate action required. {total_population_at_risk} people are at risk across {len(assets_found)} critical assets. Proceed with early actions: {acts_str}."
    elif highest_status == "warning":
        rec_text = f"{hazard_type.capitalize()} Warning for {location.name}. Monitor conditions closely. Prepare early actions for {len(assets_found)} exposed assets."
    else:
        rec_text = f"Conditions in {location.name} are normal. Continue standard monitoring."

    # --- LLM ENHANCEMENT START ---
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        try:
            client = OpenAI(api_key=openai_api_key)
            prompt = f"""You are an expert crisis analyst for ForeSightAI.
Based on the following semantic reasoning evidence, synthesize a short, professional "Early Warning Brief" (1-2 paragraphs max).
Only use facts present in the provided evidence. Summarize the hazard severity, the exposed assets/population, and format the early actions into a professional crisis brief.

Evidence:
{json.dumps(reasoning_chain, indent=2)}
"""
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            llm_text = response.choices[0].message.content.strip()
            if llm_text:
                rec_text = llm_text
        except Exception as e:
            print(f"LLM enhancement failed, falling back to rule-based string. Error: {e}")
    # --- LLM ENHANCEMENT END ---

    # Create and store the recommendation
    db_recommendation = models.Recommendation(
        location_id=location_id,
        hazard_level=highest_status,
        recommendation_text=rec_text,
        reasoning_chain=json.dumps(reasoning_chain, indent=2),
        created_at=datetime.now(UTC)
    )
    db.add(db_recommendation)
    db.commit()
    db.refresh(db_recommendation)

    return schemas.RecommendationOut.model_validate(db_recommendation)
