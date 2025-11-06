# Contributing to AlzKB Updater

Thank you for your interest in contributing to AlzKB Updater! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Issues

When reporting issues:

- Use the GitHub issue tracker
- Describe the issue clearly
- Include steps to reproduce
- Mention your Python version and OS

### Adding New Data Sources

**1. Create a new source file** in `alzkb/sources/`:

```python
from alzkb.sources.base import DataSource

class MyNewSource(DataSource):
    def fetch_data(self):
        # Implement data fetching
        pass
    
    def clean_data(self, df):
        # Implement data cleaning
        pass
```

**2. Register the source** in `alzkb/integrator.py`:

```python
from alzkb.sources.mynewsource import MyNewSource

# In _initialize_sources method:
if DATA_SOURCES["mynewsource"]["enabled"]:
    self.sources.append(MyNewSource(self.output_dir, self.keywords))
```

**3. Add configuration** in `alzkb/config.py`:

```python
DATA_SOURCES = {
    "mynewsource": {
        "name": "My New Source",
        "url": "https://api.example.com",
        "enabled": True
    }
}
```

### Code Style

Please adhere to these standards:

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to classes and methods
- Keep functions focused and simple

### Testing

While we don't have automated tests yet, please:

- Test your changes locally
- Run with sample data
- Verify CSV outputs are correct

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Commit with clear messages: `git commit -m 'Add amazing feature'`
5. Push to your fork: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Pull Request Checklist

Before submitting, ensure:

- [ ] Code follows the project style
- [ ] Changes are documented
- [ ] README updated if needed
- [ ] New data source is documented
- [ ] Tested locally

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/AlzKB-updater-mcp.git
cd AlzKB-updater-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .
pip install -r requirements.txt
```

## Project Structure

```
alzkb/
├── __init__.py           # Package initialization
├── config.py            # Configuration settings
├── integrator.py        # Main integration logic
└── sources/             # Data source implementations
    ├── base.py         # Base class (inherit from this)
    ├── uniprot.py      # Example: UniProt source
    └── drugcentral.py  # Example: DrugCentral source
```

## Adding Documentation

When adding features, please:

- Update README.md for major features and user-facing changes
- Add inline comments for complex logic
- Update ARCHITECTURE.md for structural changes
- Ensure code examples are clear and tested

## Questions?

Feel free to open an issue for questions or discussion!

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
