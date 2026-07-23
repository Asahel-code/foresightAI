from pathlib import Path

from rdflib import RDF, OWL, URIRef

from app.services.knowledge_graph_utils import (
    build_data_namespace,
    build_data_uri,
    build_graph_output_path,
    load_ontology_graph,
    normalize_region_code,
)


def test_region_normalization_and_uri_generation():
    assert normalize_region_code("KE") == "ke"
    assert normalize_region_code(None) == "global"
    assert build_data_namespace("KE") == "http://www.foresightai.org/data/ke/"
    assert build_data_uri("KE", "location_Tana_River") == "http://www.foresightai.org/data/ke/location_tana_river"
    assert build_graph_output_path("UG") == "ug_pilot.ttl"


def test_ontology_graph_contains_core_terms():
    repo_root = Path(__file__).resolve().parents[2]
    graph = load_ontology_graph(project_root=str(repo_root))

    assert (URIRef("http://www.foresightai.org/ontology/core#Exposure"), RDF.type, OWL.Class) in graph
    assert (URIRef("http://www.foresightai.org/ontology/core#hasLocation"), RDF.type, OWL.ObjectProperty) in graph
