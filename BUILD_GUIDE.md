# AlzKB v2 Build Guide

This guide provides detailed instructions for building AlzKB v2 from scratch, based on the original BUILD.org specifications.

## Overview

Building AlzKB v2 involves three main phases:

1. **Data Collection**: Download and prepare data from multiple sources
2. **Data Processing**: Parse and integrate data into the ontology
3. **Export**: Generate output files in various formats

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.8 or higher
- **Disk Space**: 15+ GB free space
  - Raw data: ~10 GB
  - Processed data: ~2 GB
  - MySQL database (AOP-DB): ~3 GB
- **Memory**: 8+ GB RAM recommended
- **MySQL Server**: Optional, required only for AOP-DB

### Software Installation

1. **Python and pip**:
```bash
# Check Python version
python --version  # Should be 3.8+

# Upgrade pip
pip install --upgrade pip
```

2. **MySQL Server** (optional, for AOP-DB):
```bash
# Ubuntu/Debian
sudo apt-get install mysql-server

# macOS with Homebrew
brew install mysql

# Windows
# Download from: https://dev.mysql.com/downloads/mysql/
```

3. **Git**:
```bash
# Check if git is installed
git --version
```

## Step-by-Step Build Process

### Phase 1: Setup

#### 1.1 Clone Repository

```bash
git clone <repository-url>
cd alzkb-updater
git checkout alzkb-v2
```

#### 1.2 Install Python Dependencies

```bash
pip install -r requirements.txt
```

Verify installation:
```bash
python -c "import owlready2; print('owlready2 OK')"
python -c "import pandas; print('pandas OK')"
```

#### 1.3 Create Data Directories

```bash
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/ontology
```

### Phase 2: Data Collection

#### 2.1 Automated Downloads

These sources can be downloaded automatically:

**Hetionet:**
```bash
cd src
python -c "
from parsers import HetionetParser
parser = HetionetParser()
parser.download_data()
"
```

**NCBI Gene:**
```bash
python -c "
from parsers import NCBIGeneParser
parser = NCBIGeneParser()
parser.download_data()
"
```

#### 2.2 Manual Downloads

##### DrugBank

1. **Create Account**:
   - Visit: https://go.drugbank.com/
   - Sign up for free academic account
   - Verify email address
   - Wait for approval (may take several days)

2. **Download Data**:
   - Log in to DrugBank
   - Navigate to: Downloads → Academic Download
   - Click "External Links" tab
   - In "External Drug Links" table, click "Download" for "All"
   - Save as: `data/raw/drugbank/drug_links.csv`

3. **Verify**:
```bash
ls -lh data/raw/drugbank/drug_links.csv
```

##### DisGeNET

1. **Create Account**:
   - Visit: https://www.disgenet.org/
   - Create free account
   - Log in

2. **Download Files**:
   - Navigate to Downloads page
   - Download these files:
     - `curated_gene_disease_associations.tsv.gz`
     - `disease_mappings.tsv.gz`

3. **Extract and Place**:
```bash
cd data/raw/disgenet
gunzip curated_gene_disease_associations.tsv.gz
gunzip disease_mappings.tsv.gz
cd ../../..
```

4. **Verify**:
```bash
ls -lh data/raw/disgenet/*.tsv
```

##### AOP-DB (Optional)

**Warning**: This is a large download (7.2 GB compressed)!

1. **Download**:
```bash
cd /tmp
wget https://gaftp.epa.gov/EPADataCommons/ORD/AOP-DB/AOP-DB_v2.zip
```

2. **Extract**:
```bash
unzip AOP-DB_v2.zip
tar -xzf aopdb_no-orthoscores.tar.gz
```

3. **Import to MySQL**:
```bash
# Create database
mysql -u root -p -e "CREATE DATABASE aopdb;"

# Import data (this takes a while!)
mysql -u root -p aopdb < aopdb_no-orthoscores.sql
```

4. **Verify**:
```bash
mysql -u root -p aopdb -e "SHOW TABLES;"
```

### Phase 3: Build AlzKB

#### 3.1 Basic Build (No AOP-DB)

Build with automatically downloadable sources:

```bash
cd src
python main.py --sources hetionet ncbigene
```

#### 3.2 Full Build (With Manual Sources)

After completing manual downloads:

```bash
python main.py --sources hetionet ncbigene drugbank disgenet
```

#### 3.3 Complete Build (With AOP-DB)

If you have MySQL and AOP-DB set up:

```bash
python main.py \
  --sources hetionet ncbigene drugbank disgenet aopdb \
  --mysql-host localhost \
  --mysql-user root \
  --mysql-password yourpassword \
  --mysql-db aopdb
```

### Phase 4: Verify Output

#### 4.1 Check Output Files

```bash
ls -lh data/processed/
```

