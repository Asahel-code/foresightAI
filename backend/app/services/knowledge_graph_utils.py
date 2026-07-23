import os
from pathlib import Path

from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef


def slugify(text: str) -> str:
    """Convert a display name to a URL-safe slug."""
    return (
        text.lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
        .replace("-", "_")
        .replace(",", "")
        .replace(".", "")
    )


def normalize_region_code(country_code: str | None) -> str:
    """Normalize a country code so it can be used in RDF IRIs."""
    if not country_code:
        return "global"
    return country_code.strip().lower()


def build_data_namespace(country_code: str | None) -> str:
    """Build the data namespace root for a given country or region."""
    return f"http://www.foresightai.org/data/{normalize_region_code(country_code)}/"


def build_data_uri(country_code: str | None, resource_name: str) -> str:
    """Build a region-aware RDF resource IRI."""
    return f"{build_data_namespace(country_code)}{slugify(resource_name)}"


def build_target_uri(location_name: str, country_code: str | None) -> str:
    """Build the target location IRI used by reasoning queries."""
    return build_data_uri(country_code, f"location_{location_name}")


def build_graph_output_path(country_code: str | None, output_dir: str | None = None) -> str:
    """Resolve the expected RDF graph file path for a region."""
    region = normalize_region_code(country_code)
    filename = f"{region}_pilot.ttl"
    if output_dir:
        return os.path.join(output_dir, filename)
    return filename


def load_ontology_graph(project_root: str | None = None) -> Graph:
    """Load the ontology vocabulary into a graph, tolerating parser issues in the OWL files."""
    root = Path(project_root or os.getcwd()).resolve()
    ontology_dir = root / "ontology"
    graph = Graph()

    core_ns = Namespace("http://www.foresightai.org/ontology/core#")
    geo_ns = Namespace("http://www.foresightai.org/ontology/geography#")
    haz_ns = Namespace("http://www.foresightai.org/ontology/hazards#")
    ds_ns = Namespace("http://www.foresightai.org/ontology/datasets#")

    graph.bind("core", core_ns)
    graph.bind("geo", geo_ns)
    graph.bind("haz", haz_ns)
    graph.bind("ds", ds_ns)
    graph.bind("owl", OWL)
    graph.bind("rdfs", RDFS)

    ontology_files = [
        ontology_dir / "core" / "foresight.owl",
        ontology_dir / "geography" / "geography.owl",
        ontology_dir / "hazards" / "hazards.owl",
        ontology_dir / "datasets" / "datasets.owl",
    ]

    for ontology_file in ontology_files:
        if not ontology_file.exists():
            continue
        try:
            graph.parse(ontology_file, format="xml")
        except Exception:
            if ontology_file.name == "foresight.owl":
                graph.add((URIRef(str(core_ns)[:-1]), RDF.type, OWL.Ontology))
                graph.add((URIRef(str(core_ns)[:-1]), OWL.imports, URIRef("http://www.foresightai.org/ontology/geography")))
                graph.add((URIRef(str(core_ns)[:-1]), OWL.imports, URIRef("http://www.foresightai.org/ontology/hazards")))
                graph.add((URIRef(str(core_ns)[:-1]), OWL.imports, URIRef("http://www.foresightai.org/ontology/datasets")))
                for term in [
                    core_ns.Exposure,
                    core_ns.Vulnerability,
                    core_ns.Impact,
                    core_ns.EarlyAction,
                    core_ns.hasLocation,
                    core_ns.hasDescription,
                    core_ns.hasEstimatedCost,
                    core_ns.hasAffectedPopulation,
                    core_ns.hasLeadTimeHours,
                ]:
                    graph.add((term, RDF.type, OWL.Class if str(term).endswith(("Exposure", "Vulnerability", "Impact", "EarlyAction")) else OWL.ObjectProperty))
            elif ontology_file.name == "geography.owl":
                graph.add((URIRef(str(geo_ns)[:-1]), RDF.type, OWL.Ontology))
                graph.add((geo_ns.Location, RDF.type, OWL.Class))
                graph.add((geo_ns.hasName, RDF.type, OWL.DatatypeProperty))
                graph.add((geo_ns.hasLatitude, RDF.type, OWL.DatatypeProperty))
                graph.add((geo_ns.hasLongitude, RDF.type, OWL.DatatypeProperty))
            elif ontology_file.name == "hazards.owl":
                graph.add((URIRef(str(haz_ns)[:-1]), RDF.type, OWL.Ontology))
                graph.add((haz_ns.Hazard, RDF.type, OWL.Class))
                graph.add((haz_ns.Observation, RDF.type, OWL.Class))
                graph.add((haz_ns.observes, RDF.type, OWL.ObjectProperty))
                graph.add((haz_ns.hasType, RDF.type, OWL.DatatypeProperty))
                graph.add((haz_ns.hasTimestamp, RDF.type, OWL.DatatypeProperty))
                graph.add((haz_ns.hasValue, RDF.type, OWL.DatatypeProperty))
                graph.add((haz_ns.hasUnit, RDF.type, OWL.DatatypeProperty))
            elif ontology_file.name == "datasets.owl":
                graph.add((URIRef(str(ds_ns)[:-1]), RDF.type, OWL.Ontology))
                graph.add((ds_ns.Dataset, RDF.type, OWL.Class))
                graph.add((ds_ns.DataSource, RDF.type, OWL.Class))
                graph.add((ds_ns.hasSource, RDF.type, OWL.ObjectProperty))
                graph.add((ds_ns.hasSourceURL, RDF.type, OWL.DatatypeProperty))
                graph.add((ds_ns.hasFormat, RDF.type, OWL.DatatypeProperty))
                graph.add((ds_ns.lastIngested, RDF.type, OWL.DatatypeProperty))

    return graph
