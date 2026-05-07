# AlzKB Updater

A pipeline for building and updating the [Alzheimer's Knowledge Base (AlzKB)](https://github.com/EpistasisLab/AlzKB) — a disease-specific knowledge graph integrating data from 16 biomedical databases.

## Overview

The pipeline runs four steps in sequence:

```
1. Extract   — download and parse data from biomedical databases
2. Export TSV — save parsed DataFrames to data/processed/
3. Populate  — populate the OWL ontology using ista
4. Export graph — write Memgraph-compatible CSV files to data/output/
```

Configuration lives in `config/`:
- `project.yaml` — disease scope (Alzheimer's terms, UMLS CUIs, drug names)
- `databases.yaml` — which sources to enable and their access credentials
- `ontology_mappings.yaml` — how parsed columns map to ontology properties

## Installation

**Prerequisites:** Python 3.8+, MySQL (for AOP-DB), PostgreSQL (for DrugCentral), Git

```bash
git clone https://github.com/BinglanLi/alzkb-updater.git
cd alzkb-updater

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

# Install ista (bundled in .ista/)
pip install -e .ista
```

**Credentials** — create a `.env` file:
```bash
DISGENET_API_KEY=your_key_here
DRUGBANK_USERNAME=your_username
DRUGBANK_PASSWORD=your_password
MYSQL_USERNAME=root
MYSQL_PASSWORD=your_password
MYSQL_DB_NAME=aopdb
```

## Usage

```bash
# Full pipeline
python src/main.py

# Run and export a single source (useful for testing)
python src/main.py --source disgenet

# Verbose output
python src/main.py --log-level DEBUG

# Re-download source files even if they already exist
python src/main.py --force-download
```

Output files appear in `data/output/`:
- `alzkb_v2_populated.rdf` — populated OWL ontology
- `nodes_{NodeType}.csv` — one CSV per node type (Gene, Drug, Disease, …)
- `edges_{RelType}.csv` — one CSV per relationship type
- `import.cypher` — Cypher LOAD CSV script; paste into Memgraph Lab to load the graph

Logs are written to `kg_build.log`.

## Interactive use (Jupyter)

Open `run_individual_components.ipynb` to run parsers one at a time. This is useful for debugging a specific source without running the full pipeline.

## Configuration

### Enable a data source

Edit `config/databases.yaml`:
```yaml
disgenet:
  enabled: true          # change to false to skip
  args:
    api_key_env: DISGENET_API_KEY
```

### Change disease scope

Edit `config/project.yaml`:
```yaml
project:
  disease_scope:
    primary_terms:
      - "alzheimer"
      - "alzheimer's disease"
    umls_cuis:
      - "C0002395"
```

## Adding a new data source

1. Create a parser in `src/parsers/`:

```python
from .base_parser import BaseParser

class MySourceParser(BaseParser):
    def download_data(self) -> bool:
        # download files to self.source_dir
        return True

    def parse_data(self) -> dict[str, pd.DataFrame]:
        # return {"table_name": dataframe, ...}
        return {}

    def get_schema(self) -> dict:
        return {}
```

2. Register it in `src/main.py`:

```python
PARSERS = {
    ...
    "mysource": MySourceParser,
}
```

3. Add an entry to `config/databases.yaml`:

```yaml
mysource:
  enabled: true
  args:
    api_key_env: MYSOURCE_API_KEY
  notes: "Brief description."
```

4. Add ontology mappings to `config/ontology_mappings.yaml`.

## Project structure

```
alzkb-updater/
├── config/
│   ├── project.yaml              # disease scope, ontology settings
│   ├── databases.yaml            # source databases and credentials
│   └── ontology_mappings.yaml    # column-to-ontology-property mappings
├── src/
│   ├── main.py                   # pipeline entry point (read this first)
│   ├── parsers/                  # 16 source parsers
│   │   ├── base_parser.py
│   │   ├── aopdb_parser.py
│   │   ├── bgee_parser.py
│   │   ├── bindingdb_parser.py
│   │   ├── ctd_parser.py
│   │   ├── disease_ontology_parser.py
│   │   ├── disgenet_parser.py
│   │   ├── dorothea_parser.py
│   │   ├── drugbank_parser.py
│   │   ├── drugcentral_parser.py
│   │   ├── gene_ontology_parser.py
│   │   ├── gwas_parser.py
│   │   ├── medline_cooccurrence_parser.py
│   │   ├── mesh_parser.py
│   │   ├── ncbigene_parser.py
│   │   ├── pubtator_parser.py
│   │   └── uberon_parser.py
│   ├── ontology/
│   │   └── populator.py          # OWL population via ista
│   └── export/
│       └── memgraph_exporter.py  # typed CSV export for Memgraph
├── data/
│   ├── raw/                      # downloaded source files
│   ├── processed/                # parsed TSV files (one folder per source)
│   ├── ontology/                 # base OWL ontology
│   └── output/                   # final outputs
├── eval/                            # eval_after_parser.py, eval_after_ontology.py, eval_after_memgraph.py
├── docs/                            # overview.md, reference.md
├── run_individual_components.ipynb  # run parsers interactively
├── run.sh                           # convenience wrapper
└── requirements.txt
```

## Data sources

| Source | Parser | Access |
|--------|--------|--------|
| AOP-DB | `AOPDBParser` | Local MySQL |
| Bgee | `BgeeParser` | HTTP download |
| BindingDB | `BindingDBParser` | HTTP download |
| CTD | `CTDParser` | HTTP download |
| Disease Ontology | `DiseaseOntologyParser` | OBO file |
| DisGeNET | `DisGeNETParser` | REST API (key required) |
| DoRothEA | `DoRothEAParser` | OmniPath API |
| DrugBank | `DrugBankParser` | HTTP download (credentials required) |
| DrugCentral | `DrugCentralParser` | Local PostgreSQL |
| Gene Ontology | `GeneOntologyParser` | OBO file |
| GWAS Catalog | `GWASParser` | HTTP download |
| MEDLINE | `MEDLINECooccurrenceParser` | NCBI E-utilities (PubMed) |
| MeSH | `MeSHParser` | XML download |
| NCBI Gene | `NCBIGeneParser` | NCBI FTP |
| PubTator | `PubTatorParser` | NCBI FTP |
| Uberon | `UberonParser` | OBO file |

## Troubleshooting

**`ista` not found:**
```bash
pip install -e .ista
```

**MySQL connection failed:** verify MySQL is running and credentials in `.env` are correct.

**PostgreSQL connection failed (DrugCentral):** load the dump first — `gunzip -c drugcentral.sql.gz | psql drugcentral` — then verify `psql drugcentral` connects without a password prompt.

**API authentication failed:** check API keys in `.env`.

**Download failed:** some sources need manual download — check the log for instructions.

## Further reading

- [`docs/overview.md`](docs/overview.md) — pipeline step details, config file contracts, and cross-module invariants
- [`docs/reference.md`](docs/reference.md) — full parser table, environment variables, and dependency list

## References

- [AlzKB original](https://github.com/EpistasisLab/AlzKB)
- [ista](https://github.com/RomanoLab/ista)
- [Hetionet](https://het.io/)
- [OmniPath/DoRothEA](https://omnipathdb.org/)
