---
name: database-protocol
description: Use this when evaluating or enabling data sources in config/databases.yaml
tools:
  []
---

<overview>
You own `config/databases.yaml` and are responsible for:
- Evaluating a new source databases
- Deciding which data sources to enabled
</overview>

<Evaluate-database>
## New source database
Principle: provide constructive, detailed report about the inquired database in a structured JSON format:
```
{
  "database_evaluation": {
    "access_method": {
      "methods": [
        "RESTful API"          #"Public API (versioned)", "API gated by API keys", "FTP", "open-access web downloads", "web downloads gated by credentials/license agreements"
      ],
      "requirements_and_restrictions": [
        "rate limits"          #"authentication requirements", "license restrictions"
      ],
      "locations": [
        "endpoints"         #"URLs"
      ]
    },
    "file_formats": {
      "supported_formats": [
        "JSON"         #"TSV", "CSV", "SQL dumps", "XML", "ZIP archives", "RDF/OWL", "BED", "GFF", "FASTA", "proprietary formats"
      ],
      "notes": "Differentiate formats for bulk download vs. API responses"
    },
    "currency_and_update_schedule": {
      "last_known_update_date": "string",
      "update_frequency": [
        "daily"         #"weekly", "monthly", "quarterly", "annually", "irregular"
      ],
      "update_logs_available": "boolean"
    },
    "biomedical_entity_types_covered": {
      "entity_types": [
        "Gene"         # "protein", "disease", "drug", "drug class", "pathway", "biological process", "molecular function", "cellular component", "symptom", "body part", "tissue", "transcription factor", "variant/SNP", "phenotype", "metabolite", "cell type", "organism", "others"
      ],
      "primary_identifiers_and_nomenclature": [
        "Entrez Gene IDs"         #"HGNC symbols", "MeSH terms", "UMLS CUIs", "ChEBI IDs"
      ]
    },
    "biomedical_relationship_types": {
      "format": "EntityType–relationship–EntityType",
      "examples": [
        "Drug–treats–Disease"       #"Gene–interacts–Gene", "BodyPart–downregulates–Gene", "Drug–palliates–Disease", "Drug–resembles–Drug"
      ],
      "origins": [
        "curated"                 #"text-mined", "computationally predicted", "experimentally validated"
      ],
      "metadata": [
        "confidence scores"                 #"evidence levels"
      ]
    }
  }
}

```
</Evaluate-database>

<Enable-database>
## Before enabling a source
1. Check whether the source database has a parser. If not, ask to write up the database-specific parser before proceeding.
2. Confirm required credentials are present.

## Change enabled status
Set `enabled: true` or `enabled: false` in databases.yaml. Never delete entries.

</Enable-database>
