"""
Test script for AlzKB v2 implementation.

This script performs basic validation of the AlzKB v2 components
without requiring actual data downloads.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 80)
print("AlzKB v2 Implementation Test")
print("=" * 80)

# Test 1: Import ontology modules
print("\n1. Testing ontology module imports...")
try:
    from ontology import OntologyManager, OntologyPopulator
    print("   ✓ Ontology modules imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import ontology modules: {e}")
    sys.exit(1)

# Test 2: Import parser modules
print("\n2. Testing parser module imports...")
try:
    from parsers import (
        BaseParser, HetionetParser, NCBIGeneParser,
        DrugBankParser, DisGeNETParser, AOPDBParser
    )
    print("   ✓ Parser modules imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import parser modules: {e}")
    sys.exit(1)

# Test 3: Check ontology file exists
print("\n3. Testing ontology file...")
ontology_path = "data/ontology/alzkb_v2.rdf"
if os.path.exists(ontology_path):
    size = os.path.getsize(ontology_path)
    print(f"   ✓ Ontology file exists: {ontology_path} ({size:,} bytes)")
else:
    print(f"   ✗ Ontology file not found: {ontology_path}")

# Test 4: Initialize OntologyManager
print("\n4. Testing OntologyManager...")
try:
    manager = OntologyManager(ontology_path)
    print("   ✓ OntologyManager initialized")
    
    # Try to load ontology (requires owlready2)
    try:
        if manager.load_ontology():
            print("   ✓ Ontology loaded successfully")
            manager.print_statistics()
        else:
            print("   ⚠ Ontology loading failed (may need owlready2)")
    except Exception as e:
        print(f"   ⚠ Could not load ontology: {e}")
        print("   Note: Install owlready2 with: pip install owlready2")
        
except Exception as e:
    print(f"   ✗ Failed to initialize OntologyManager: {e}")

# Test 5: Initialize parsers
print("\n5. Testing parser initialization...")
try:
    hetionet = HetionetParser()
    print(f"   ✓ HetionetParser initialized: {hetionet.source_dir}")
    
    ncbigene = NCBIGeneParser()
    print(f"   ✓ NCBIGeneParser initialized: {ncbigene.source_dir}")
    
    drugbank = DrugBankParser()
    print(f"   ✓ DrugBankParser initialized: {drugbank.source_dir}")
    
    disgenet = DisGeNETParser()
    print(f"   ✓ DisGeNETParser initialized: {disgenet.source_dir}")
    
    aopdb = AOPDBParser()
    print(f"   ✓ AOPDBParser initialized: {aopdb.source_dir}")
    
except Exception as e:
    print(f"   ✗ Failed to initialize parsers: {e}")

# Test 6: Check parser schemas
print("\n6. Testing parser schemas...")
try:
    hetionet = HetionetParser()
    schema = hetionet.get_schema()
    print(f"   ✓ HetionetParser schema: {list(schema.keys())}")
    
    ncbigene = NCBIGeneParser()
    schema = ncbigene.get_schema()
    print(f"   ✓ NCBIGeneParser schema: {list(schema.keys())}")
    
except Exception as e:
    print(f"   ✗ Failed to get schemas: {e}")

# Test 7: Check main.py
print("\n7. Testing main.py...")
try:
    from main import AlzKBBuilder
    builder = AlzKBBuilder()
    print("   ✓ AlzKBBuilder initialized")
    print(f"   Data directory: {builder.data_dir}")
except Exception as e:
    print(f"   ✗ Failed to import/initialize AlzKBBuilder: {e}")

print("\n" + "=" * 80)
print("Test Summary")
print("=" * 80)
print("✓ Basic implementation validation complete")
print("\nNext steps:")
print("1. Install dependencies: pip install -r requirements.txt")
print("2. Download data sources (see BUILD_GUIDE.md)")
print("3. Run: cd src && python main.py")
print("=" * 80)
