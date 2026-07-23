PREFIXES = """
PREFIX core: <http://www.foresightai.org/ontology/core#>
PREFIX haz: <http://www.foresightai.org/ontology/hazards#>
PREFIX geo: <http://www.foresightai.org/ontology/geography#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

# Find the most recent hazard observations for a target location (or any of its sub-locations)
GET_HAZARD_OBSERVATIONS = PREFIXES + """
SELECT ?value ?unit ?status ?date ?source
WHERE {
    ?obs a haz:Observation ;
         haz:observes ?hazard ;
         haz:hasValue ?value ;
         haz:hasUnit ?unit ;
         haz:hasTimestamp ?date ;
         core:hasStatus ?status ;
         core:hasDataSource ?source ;
         core:hasLocation ?loc .
         
    ?hazard haz:hasType ?hazardType .
    
    # Include the location itself and any child locations (e.g. sub-counties)
    ?loc core:isPartOf* <{target_uri}> .
    
    FILTER(?hazardType = "{hazard_type}")
}
ORDER BY DESC(?date)
LIMIT 10
"""

# Find exposure assets in the target location or its sub-locations
GET_EXPOSED_ASSETS = PREFIXES + """
SELECT ?assetName ?assetType ?population ?valueUsd
WHERE {
    ?asset a core:Exposure ;
           rdfs:label ?assetName ;
           core:hasAssetType ?assetType ;
           core:hasLocation ?loc .
           
    OPTIONAL { ?asset core:hasAffectedPopulation ?population }
    OPTIONAL { ?asset core:hasEstimatedCost ?valueUsd }

    ?loc core:isPartOf* <{target_uri}> .
}
ORDER BY ?assetName
"""

# Get vulnerability indicators specifically for the target location
GET_VULNERABILITY_INDICATORS = PREFIXES + """
SELECT ?indicatorName ?value ?unit
WHERE {
    ?ind a core:Vulnerability ;
         core:hasIndicatorName ?indicatorName ;
         core:hasIndicatorValue ?value ;
         core:hasIndicatorUnit ?unit ;
         core:hasLocation <{target_uri}> .
}
ORDER BY ?indicatorName
"""

# Get early actions that mitigate the specific hazard
GET_EARLY_ACTIONS = PREFIXES + """
SELECT ?actionName ?description
WHERE {
    ?action a core:EarlyAction ;
            rdfs:label ?actionName ;
            core:hasDescription ?description ;
            core:mitigates ?hazard .
            
    ?hazard haz:hasType ?hazardType .
    FILTER(?hazardType = "{hazard_type}")
}
"""
