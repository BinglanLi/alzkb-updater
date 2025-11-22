# Contributing to alzkb-updater

## Adding New Data Sources

### Step 1: Create a New Retriever

Create a new file in `src/retrievers/` (e.g., `drugbank_retriever.py`):

```python
from .base_retriever import BaseRetriever
import pandas as pd

class DrugBankRetriever(BaseRetriever):
    """Retrieve drug data from DrugBank."""
    
    def __init__(self):
        super().__init__(
            name="DrugBank",
            base_url="https://api.drugbank.com",
            rate_limit=1.0  # seconds between requests
        )
    
    def get_schema(self):
        """Define your output columns."""
        return [
            "drugbank_id",
            "drug_name",
            "description",
            "indication"
        ]
    
    def retrieve_data(self, query="alzheimer", limit=100):
        """Implement data retrieval logic."""
        # Your API calls here
        # Return a DataFrame with the schema columns
        pass
```

### Step 2: Register the Retriever

Update `src/retrievers/__init__.py`:

```python
from .drugbank_retriever import DrugBankRetriever

__all__ = [
    'BaseRetriever',
    'UniProtRetriever',
    'PubChemRetriever',
    'DrugBankRetriever'  # Add your retriever
]
```

### Step 3: Integrate in Main Application

Update `src/main.py`:

```python
from retrievers import DrugBankRetriever

# In main():
drugbank = DrugBankRetriever()
drug_data = drugbank.retrieve_data(query=args.query, limit=args.drug_limit)
drug_data_clean = cleaner.standardize_dataframe(drug_data)
integrator.add_source_data("DrugBank", drug_data_clean)
```

### Step 4: Add Command-Line Arguments

In `src/main.py`, add new arguments:

```python
parser.add_argument(
    '--drug-limit',
    type=int,
    default=50,
    help='Maximum number of drugs to retrieve (default: 50)'
)
```

## Code Style Guidelines

1. **Follow PEP 8**: Use standard Python style
2. **Type Hints**: Add type hints to function signatures
3. **Docstrings**: Document all classes and methods
4. **Logging**: Use the logger, don't use print()
5. **Error Handling**: Catch exceptions, log them, return empty DataFrames

## Testing Your Changes

### Local Testing

```bash
# Test with small limits first
cd src
python main.py --protein-limit 5 --compound-limit 5

# Check output
ls -lh ../data/processed/
```

### Verify CSV Output

```python
import pandas as pd

# Check your data
df = pd.read_csv('data/processed/alzkb_newsource_20240101.csv')
print(df.head())
print(df.info())
```

## Best Practices

### API Rate Limiting

Always respect API rate limits:

```python
# In your retriever __init__:
super().__init__(
    name="YourAPI",
    base_url="https://api.example.com",
    rate_limit=1.0  # Adjust based on API docs
)
```

### Error Handling

```python
def retrieve_data(self, **kwargs):
    response = self._make_request(url, params)
    
    if response is None:
        self.logger.warning("Failed to retrieve data")
        return pd.DataFrame(columns=self.get_schema())
    
    try:
        # Parse response
        pass
    except Exception as e:
        self.logger.error(f"Error parsing response: {str(e)}")
        return pd.DataFrame(columns=self.get_schema())
```

### Data Cleaning

Use the DataCleaner for consistent cleaning:

```python
from integrators import DataCleaner

cleaner = DataCleaner()
clean_data = cleaner.standardize_dataframe(raw_data)
```

## Updating Documentation

When adding features:

1. Update `README.md` with new data source info
2. Update `PROJECT_SUMMARY.md` architecture section
3. Add examples to `QUICKSTART.md` if needed
4. Update GitHub Actions workflow if necessary

## GitHub Actions

If your data source needs authentication:

1. Add secrets in GitHub repository settings
2. Update `.github/workflows/update-alzkb.yml`:

```yaml
- name: Run AlzKB updater
  env:
    API_KEY: ${{ secrets.YOUR_API_KEY }}
  run: |
    cd src
    python main.py
```

3. Access in your code:

```python
import os
api_key = os.getenv('API_KEY')
```

## Common Issues

### Issue: Rate Limiting

**Solution**: Increase `rate_limit` in retriever initialization

### Issue: Large Datasets

**Solution**: Implement pagination in your retriever

```python
def retrieve_data(self, limit=100):
    all_data = []
    page_size = 100
    
    for offset in range(0, limit, page_size):
        page_data = self._fetch_page(offset, page_size)
        all_data.append(page_data)
    
    return pd.concat(all_data, ignore_index=True)
```

### Issue: API Authentication

**Solution**: Add authentication to your retriever

```python
def __init__(self, api_key=None):
    super().__init__(...)
    self.api_key = api_key or os.getenv('API_KEY')

def _make_request(self, url, params=None):
    headers = {'Authorization': f'Bearer {self.api_key}'}
    return super()._make_request(url, params, headers)
```

## Questions?

- Check existing retrievers for examples
- Review the base_retriever.py documentation
- Look at the reference repositories mentioned in README.md
