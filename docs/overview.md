# Pipeline Overview

alzkb-updater is a template for building disease-specific biomedical knowledge graphs from public databases. AlzKB (Alzheimer's Knowledge Base) is the reference implementation. A completed pipeline run produces a graph importable into Memgraph for downstream queries.

## Pipeline Steps

Steps 1–4 run in sequence via `python src/main.py`.

```
1. Extract      — parsers download source data, return DataFrames
                   → data/raw/<source>/
2. Export TSV   — DataFrames written to disk
                   → data/processed/<source>/<name>.tsv
3. Populate     — OntologyPopulator reads TSVs + OWL schema
                   → data/output/*_populated.rdf
4. Export Graph — MemgraphExporter reads populated RDF
                   → data/output/nodes_<Type>.csv
                   → data/output/edges_<Rel>.csv
                   → data/output/import.cypher
```

Two evaluation tools run independently of the main pipeline:
- `test/eval_parser.py` — validates per-parser TSV output against `ontology_mappings.yaml` and `get_schema()`
- `eval/eval_after_parser.py`, `eval_after_ontology.py`, `eval_after_memgraph.py` — validate outputs at each pipeline stage

## Config Files

| File | Controls |
|------|----------|
| `config/databases.yaml` | Which parsers run; constructor args and credentials |
| `config/project.yaml` | Active OWL class and property names; disease scope; ontology file paths |
| `config/ontology_mappings.yaml` | How each TSV column maps to OWL types and properties; processing order |

All three are loaded once at startup by `load_config()` in `src/main.py`.

## Cross-Module Contracts

Six invariants must hold for the pipeline to produce correct output. **Violations fail silently — no runtime error is raised.**

1. **Source name consistency** — `databases.yaml` key = `PARSERS` key (`main.py`) = `ontology_mappings.yaml` entry prefix = `data/processed/<source>/` subdirectory. All must be identical strings.
2. **TSV filename stems** — `parse_data()` return dict keys become TSV stems. Each `source_filename` in `ontology_mappings.yaml` must exactly match one stem.
3. **Column name agreement** — Every column name referenced in `ontology_mappings.yaml` must exist in the TSV. `get_schema()` must exactly match `parse_data()` output.
4. **Node-before-relationship ordering** — All node entries must precede relationship entries in `ontology_mappings.yaml`. A relationship entry processed before its subject or object nodes produces zero edges with no error.
5. **OWL name validity** — `node_type` and `relationship_type` values must exist as OWL classes/properties in `data/ontology/alzkb_v2.rdf` AND be active (uncommented) in `project.yaml` `node_types`/`edge_types`.
6. **`_env` credential injection** — `_resolve_env_vars()` in `main.py` strips the `_env` suffix and resolves the value from the environment at startup. Unset variables silently become `None` — no error is raised until the parser tries to use the credential.
