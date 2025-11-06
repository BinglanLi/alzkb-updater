# AlzKB Updater - Architecture Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AlzKB Updater                           │
│                    (Alzheimer's Knowledge Base)                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                      │
├─────────────────────────────────────────────────────────────────┤
│  • main.py (CLI)                                                │
│  • demo.py (Demo script)                                        │
│  • GitHub Actions (Automation)                                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Integration Layer                          │
├─────────────────────────────────────────────────────────────────┤
│                    AlzKBIntegrator                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  • Coordinate data sources                                │ │
│  │  • Manage update workflow                                 │ │
│  │  • Combine data from multiple sources                     │ │
│  │  • Generate summary statistics                            │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│   Data Source Layer      │    │   Data Source Layer      │
├──────────────────────────┤    ├──────────────────────────┤
│   UniProtSource          │    │   DrugCentralSource      │
│  ┌────────────────────┐  │    │  ┌────────────────────┐  │
│  │ • fetch_data()     │  │    │  │ • fetch_data()     │  │
│  │ • clean_data()     │  │    │  │ • clean_data()     │  │
│  │ • save_raw_data()  │  │    │  │ • save_raw_data()  │  │
│  │ • save_processed() │  │    │  │ • save_processed() │  │
│  └────────────────────┘  │    │  └────────────────────┘  │
└──────────────────────────┘    └──────────────────────────┘
                │                               │
                ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│   External APIs          │    │   External APIs          │
├──────────────────────────┤    ├──────────────────────────┤
│   UniProt REST API       │    │   DrugCentral            │
│   rest.uniprot.org       │    │   unmtid-shinyapps.net   │
└──────────────────────────┘    └──────────────────────────┘
                │                               │
                └───────────────┬───────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Storage Layer                             │
├─────────────────────────────────────────────────────────────────┤
│  data/                                                          │
│  ├── raw/                                                       │
│  │   ├── uniprot_raw.csv                                       │
│  │   └── drugcentral_raw.csv                                   │
│  └── processed/                                                 │
│      ├── uniprot_processed.csv                                 │
│      ├── drugcentral_processed.csv                             │
│      ├── alzkb_integrated.csv                                  │
│      └── alzkb_summary.txt                                     │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. User Interface Layer

**main.py**
- Entry point for CLI usage
- Parses command-line arguments
- Initializes and runs integrator

**demo.py**
- Simplified demo script
- Tests with limited keywords
- Shows example usage

**GitHub Actions**
- Automated workflow
- Scheduled updates
- Automatic commits

### 2. Integration Layer

**AlzKBIntegrator** (`alzkb/integrator.py`)

```python
class AlzKBIntegrator:
    Methods:
    ├── __init__(output_dir, keywords)
    ├── _initialize_sources()
    ├── update_all_sources() → Dict[str, DataFrame]
    ├── integrate_data() → DataFrame
    └── generate_summary(df) → Dict
```

Responsibilities:
- Initialize all data sources
- Coordinate update workflow
- Combine data from multiple sources
- Generate summary statistics
- Save integrated results

### 3. Data Source Layer

**Base Class** (`alzkb/sources/base.py`)

```python
class DataSource(ABC):
    Abstract Methods:
    ├── fetch_data() → DataFrame
    └── clean_data(df) → DataFrame
    
    Concrete Methods:
    ├── save_raw_data(df)
    ├── save_processed_data(df)
    └── update() → DataFrame
```

**UniProtSource** (`alzkb/sources/uniprot.py`)
- Queries UniProt REST API
- Fetches protein information
- Filters by Alzheimer's keywords
- Extracts: genes, functions, diseases

**DrugCentralSource** (`alzkb/sources/drugcentral.py`)
- Accesses DrugCentral data
- Fetches drug information
- Filters for Alzheimer's drugs
- Extracts: indications, mechanisms

### 4. Configuration Layer

**config.py** (`alzkb/config.py`)

```python
Configuration:
├── BASE_DIR
├── DATA_DIR
├── RAW_DATA_DIR
├── PROCESSED_DATA_DIR
├── DATA_SOURCES
│   ├── uniprot
│   └── drugcentral
├── ALZHEIMER_KEYWORDS
└── OUTPUT_FORMAT
```

## Data Flow

### Update Workflow

```
1. User triggers update
   │
   ├─→ main.py or GitHub Actions
   │
   ▼
2. AlzKBIntegrator.integrate_data()
   │
   ├─→ For each enabled source:
   │   │
   │   ├─→ Source.fetch_data()
   │   │   │
   │   │   ├─→ Query external API
   │   │   ├─→ Parse response
   │   │   └─→ Return raw DataFrame
   │   │
   │   ├─→ Source.save_raw_data()
   │   │   └─→ Save to data/raw/
   │   │
   │   ├─→ Source.clean_data()
   │   │   │
   │   │   ├─→ Standardize columns
   │   │   ├─→ Filter relevant data
   │   │   ├─→ Add metadata
   │   │   └─→ Return cleaned DataFrame
   │   │
   │   └─→ Source.save_processed_data()
   │       └─→ Save to data/processed/
   │
   ▼
3. Combine all sources
   │
   ├─→ Concatenate DataFrames
   ├─→ Add integration metadata
   └─→ Save alzkb_integrated.csv
   │
   ▼
4. Generate summary
   │
   ├─→ Count records by source
   ├─→ Count records by type
   └─→ Save alzkb_summary.txt
```

### Data Transformation Pipeline

```
Raw Data → Cleaning → Standardization → Integration → Export

UniProt API Response
├─→ TSV format
├─→ Parse columns
├─→ Rename to standard format
├─→ Filter by keywords
├─→ Add source metadata
└─→ CSV export

DrugCentral Data
├─→ Structured format
├─→ Parse records
├─→ Rename to standard format
├─→ Filter for Alzheimer's
├─→ Add source metadata
└─→ CSV export

Combined Data
├─→ Merge all sources
├─→ Add integration timestamp
├─→ Generate summary
└─→ Export integrated CSV
```

## Design Patterns

### 1. Abstract Factory Pattern

```python
DataSource (Abstract Base Class)
    ├── UniProtSource
    └── DrugCentralSource
```

**Benefits:**

- Easy to add new sources
- Consistent interface
- Polymorphic behavior

### 2. Template Method Pattern

```python
class DataSource:
    def update(self):  # Template method
        raw_df = self.fetch_data()      # Abstract
        self.save_raw_data(raw_df)      # Concrete
        processed_df = self.clean_data(raw_df)  # Abstract
        self.save_processed_data(processed_df)  # Concrete
        return processed_df
```

**Benefits:**

- Consistent workflow
- Reusable logic
- Clear extension points

### 3. Strategy Pattern

```python
# Different strategies for data fetching
class UniProtSource:
    def fetch_data(self):
        # REST API strategy
        pass
        
class DrugCentralSource:
    def fetch_data(self):
        # File download strategy
        pass
```

**Benefits:**

- Flexible data retrieval
- Source-specific logic
- Easy to modify

## Extension Points

### Adding a New Data Source

**1. Create source class:**

```python
class NewSource(DataSource):
    def fetch_data(self):
        # Implement fetching logic
        pass
        
    def clean_data(self, df):
        # Implement cleaning logic
        pass
```

**2. Register in integrator:**

```python
# In AlzKBIntegrator._initialize_sources()
if DATA_SOURCES["newsource"]["enabled"]:
    self.sources.append(NewSource(...))
```

**3. Add configuration:**

```python
# In config.py
DATA_SOURCES["newsource"] = {
    "name": "New Source",
    "url": "https://api.example.com",
    "enabled": True
}
```

### Customizing Data Processing

Override methods in source classes:

- `fetch_data()` - Custom retrieval logic
- `clean_data()` - Custom cleaning logic
- Add new methods as needed

### Extending Output Formats

Modify `DataSource` base class:

```python
def save_json(self, df):
    # Add JSON export
    pass
    
def save_parquet(self, df):
    # Add Parquet export
    pass
```

## Error Handling

### Strategy

```python
try:
    # Fetch data
except RequestException:
    # Log error
    # Continue with other sources
    
try:
    # Clean data
except Exception:
    # Log error
    # Return empty DataFrame
```

### Logging

```python
logger.info("Starting update...")
logger.warning("No data fetched")
logger.error("API request failed: {error}")
```

## Performance Considerations

### API Rate Limiting

- Built-in delays between requests
- Configurable timeout values
- Retry logic for transient failures

### Memory Management

- Process sources sequentially
- Clean up DataFrames after saving
- Use chunking for large datasets

### Scalability

- Parallel source updates (future)
- Database backend (future)
- Caching layer (future)

## Security Considerations

### API Keys

- Store in environment variables
- Never commit to repository
- Use GitHub Secrets for Actions

### Data Validation

- Validate API responses
- Check data types
- Handle missing values

### Access Control

- Read-only API access
- No sensitive data storage
- Public data only

## Testing Strategy

### Manual Testing

- Run demo.py
- Check output files
- Verify data quality

### Future Automated Testing

- Unit tests for each source
- Integration tests
- Data validation tests

## Deployment

### Local Deployment
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### GitHub Actions Deployment

- Push to GitHub
- Enable Actions
- Workflow runs automatically

### Future: Docker Deployment

```dockerfile
FROM python:3.10
COPY . /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

## Monitoring

### Logs

- Console output
- File logging (future)
- Error tracking

### Metrics

- Record counts
- Update timestamps
- Success/failure rates

### Alerts

- GitHub Actions notifications
- Email alerts (future)
- Slack integration (future)

## Maintenance

### Regular Tasks

- Monitor API changes
- Update dependencies
- Review data quality
- Add new sources

### Version Control

- Semantic versioning
- Change log
- Migration guides

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Maintainer**: AlzKB Team
