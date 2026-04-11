---
name: mapping-protocol
description: Use this when mapping TSV or CSV columns to OWL ontology properties
---

## Your role
You own `config/ontology_mappings.yaml`. You map columns in processed TSV files
to node types and relationship types in the OWL ontology.

<overview>
You own `config/ontology_mappings.yaml`. You map CSV or TSV columns to node types and relationship types in the OWL ontology (data/ontology/alzkb_v2.rdf) by modifying `config/ontology_mappings.yaml`.
</overview>


<map-ontology>
## Before editing ontology_mappings.yaml
1. Inspect `data/processed/{source}/` to understand available columns.
2. Identify any schema mismatch or missing property first.
3. Stop and seek human feedback for mismatched entities or properties.
4. Resolve all ontology errors before populating.

## parse_config structure
For nodes:
  id_column: column used as the individual's IRI
  label_column: column used as the display label
  data_property_map: {tsv_column: ontology_data_property_name}
  merge_column: {column_name: col, data_property: prop}  # for deduplication

For relationships:
  subject_node_type: ontology class name for the subject
  object_node_type: ontology class name for the object
  subject_match_property: data property used to match subject individuals
  object_match_property: data property used to match object individuals

## When ontology types are missing
Seek human approval and feedback on options:
- update columsn (rewriting parsers)
- add to ontology
- skip the column
</map-ontology>
