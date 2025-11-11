# Quick Start Guide

## For Linux/Mac Users

1. Make sure Python 3.8+ is installed:
```bash
python3 --version
```

2. Run the updater:
```bash
./run.sh
```

That's it! The script will:
- Create a virtual environment
- Install dependencies
- Run the AlzKB updater
- Save CSV files to `data/processed/`

## For Windows Users

1. Make sure Python 3.8+ is installed:
```cmd
python --version
```

2. Run the updater:
```cmd
run.bat
```

## Custom Options

Run with custom parameters:

**Linux/Mac:**
```bash
./run.sh --query "alzheimer disease" --protein-limit 200
```

**Windows:**
```cmd
run.bat --query "alzheimer disease" --protein-limit 200
```

## Output

Check the `data/processed/` folder for:
- `alzkb_uniprot_*.csv` - Protein data
- `alzkb_pubchem_*.csv` - Compound data
- `alzkb_summary_*.csv` - Statistics
- `alzkb_metadata_*.csv` - Integration info

## Troubleshooting

**Issue: Permission denied on run.sh**
```bash
chmod +x run.sh
```

**Issue: Python not found**
- Install Python 3.8 or higher from python.org

**Issue: Network errors**
- Check internet connection
- APIs may be temporarily unavailable (this is normal)
- The system will log errors and continue with available data

## GitHub Actions

To enable automatic updates:

1. Fork this repository
2. Go to Settings → Actions → General
3. Enable "Read and write permissions" for workflows
4. The updater will run every Monday at midnight UTC
5. You can also trigger it manually from the Actions tab
