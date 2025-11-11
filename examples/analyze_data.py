#!/usr/bin/env python3
"""
Example script showing how to analyze AlzKB exported data.
"""
import pandas as pd
import glob
import os

def find_latest_file(pattern):
    """Find the most recent file matching the pattern."""
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def main():
    print("="*60)
    print("AlzKB Data Analysis Example")
    print("="*60)
    
    # Find latest data files
    protein_file = find_latest_file("../data/processed/alzkb_uniprot_*.csv")
    compound_file = find_latest_file("../data/processed/alzkb_pubchem_*.csv")
    summary_file = find_latest_file("../data/processed/alzkb_summary_*.csv")
    
    if not protein_file or not compound_file:
        print("\nError: No data files found. Please run the updater first:")
        print("  ./run.sh")
        return
    
    print(f"\nLoading data...")
    print(f"  Proteins: {protein_file}")
    print(f"  Compounds: {compound_file}")
    
    # Load data
    proteins = pd.read_csv(protein_file)
    compounds = pd.read_csv(compound_file)
    
    # Basic statistics
    print("\n" + "="*60)
    print("BASIC STATISTICS")
    print("="*60)
    
    print(f"\nProteins:")
    print(f"  Total records: {len(proteins)}")
    print(f"  Unique proteins: {proteins['uniprot_id'].nunique()}")
    print(f"  Organisms: {proteins['organism'].nunique()}")
    
    print(f"\nCompounds:")
    print(f"  Total records: {len(compounds)}")
    print(f"  Unique compounds: {compounds['pubchem_cid'].nunique()}")
    print(f"  Avg molecular weight: {compounds['molecular_weight'].mean():.2f}")
    
    # Top organisms
    print("\n" + "="*60)
    print("TOP 5 ORGANISMS")
    print("="*60)
    print(proteins['organism'].value_counts().head())
    
    # Proteins with disease associations
    print("\n" + "="*60)
    print("DISEASE ASSOCIATIONS")
    print("="*60)
    disease_proteins = proteins[proteins['disease_association'].notna()]
    print(f"Proteins with disease associations: {len(disease_proteins)}")
    
    if len(disease_proteins) > 0:
        print("\nExample disease-associated proteins:")
        print(disease_proteins[['uniprot_id', 'protein_name', 'gene_name']].head())
    
    # Molecular weight distribution
    print("\n" + "="*60)
    print("COMPOUND PROPERTIES")
    print("="*60)
    print(f"Molecular weight range: {compounds['molecular_weight'].min():.2f} - {compounds['molecular_weight'].max():.2f}")
    print(f"Median molecular weight: {compounds['molecular_weight'].median():.2f}")
    
    # Load summary if available
    if summary_file:
        print("\n" + "="*60)
        print("DATA QUALITY SUMMARY")
        print("="*60)
        summary = pd.read_csv(summary_file)
        print(summary.to_string(index=False))
    
    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)

if __name__ == "__main__":
    main()