Expected files:
- `alzkb_hetionet_nodes_YYYYMMDD.csv`
- `alzkb_hetionet_edges_YYYYMMDD.csv`
- `alzkb_ncbigene_genes_YYYYMMDD.csv`
- `alzkb_drugbank_drugs_YYYYMMDD.csv` (if manual download completed)
- `alzkb_disgenet_associations_YYYYMMDD.csv` (if manual download completed)
- `alzkb_summary_YYYYMMDD.csv`

#### 4.2 Inspect Data

```bash
# View summary
cat data/processed/alzkb_summary_*.csv

# Count records
wc -l data/processed/alzkb_*.csv
```

#### 4.3 Validate CSV Files

```python
import pandas as pd

# Check Hetionet nodes
df = pd.read_csv('data/processed/alzkb_hetionet_nodes_YYYYMMDD.csv')
print(f"Hetionet nodes: {len(df)}")
print(df.head())

# Check gene data
df = pd.read_csv('data/processed/alzkb_ncbigene_genes_YYYYMMDD.csv')
print(f"Genes: {len(df)}")
print(df.head())
```

## Build Options

### Incremental Builds

If you've already downloaded data:

```bash
# Skip download, only parse and export
python main.py --no-download
```

### Specific Sources Only

```bash
# Build only Hetionet
python main.py --sources hetionet

# Build only gene data
python main.py --sources ncbigene

# Build multiple specific sources
python main.py --sources hetionet ncbigene drugbank
```

### Custom Data Directory

```bash
python main.py --data-dir /path/to/custom/data
```

## Troubleshooting

### Common Issues

#### 1. Download Failures

**Problem**: Network errors or timeouts during download

**Solutions**:
- Check internet connection
- Retry the download
- Use `--no-download` and download manually
- Check if source website is accessible

#### 2. Missing Dependencies

**Problem**: `ModuleNotFoundError: No module named 'owlready2'`

**Solution**:
```bash
pip install owlready2
```

#### 3. MySQL Connection Errors

**Problem**: `Can't connect to MySQL server`

**Solutions**:
- Verify MySQL is running: `sudo systemctl status mysql`
- Check credentials are correct
- Ensure database exists: `mysql -u root -p -e "SHOW DATABASES;"`
- Verify user has permissions

#### 4. Out of Memory

**Problem**: Process killed due to memory

**Solutions**:
- Close other applications
- Process sources separately:
  ```bash
  python main.py --sources hetionet
  python main.py --sources ncbigene --no-download
  ```
- Use a machine with more RAM

#### 5. Disk Space Issues

**Problem**: No space left on device

**Solutions**:
- Check available space: `df -h`
- Clean up old data: `rm -rf data/raw/*/`
- Use external drive: `python main.py --data-dir /mnt/external/alzkb`

### Data Fetching Errors

Some data sources may be temporarily unavailable. This is expected and acceptable:

- **Hetionet**: GitHub may rate-limit; retry later
- **NCBI Gene**: FTP server may be down for maintenance
- **DrugBank**: Requires valid account and approval
- **DisGeNET**: Requires account login
- **AOP-DB**: Large file, may timeout; use download manager

**Do not fabricate data to bypass errors!** Report issues honestly.

### Getting Help

1. Check logs in console output
2. Review error messages carefully
3. Consult documentation:
   - README_v2.md
   - Original BUILD.org
4. Open GitHub issue with:
   - Error message
   - Steps to reproduce
   - System information

## Performance Tips

### Faster Downloads

```bash
# Use parallel downloads for Hetionet
# (already implemented in parsers)
```

### Reduce Memory Usage

```bash
# Process one source at a time
for source in hetionet ncbigene drugbank disgenet; do
  python main.py --sources $source --no-download
done
```

### Speed Up MySQL Import

```bash
# Increase MySQL buffer size
mysql -u root -p -e "SET GLOBAL innodb_buffer_pool_size=2G;"
```

## Advanced Configuration

### Custom Parsers

To add a new data source:

1. Create parser in `src/parsers/`:
```python
from .base_parser import BaseParser

class MyParser(BaseParser):
    def download_data(self):
        # Implementation
        pass
    
    def parse_data(self):
        # Implementation
        pass
    
    def get_schema(self):
        # Implementation
        pass
```

2. Register in `__init__.py`
3. Add to main.py

### Environment Variables

Set environment variables for sensitive data:

```bash
export MYSQL_PASSWORD="yourpassword"
python main.py --mysql-password "$MYSQL_PASSWORD"
```

## Next Steps

After building AlzKB:

1. **Analyze Data**: Use Jupyter notebooks in `examples/`
2. **Export to Graph DB**: Convert to Neo4j (future feature)
3. **Query Knowledge Graph**: Use SPARQL or Cypher
4. **Extend**: Add new data sources or relationships

## References

- Original BUILD.org: https://github.com/EpistasisLab/AlzKB/blob/master/BUILD.org
- Hetionet: https://het.io/
- NCBI Gene: https://www.ncbi.nlm.nih.gov/gene/
- DrugBank: https://go.drugbank.com/
- DisGeNET: https://www.disgenet.org/
- AOP-DB: https://aopdb.epa.gov/
