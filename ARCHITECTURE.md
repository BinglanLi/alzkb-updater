# AlzKB-updater-mcp Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     AlzKB Updater System                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Data Sources (APIs)                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │   UniProt API    │              │  PubChem API     │        │
│  │  (Proteins)      │              │  (Compounds)     │        │
│  └──────────────────┘              └──────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
           │                                    │
           │                                    │
           ▼                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Retrieval Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │ UniProtRetriever │              │PubChemRetriever  │        │
│  │                  │              │                  │        │
│  │ • Rate limiting  │              │ • Rate limiting  │        │
│  │ • Error handling │              │ • Error handling │        │
│  │ • Schema def     │              │ • Schema def     │        │
│  └──────────────────┘              └──────────────────┘        │
│           │                                    │                 │
│           └────────────────┬───────────────────┘                │
│                            │                                     │
│                  ┌─────────▼─────────┐                          │
│                  │  BaseRetriever    │                          │
│                  │  (Abstract Base)  │                          │
│                  └───────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Data Processing Layer                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │  DataCleaner     │              │ DataIntegrator   │        │
│  │                  │              │                  │        │
│  │ • Text cleaning  │──────────────▶ • Multi-source  │        │
│  │ • Deduplication  │              │   integration    │        │
│  │ • Validation     │              │ • Metadata       │        │
│  └──────────────────┘              │ • Statistics     │        │
│                                     └──────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Export Layer                                 │
├─────────────────────────────────────────────────────────────────┤
│                   ┌──────────────────┐                          │
│                   │  CSVExporter     │                          │
│                   │                  │                          │
│                   │ • Timestamped    │                          │
│                   │ • Per-source     │                          │
│                   │ • Metadata       │                          │
│                   └──────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Output Files                                 │
├─────────────────────────────────────────────────────────────────┤
│  • alzkb_uniprot_YYYYMMDD.csv                                   │
│  • alzkb_pubchem_YYYYMMDD.csv                                   │
│  • alzkb_summary_YYYYMMDD.csv                                   │
│  • alzkb_metadata_YYYYMMDD.csv                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
1. RETRIEVAL
   ┌─────────────┐
   │ API Request │ ──▶ Rate Limited
   └─────────────┘
         │
         ▼
   ┌─────────────┐
   │ Response    │ ──▶ Error Handled
   └─────────────┘
         │
         ▼
   ┌─────────────┐
   │ DataFrame   │ ──▶ Schema Validated
   └─────────────┘

2. CLEANING
   ┌─────────────┐
   │ Raw Data    │
   └─────────────┘
         │
         ▼
   ┌─────────────┐
   │ Text Clean  │ ──▶ Remove whitespace, normalize
   └─────────────┘
         │
         ▼
   ┌─────────────┐
   │ Deduplicate │ ──▶ Remove exact duplicates
   └─────────────┘
         │
         ▼
   ┌─────────────┐
   │ Validate    │ ──▶ Check schema, types
   └─────────────┘

3. INTEGRATION
   ┌─────────────┐
   │ Source 1    │ ──┐
   └─────────────┘   │
                     ├──▶ ┌─────────────┐
   ┌─────────────┐   │    │ Knowledge   │
   │ Source 2    │ ──┘    │ Base        │
   └─────────────┘        └─────────────┘
                                │
                                ▼
                          ┌─────────────┐
                          │ + Metadata  │
                          │ + Timestamps│
                          └─────────────┘

4. EXPORT
   ┌─────────────┐
   │ Knowledge   │
   │ Base        │
   └─────────────┘
         │
         ├──▶ CSV File 1
         ├──▶ CSV File 2
         ├──▶ Summary
         └──▶ Metadata
