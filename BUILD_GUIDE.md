# AlzKB v2.1 Build Guide

This guide provides step-by-step instructions for building AlzKB from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Data Source Configuration](#data-source-configuration)
4. [Building AlzKB](#building-alzkb)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows with WSL
- **Python**: 3.8 or higher
- **Memory**: At least 8GB RAM (16GB recommended)
- **Disk Space**: At least 50GB free space
- **MySQL**: Version 5.7 or higher (for AOP-DB)

### Required Software

```bash
# Python 3.8+
python3 --version

# Git
git --version

# MySQL (for AOP-DB)
mysql --version

# pip
pip --version
```

## Environment Setup

### 1. Clone the Repository

```bash
cd ~/GitHub
git clone https://github.com/BinglanLi/alzkb-updater.git
cd alzkb-updater
```

### 2. Checkout the Correct Branch

```bash
git checkout alzkb-v2.1
```

### 3. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate  # On Windows
```

### 4. Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### 5. Install ista

```bash
# Clone ista repository
git clone https://github.com/RomanoLab/ista.git .ista

# Install ista
pip install -e .ista
```

### 6. Verify Installation

```bash
# Check if csv2rdf is available
which csv2rdf

# Test csv2rdf
csv2rdf --help
```

## Data Source Configuration

### 1. Create Environment File

Create a `.env` file in the project root:

```bash
# DisGeNET API
DISGENET_API_KEY=your_api_key_here

# DrugBank credentials
DRUGBANK_USERNAME=your_username
DRUGBANK_PASSWORD=your_password

# MySQL (for AOP-DB)
MYSQL_USERNAME=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB_NAME=aopdb
```

### 2. Obtain API Keys and Credentials

#### DisGeNET API Key

1. Go to https://www.disgenet.org/
2. Create an account
3. Navigate to your profile
4. Copy your API key
5. Add to `.env` file

#### DrugBank Credentials

1. Go to https://go.drugbank.com/
2. Create an account
3. Verify your email
4. Use your email and password in `.env`

### 3. Set Up AOP-DB (MySQL)

#### Download AOP-DB

```bash
# Create directory
mkdir -p data/raw/aopdb

# Download AOP-DB SQL dump
# Note: You may need to request access from AOP-DB maintainers
# or use a local copy if available
```

#### Import to MySQL

```bash
# Create database
mysql -u root -p -e "CREATE DATABASE aopdb;"

# Import SQL dump
mysql -u root -p aopdb < path/to/aopdb_dump.sql

# Verify import
mysql -u root -p -e "USE aopdb; SHOW TABLES;"
```

### 4. Verify Credentials

```bash
# Test DisGeNET API
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "https://www.disgenet.org/api/gda/disease/C0002395"

# Test MySQL connection
mysql -u root -p -e "USE aopdb; SELECT COUNT(*) FROM pathways;"
```

## Building AlzKB

### Option 1: Complete Pipeline (Recommended)

Run the complete pipeline with ista integration:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run pipeline
python src/main.py --use-ista
```

This will:
1. Download data from all sources
2. Parse and transform data
3. Export to TSV format
4. Populate ontology using ista
5. Create database files
6. Generate release notes

### Option 2: Step-by-Step Build

#### Step 1: Download and Parse Data

```python
from src.parsers import (
    AOPDBParser, DisGeNETParser, DrugBankParser,
    NCBIGeneParser, HetionetBuilder
)
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize parsers
parsers = {
    'aopdb': AOPDBParser(
        data_dir='data/raw/aopdb',
        mysql_config={
            'host': 'localhost',
            'user': os.getenv('MYSQL_USERNAME'),
            'password': os.getenv('MYSQL_PASSWORD'),
            'database': 'aopdb'
        }
    ),
    'disgenet': DisGeNETParser(
        data_dir='data/raw/disgenet',
        api_key=os.getenv('DISGENET_API_KEY')
    ),
    'drugbank': DrugBankParser(
        data_dir='data/raw/drugbank',
        username=os.getenv('DRUGBANK_USERNAME'),
        password=os.getenv('DRUGBANK_PASSWORD')
    ),
    'ncbigene': NCBIGeneParser(
        data_dir='data/raw/ncbigene'
    ),
    'hetionet': HetionetBuilder(
        data_dir='data/raw/hetionet'
    )
}

# Download and parse each source
for name, parser in parsers.items():
    print(f"Processing {name}...")
    parser.download_data()
    data = parser.parse_data()
    print(f"Completed {name}")
```

#### Step 2: Export to TSV

```python
# Export parsed data to TSV files
for name, parser in parsers.items():
    output_dir = f'data/processed/{name}'
    parser.export_to_tsv(data, output_dir)
```

#### Step 3: Populate Ontology with ista

```python
from src.ontology.ista_integrator import IstaIntegrator, get_default_configs

# Initialize ista
ista = IstaIntegrator(
    ontology_path='data/ontology/alzkb_v2.rdf',
    output_dir='data/output/rdf',
    venv_path='.venv'
)

# Get configurations
configs = get_default_configs()

# Populate for each source
rdf_files = []
for source_name, config in configs.items():
    tsv_file = f'data/processed/{source_name}/main_data.tsv'
    rdf_file = ista.populate_from_tsv(source_name, tsv_file, config)
    rdf_files.append(rdf_file)

# Merge RDF files
merged_rdf = ista.merge_rdf_files(rdf_files, 'data/output/alzkb_v2.1.rdf')
```

#### Step 4: Create Database Files

```python
from rdflib import Graph
import pandas as pd

# Load RDF
g = Graph()
g.parse('data/output/alzkb_v2.1.rdf', format='xml')

# Extract nodes and edges
nodes = set()
edges = []

for s, p, o in g:
    nodes.add(str(s))
    if str(o).startswith('http'):
        nodes.add(str(o))
        edges.append({
            'source': str(s),
            'relationship': str(p),
            'target': str(o)
        })

# Export to CSV
pd.DataFrame({'node_id': list(nodes)}).to_csv('data/output/nodes.csv', index=False)
pd.DataFrame(edges).to_csv('data/output/edges.csv', index=False)
```

### Monitoring Progress

The pipeline creates detailed logs:

```bash
# View real-time logs
tail -f alzkb_build.log

# View completed logs
less alzkb_build.log
```

## Verification

### 1. Check Output Files

```bash
# List output files
ls -lh data/output/

# Expected files:
# - alzkb_v2.1_populated.rdf
# - alzkb_nodes.csv
# - alzkb_edges.csv
# - RELEASE_NOTES_v2.1.md
```

### 2. Verify Data Integrity

```python
import pandas as pd

# Check nodes
nodes = pd.read_csv('data/output/alzkb_nodes.csv')
print(f"Total nodes: {len(nodes)}")

# Check edges
edges = pd.read_csv('data/output/alzkb_edges.csv')
print(f"Total edges: {len(edges)}")

# Check for duplicates
print(f"Duplicate nodes: {nodes.duplicated().sum()}")
print(f"Duplicate edges: {edges.duplicated().sum()}")
```

### 3. Verify RDF

```python
from rdflib import Graph

g = Graph()
g.parse('data/output/alzkb_v2.1_populated.rdf', format='xml')
print(f"Total triples: {len(g)}")
```

### 4. Run Test Queries

```python
# Example: Find all genes
genes = nodes[nodes['node_id'].str.contains('gene', case=False)]
print(f"Number of genes: {len(genes)}")

# Example: Find all drug-gene interactions
drug_gene = edges[
    (edges['source'].str.contains('drug', case=False)) &
    (edges['target'].str.contains('gene', case=False))
]
print(f"Drug-gene interactions: {len(drug_gene)}")
```

## Troubleshooting

### Common Issues

#### 1. ista Not Found

**Problem**: `csv2rdf: command not found`

**Solution**:
```bash
# Reinstall ista
pip install -e .ista

# Verify installation
which csv2rdf
```

#### 2. MySQL Connection Failed

**Problem**: `Access denied for user 'root'@'localhost'`

**Solution**:
```bash
# Check MySQL is running
sudo systemctl status mysql

# Test connection
mysql -u root -p

# Update .env with correct credentials
```

#### 3. API Authentication Failed

**Problem**: `401 Unauthorized` from DisGeNET API

**Solution**:
- Verify API key in `.env`
- Check if API key is active
- Try generating a new API key

#### 4. Memory Error

**Problem**: `MemoryError` during processing

**Solution**:
```python
# Process data in chunks
chunk_size = 10000
for chunk in pd.read_csv('large_file.tsv', chunksize=chunk_size):
    process_chunk(chunk)
```

#### 5. Download Timeouts

**Problem**: Downloads timing out

**Solution**:
```python
# Increase timeout in parser
response = requests.get(url, timeout=600)  # 10 minutes

# Or download manually and place in data/raw/
```

### Getting Help

If you encounter issues:

1. Check the logs: `alzkb_build.log`
2. Search existing issues on GitHub
3. Open a new issue with:
   - Error message
   - Log file excerpt
   - System information
   - Steps to reproduce

## Performance Optimization

### For Large Datasets

```python
# Use multiprocessing
from multiprocessing import Pool

def process_source(source_name):
    parser = get_parser(source_name)
    return parser.download_and_parse()

with Pool(processes=4) as pool:
    results = pool.map(process_source, source_names)
```

### For Limited Memory

```python
# Process in batches
batch_size = 1000
for i in range(0, len(data), batch_size):
    batch = data[i:i+batch_size]
    process_batch(batch)
```

## Next Steps

After building AlzKB:

1. **Import to Graph Database**:
   ```bash
   # For Memgraph
   COPY nodes FROM 'data/output/alzkb_nodes.csv' WITH (HEADER = TRUE);
   COPY edges FROM 'data/output/alzkb_edges.csv' WITH (HEADER = TRUE);
   ```

2. **Run Queries**:
   ```cypher
   // Example Cypher query
   MATCH (d:Disease)-[r]-(g:Gene)
   WHERE d.name CONTAINS 'Alzheimer'
   RETURN d, r, g LIMIT 10;
   ```

3. **Deploy API**:
   - Set up GraphQL or REST API
   - Configure authentication
   - Deploy to server

## References

- [AlzKB Original](https://github.com/EpistasisLab/AlzKB)
- [ista Documentation](https://github.com/RomanoLab/ista)
- [Hetionet](https://het.io/)
- [Memgraph Documentation](https://memgraph.com/docs)

---

**Last Updated**: 2024-01-20
**Version**: 2.1
