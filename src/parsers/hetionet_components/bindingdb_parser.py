"""
BindingDB Parser for AlzKB.

This module parses BindingDB data to extract drug-gene binding relationships
(chemicalBindsGene) for AlzKB.

Data Source: https://www.bindingdb.org/bind/downloads/

Output:
  - drug_binds_gene.tsv: chemicalBindsGene relationships with binding affinity
"""

import logging
import zipfile
from pathlib import Path
from typing import Dict, List
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)


class BindingDBParser(BaseParser):
    """
    Parser for BindingDB database.

    Extracts drug-target binding data including affinity measurements
    for use in AlzKB's chemicalBindsGene relationships.
    """

    # BindingDB download URL (update version as needed)
    BINDINGDB_URL = "https://www.bindingdb.org/bind/downloads/BindingDB_All_2024m11.tsv.zip"

    def __init__(self, data_dir: str):
        """
        Initialize the BindingDB parser.

        Args:
            data_dir: Directory to store downloaded and processed data
        """
        super().__init__(data_dir)
        self.source_name = "bindingdb"

    def download_data(self) -> bool:
        """
        Download the BindingDB TSV file.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading BindingDB...")

        result = self.download_file(self.BINDINGDB_URL, "BindingDB_All.tsv.zip")

        if result:
            # Extract the zip file
            zip_path = self.source_dir / "BindingDB_All.tsv.zip"
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(self.source_dir)
                logger.info(f"Successfully extracted BindingDB")
                return True
            except Exception as e:
                logger.error(f"Failed to extract BindingDB: {e}")
                return False
        else:
            logger.error("Failed to download BindingDB")
            return False

    def parse_data(self) -> Dict[str, pd.DataFrame]:
        """
        Parse the BindingDB TSV file.

        Returns:
            Dictionary with:
              - 'drug_binds_gene': DataFrame of drug-gene binding relationships
        """
        # Find the TSV file (name varies by version)
        tsv_files = list(self.source_dir.glob("BindingDB_All*.tsv"))
        if not tsv_files:
            logger.error("BindingDB TSV file not found")
            return {}

        tsv_path = tsv_files[0]
        logger.info(f"Parsing BindingDB from {tsv_path}")

        try:
            # Read BindingDB (large file, select relevant columns)
            # Key columns based on BindingDB schema
            usecols = [
                'Ligand SMILES',
                'Ligand InChI',
                'Ligand InChI Key',
                'BindingDB Ligand Name',
                'Target Name',
                'Target Source Organism According to Curator or DataSource',
                'Ki (nM)',
                'IC50 (nM)',
                'Kd (nM)',
                'EC50 (nM)',
                'UniProt (SwissProt) Primary ID of Target Chain',
                'PubChem CID',
                'DrugBank ID of Ligand',
                'ChEMBL ID of Ligand'
            ]

            # Try reading with specific columns
            try:
                df = pd.read_csv(
                    tsv_path,
                    sep='\t',
                    usecols=lambda x: x in usecols,
                    low_memory=False,
                    on_bad_lines='skip'
                )
            except Exception:
                # Fall back to reading all columns
                df = pd.read_csv(
                    tsv_path,
                    sep='\t',
                    low_memory=False,
                    nrows=1000000,  # Limit for memory
                    on_bad_lines='skip'
                )

            logger.info(f"Loaded {len(df)} BindingDB entries")

            # Filter for human targets
            if 'Target Source Organism According to Curator or DataSource' in df.columns:
                df = df[df['Target Source Organism According to Curator or DataSource'].str.contains(
                    'Homo sapiens', case=False, na=False
                )]

            # Extract binding relationships
            bindings = self._extract_bindings(df)

            logger.info(f"Extracted {len(bindings)} drug-gene binding relationships")

            return {
                "drug_binds_gene": pd.DataFrame(bindings)
            }

        except Exception as e:
            logger.error(f"Error parsing BindingDB: {e}")
            return {}

    def _extract_bindings(self, df: pd.DataFrame) -> List[Dict]:
        """
        Extract drug-gene binding relationships from BindingDB data.

        Args:
            df: BindingDB DataFrame

        Returns:
            List of binding relationship dictionaries
        """
        bindings = []

        # Map column names (handle variations)
        ligand_name_col = self._find_column(df, ['BindingDB Ligand Name', 'Ligand Name'])
        target_name_col = self._find_column(df, ['Target Name'])
        uniprot_col = self._find_column(df, ['UniProt (SwissProt) Primary ID of Target Chain', 'UniProt ID'])
        drugbank_col = self._find_column(df, ['DrugBank ID of Ligand', 'DrugBank ID'])
        pubchem_col = self._find_column(df, ['PubChem CID'])
        ki_col = self._find_column(df, ['Ki (nM)'])
        ic50_col = self._find_column(df, ['IC50 (nM)'])
        kd_col = self._find_column(df, ['Kd (nM)'])

        for _, row in df.iterrows():
            # Get ligand identifier
            ligand_name = row.get(ligand_name_col, '') if ligand_name_col else ''
            drugbank_id = row.get(drugbank_col, '') if drugbank_col else ''
            pubchem_cid = row.get(pubchem_col, '') if pubchem_col else ''

            # Get target identifier
            target_name = row.get(target_name_col, '') if target_name_col else ''
            uniprot_id = row.get(uniprot_col, '') if uniprot_col else ''

            if not (ligand_name or drugbank_id) or not (target_name or uniprot_id):
                continue

            # Get best affinity value
            affinity_nm = None
            affinity_type = None

            for col, atype in [(ki_col, 'Ki'), (kd_col, 'Kd'), (ic50_col, 'IC50')]:
                if col:
                    val = row.get(col, '')
                    try:
                        if pd.notna(val) and val != '' and val != '>':
                            # Handle range values (e.g., ">10000")
                            val_str = str(val).replace('>', '').replace('<', '').strip()
                            affinity_nm = float(val_str)
                            affinity_type = atype
                            break
                    except (ValueError, TypeError):
                        continue

            binding = {
                "ligand_name": ligand_name,
                "drugbank_id": drugbank_id if pd.notna(drugbank_id) else "",
                "pubchem_cid": pubchem_cid if pd.notna(pubchem_cid) else "",
                "target_name": target_name,
                "uniprot_id": uniprot_id if pd.notna(uniprot_id) else "",
                "affinity_nm": affinity_nm,
                "affinity_type": affinity_type,
                "relationship": "chemicalBindsGene",
                "source": "BindingDB"
            }
            bindings.append(binding)

        # Remove duplicates
        seen = set()
        unique_bindings = []
        for b in bindings:
            key = (b['drugbank_id'] or b['ligand_name'], b['uniprot_id'] or b['target_name'])
            if key not in seen:
                seen.add(key)
                unique_bindings.append(b)

        return unique_bindings

    def _find_column(self, df: pd.DataFrame, candidates: List[str]) -> str:
        """Find first matching column name from candidates."""
        for col in candidates:
            if col in df.columns:
                return col
        return None

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the schema for BindingDB data.

        Returns:
            Dictionary defining the schema for drug-gene binding relationships
        """
        return {
            "drug_binds_gene": {
                "ligand_name": "Ligand/drug name",
                "drugbank_id": "DrugBank ID (if available)",
                "pubchem_cid": "PubChem Compound ID",
                "target_name": "Target protein name",
                "uniprot_id": "UniProt ID of target",
                "affinity_nm": "Binding affinity in nM",
                "affinity_type": "Type of affinity measurement (Ki, Kd, IC50)",
                "relationship": "Relationship type (chemicalBindsGene)",
                "source": "Data source (BindingDB)"
            }
        }