```

## Component Interactions

```
┌──────────────┐
│   main.py    │  ◀── Entry Point
└──────┬───────┘
       │
       ├──▶ ┌──────────────────┐
       │    │ UniProtRetriever │
       │    └──────────────────┘
       │
       ├──▶ ┌──────────────────┐
       │    │PubChemRetriever  │
       │    └──────────────────┘
       │
       ├──▶ ┌──────────────────┐
       │    │  DataCleaner     │
       │    └──────────────────┘
       │
       ├──▶ ┌──────────────────┐
       │    │ DataIntegrator   │
       │    └──────────────────┘
       │
       └──▶ ┌──────────────────┐
            │  CSVExporter     │
            └──────────────────┘
```

## Class Hierarchy

```
BaseRetriever (Abstract)
    │
    ├── UniProtRetriever
    │       │
    │       ├── get_schema()
    │       └── retrieve_data()
    │
    └── PubChemRetriever
            │
            ├── get_schema()
            ├── retrieve_data()
            ├── _search_compounds()
            └── _get_compound_properties()

DataCleaner (Utility)
    │
    ├── clean_text()
    ├── standardize_dataframe()
    └── validate_dataframe()

DataIntegrator
    │
    ├── add_source_data()
    ├── create_knowledge_base()
    ├── get_metadata()
    └── create_summary_statistics()

CSVExporter
    │
    ├── export_knowledge_base()
    ├── export_summary()
    └── export_metadata()
```

## Execution Flow

```
START
  │
  ▼
┌─────────────────────┐
│ Parse CLI Arguments │
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│ Initialize          │
│ Retrievers          │
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│ Retrieve Data       │
│ (Parallel)          │
│ • UniProt           │
│ • PubChem           │
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│ Clean Data          │
│ • Standardize       │
│ • Deduplicate       │
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│ Integrate Data      │
│ • Add metadata      │
│ • Create KB         │
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│ Generate Statistics │
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│ Export to CSV       │
│ • Data files        │
│ • Summary           │
│ • Metadata          │
└─────────────────────┘
  │
  ▼
END
```

## GitHub Actions Workflow

```
┌─────────────────────┐
│ Trigger             │
│ • Schedule (weekly) │
│ • Manual            │
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│ Setup Environment   │
│ • Checkout code     │
│ • Install Python    │
│ • Install deps      │
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│ Run AlzKB Updater   │
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│ Commit & Push       │
│ • Add CSV files     │
│ • Commit changes    │
│ • Push to repo      │
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│ Create Artifacts    │
│ • Upload CSV files  │
│ • Generate summary  │
└─────────────────────┘
  │
  ▼
END
```

## Error Handling Strategy

```
API Request
  │
  ├─ Success ──▶ Parse Response
  │                    │
  │                    ├─ Success ──▶ Return DataFrame
  │                    │
  │                    └─ Error ──▶ Log Error
  │                                  Return Empty DataFrame
  │
  └─ Error ──▶ Log Error
               Retry (if appropriate)
               Return Empty DataFrame
```

## Extension Points

To add a new data source:

```
1. Create New Retriever
   ┌─────────────────────┐
   │ NewRetriever        │
   │ extends             │
   │ BaseRetriever       │
   └─────────────────────┘

2. Implement Methods
   • get_schema()
   • retrieve_data()

3. Register
   • Add to __init__.py
   • Import in main.py

4. Integrate
   • Initialize in main()
   • Call retrieve_data()
   • Add to integrator

5. Document
   • Update README
   • Update architecture
```

## Performance Considerations

```
Rate Limiting
  │
  ├─ UniProt: 0.5s between requests (2 req/s)
  └─ PubChem: 0.2s between requests (5 req/s)

Data Volume
  │
  ├─ Default: 100 proteins + 50 compounds
  ├─ Configurable via CLI
  └─ Consider pagination for large datasets

Memory Usage
  │
  ├─ DataFrames held in memory
  ├─ Suitable for thousands of records
  └─ For millions: implement streaming

Network
  │
  ├─ Timeout: 30 seconds per request
  ├─ Retry: Not implemented (fail gracefully)
  └─ Parallel: Sequential retrieval (simplicity)
```
