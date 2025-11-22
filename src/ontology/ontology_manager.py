"""
OntologyManager: Manages the AlzKB OWL ontology.

This class provides functionality for loading and working with the AlzKB ontology.
"""

import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class OntologyManager:
    """
    Manages the AlzKB OWL ontology.
    
    This class handles loading the ontology file and provides access to
    ontology classes, properties, and individuals.
    """
    
    def __init__(self, ontology_path: Optional[str] = None):
        """
        Initialize the OntologyManager.
        
        Args:
            ontology_path: Path to the ontology RDF file. If None, uses default location.
        """
        self.ontology_path = ontology_path
        self.ontology = None
        self._owlready2_available = False
        
        # Check if owlready2 is available
        try:
            import owlready2
            self._owlready2_available = True
            logger.info("owlready2 is available")
        except ImportError:
            logger.warning("owlready2 not available. Ontology functionality will be limited.")
            logger.warning("Install with: pip install owlready2")
    
    def load_ontology(self, ontology_path: Optional[str] = None) -> bool:
        """
        Load the ontology from file.
        
        Args:
            ontology_path: Path to the ontology RDF file. If None, uses the path
                          provided during initialization or default location.
        
        Returns:
            True if successful, False otherwise.
        """
        if not self._owlready2_available:
            logger.error("Cannot load ontology: owlready2 not available")
            return False
        
        import owlready2
        
        if ontology_path:
            self.ontology_path = ontology_path
        
        if not self.ontology_path:
            # Use default location
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.ontology_path = os.path.join(
                current_dir, "..", "..", "data", "ontology", "alzkb_v2.rdf"
            )
        
        if not os.path.exists(self.ontology_path):
            logger.error(f"Ontology file not found: {self.ontology_path}")
            return False
        
        try:
            logger.info(f"Loading ontology from: {self.ontology_path}")
            self.ontology = owlready2.get_ontology(f"file://{self.ontology_path}").load()
            logger.info(f"✓ Successfully loaded ontology")
            return True
        except Exception as e:
            logger.error(f"Failed to load ontology: {e}")
            return False
    
    def get_ontology(self):
        """Get the loaded ontology object."""
        return self.ontology
    
    def is_loaded(self) -> bool:
        """Check if ontology is loaded."""
        return self.ontology is not None
    
    def get_classes(self):
        """Get all classes defined in the ontology."""
        if not self.is_loaded():
            logger.error("Ontology not loaded")
            return []
        
        return list(self.ontology.classes())
    
    def get_properties(self):
        """Get all properties defined in the ontology."""
        if not self.is_loaded():
            logger.error("Ontology not loaded")
            return []
        
        return list(self.ontology.properties())
    
    def get_individuals(self):
        """Get all individuals in the ontology."""
        if not self.is_loaded():
            logger.error("Ontology not loaded")
            return []
        
        return list(self.ontology.individuals())
    
    def save_ontology(self, output_path: Optional[str] = None):
        """
        Save the ontology to file.
        
        Args:
            output_path: Path to save the ontology. If None, overwrites the original file.
        """
        if not self.is_loaded():
            logger.error("Cannot save: Ontology not loaded")
            return False
        
        save_path = output_path or self.ontology_path
        
        try:
            self.ontology.save(file=save_path)
            logger.info(f"✓ Saved ontology to: {save_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save ontology: {e}")
            return False
    
    def print_statistics(self):
        """Print statistics about the ontology."""
        if not self.is_loaded():
            logger.error("Ontology not loaded")
            return
        
        print("\n=== Ontology Statistics ===")
        print(f"Classes: {len(list(self.ontology.classes()))}")
        print(f"Properties: {len(list(self.ontology.properties()))}")
        print(f"Individuals: {len(list(self.ontology.individuals()))}")
