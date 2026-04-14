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
2. Verify outputs in `data/output/`: `nodes_*.csv`, `edges_*.csv`, and `import.cypher` are all present.


## Validating the Cypher script
Verify `import.cypher`:
- Each node type has both a `CREATE INDEX ON :NodeType;` and a `CREATE INDEX ON :NodeType(id);` statement.
- LOAD CSV paths use the `/import-data/` prefix (matching the Docker volume mount).
- Node labels match the ontology class names.
- Edge MATCH clauses are label-agnostic (`MATCH (a {id: row.start_id})`) — safe when node IDs have type-specific prefixes.
</export-memgraph>


<issues>

</issues>