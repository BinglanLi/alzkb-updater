# Project Reference

## File Tree

```
alzkb-updater/
├── config/
│   ├── project.yaml              # disease scope, ontology paths, node/edge type lists
│   ├── databases.yaml            # source databases, enabled flags, credentials
│   └── ontology_mappings.yaml   # column-to-ontology-property mappings
│
├── src/
│   ├── main.py                   # pipeline entry point; PARSERS registry; step orchestration
│   ├── parsers/
│   │   ├── base_parser.py        # BaseParser ABC
│   │   └── *.py                  # one file per source parser
│   ├── ontology/
│   │   └── populator.py          # OntologyPopulator (owlready2 + ista)
│   └── export/
│       └── memgraph_exporter.py  # MemgraphExporter (rdflib → CSV + Cypher)
│
├── data/
│   ├── raw/                      # downloaded source files (one subdir per source)
│   ├── processed/                # parsed TSV files (one subdir per source)
│   ├── ontology/                 # base OWL RDF (schema only, no individuals)
│   └── output/                   # populated RDF, node/edge CSVs, import.cypher
│
├── eval/                         # eval_after_parser.py, eval_after_ontology.py, eval_after_memgraph.py
├── test/
│   └── eval_parser.py            # legacy parser + mapping evaluation tool
│
├── docs/                         # overview.md, reference.md
├── .ista/                        # bundled ista library (pip install -e .ista)
└── run.sh                        # activates .venv and calls python src/main.py "$@"
```

## Parsers

| Class | Source | Access | Outputs |
|-------|--------|--------|---------|
| `AOPDBParser` | AOP-DB | Local MySQL | `drugs.tsv`, `pathways.tsv`, `gene_pathway.tsv` |
| `BgeeParser` | Bgee | HTTP | `anatomy_gene.tsv` |
| `BindingDBParser` | BindingDB | HTTP | `binding_data.tsv` |
| `CTDParser` | CTD | HTTP | `chemicals.tsv`, `chemical_disease.tsv`, `chemical_gene.tsv` |
| `DiseaseOntologyParser` | Disease Ontology | OBO file | `diseases.tsv` |
| `DisGeNETParser` | DisGeNET | REST API | `disease_classifications.tsv`, `disease_mappings.tsv`, `gene_disease_associations.tsv` |
| `DoRothEAParser` | DoRothEA/OmniPath | HTTP API | `tf_gene_interactions.tsv` |
| `DrugBankParser` | DrugBank | HTTP (credentials) | `drugs.tsv` |
| `DrugCentralParser` | DrugCentral | Local PostgreSQL | `drug_treats_disease.tsv`, `drug_palliates_disease.tsv`, `pharmacologic_classes.tsv`, `pharmacologic_class_includes_compound.tsv` |
| `GeneOntologyParser` | Gene Ontology | OBO file | `biological_process.tsv`, `molecular_function.tsv`, `cellular_component.tsv` |
| `GWASParser` | GWAS Catalog | HTTP | `gene_disease_associations.tsv` |
| `MEDLINECooccurrenceParser` | MEDLINE | Pre-computed files | `symptom_disease.tsv`, `disease_anatomy.tsv`, `disease_disease.tsv` |
| `MeSHParser` | MeSH | XML download | `symptoms.tsv` |
| `NCBIGeneParser` | NCBI Gene | NCBI FTP | `genes.tsv` |
| `PubTatorParser` | PubTator | NCBI FTP | `cooccurrence.tsv` |
| `UberonParser` | Uberon | OBO file | `anatomy.tsv` |

## Environment Variables

Set in `.env` at the project root. Loaded at startup via `python-dotenv`. Injected into parsers via `*_env` keys in `config/databases.yaml`.

| Variable | Required for |
|----------|-------------|
| `DISGENET_API_KEY` | DisGeNET REST API |
| `DRUGBANK_USERNAME` | DrugBank file download |
| `DRUGBANK_PASSWORD` | DrugBank file download |
| `MYSQL_USERNAME` | AOP-DB MySQL |
| `MYSQL_PASSWORD` | AOP-DB MySQL |
| `MYSQL_DB_NAME` | AOP-DB MySQL |

## Core Dependencies

| Package | Purpose |
|---------|---------|
| `pandas` | DataFrames in parsers and pipeline |
| `requests` | HTTP downloads and REST API calls |
| `pyyaml` | YAML config parsing |
| `python-dotenv` | `.env` loading |
| `owlready2` | OWL ontology loading and saving |
| `rdflib` | Populated RDF parsing for graph export |
| `obonet` | OBO format parsing (Gene Ontology, Uberon, Disease Ontology) |
| `pronto` | Alternative OBO parser |
| `ista` (bundled) | TSV → OWL individual population; `pip install -e .ista` |
| `psycopg2-binary` | DrugCentral PostgreSQL (install separately) |
