---
name: memgraph-protocol
description: Use this when exporting the populated ontology to Memgraph
---

<overview>
The `export_graph` step converts the populated RDF ontology into typed CSV files and a Cypher LOAD CSV import script for Memgraph.

</overview>

<prerequisite>
Confirm `data/output/alzkb_v2_populated.rdf` exist.
</prerequisite>

<export-memgraph>

# Run exporting
1. Call `run_export_graph()`.
2. Verify outputs: call `list_output_files()` — .


## Validating the Cypher script
Verify outputs:
- Ensure the expected nodes_*.csv, edges_*.csv, and import.cypher
- Each node type has a CREATE CONSTRAINT or CREATE INDEX statement.
- LOAD CSV paths match the actual CSV filenames in data/output/.
- Node labels match the ontology class names.
</export-memgraph>


<issues>

</issues>