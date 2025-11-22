"""
OntologyPopulator: Populates the AlzKB ontology with data from various sources.

This class provides functionality for adding individuals and relationships
to the ontology based on data from external sources.
"""

import logging
from typing import Dict, Any, Optional, List
import pandas as pd

logger = logging.getLogger(__name__)


class OntologyPopulator:
    """
    Populates the AlzKB ontology with data from various sources.
    
    This class handles the process of creating individuals and relationships
    in the ontology based on parsed data from external sources.
    """
    
    def __init__(self, ontology_manager):
        """
        Initialize the OntologyPopulator.
        
        Args:
            ontology_manager: An OntologyManager instance with a loaded ontology.
        """
        self.ontology_manager = ontology_manager
        self.ontology = ontology_manager.get_ontology()
        
        if not self.ontology:
            raise ValueError("Ontology must be loaded before populating")
    
    def add_individual(self, 
                      class_name: str, 
                      individual_id: str,
                      properties: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add an individual to the ontology.
        
        Args:
            class_name: Name of the ontology class for this individual
            individual_id: Unique identifier for the individual
            properties: Dictionary of property names and values
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the class from ontology
            onto_class = getattr(self.ontology, class_name, None)
            if not onto_class:
                logger.error(f"Class not found in ontology: {class_name}")
                return False
            
            # Create individual
            individual = onto_class(individual_id)
            
            # Set properties if provided
            if properties:
                for prop_name, prop_value in properties.items():
                    if hasattr(individual, prop_name):
                        setattr(individual, prop_name, prop_value)
                    else:
                        logger.warning(f"Property not found: {prop_name}")
            
            logger.debug(f"Added individual: {individual_id} ({class_name})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add individual {individual_id}: {e}")
            return False
    
    def add_individuals_from_dataframe(self,
                                      df: pd.DataFrame,
                                      class_name: str,
                                      id_column: str,
                                      property_mapping: Dict[str, str]) -> int:
        """
        Add multiple individuals from a pandas DataFrame.
        
        Args:
            df: DataFrame containing the data
            class_name: Name of the ontology class for these individuals
            id_column: Name of the column containing unique identifiers
            property_mapping: Mapping of DataFrame columns to ontology properties
        
        Returns:
            Number of individuals successfully added
        """
        count = 0
        
        for idx, row in df.iterrows():
            individual_id = str(row[id_column])
            
            # Build properties dictionary
            properties = {}
            for df_col, onto_prop in property_mapping.items():
                if df_col in row and pd.notna(row[df_col]):
                    properties[onto_prop] = row[df_col]
            
            if self.add_individual(class_name, individual_id, properties):
                count += 1
        
        logger.info(f"Added {count}/{len(df)} individuals of type {class_name}")
        return count
    
    def add_relationship(self,
                        subject_id: str,
                        predicate: str,
                        object_id: str) -> bool:
        """
        Add a relationship (triple) to the ontology.
        
        Args:
            subject_id: ID of the subject individual
            predicate: Name of the object property (relationship type)
            object_id: ID of the object individual
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find individuals
            subject = self.ontology.search_one(iri=f"*{subject_id}")
            obj = self.ontology.search_one(iri=f"*{object_id}")
            
            if not subject:
                logger.error(f"Subject not found: {subject_id}")
                return False
            
            if not obj:
                logger.error(f"Object not found: {object_id}")
                return False
            
            # Get property
            prop = getattr(self.ontology, predicate, None)
            if not prop:
                logger.error(f"Property not found: {predicate}")
                return False
            
            # Add relationship
            getattr(subject, predicate).append(obj)
            logger.debug(f"Added relationship: {subject_id} -{predicate}-> {object_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add relationship: {e}")
            return False
    
    def add_relationships_from_dataframe(self,
                                        df: pd.DataFrame,
                                        subject_column: str,
                                        predicate: str,
                                        object_column: str) -> int:
        """
        Add multiple relationships from a pandas DataFrame.
        
        Args:
            df: DataFrame containing the relationships
            subject_column: Column containing subject IDs
            predicate: Name of the relationship type
            object_column: Column containing object IDs
        
        Returns:
            Number of relationships successfully added
        """
        count = 0
        
        for idx, row in df.iterrows():
            subject_id = str(row[subject_column])
            object_id = str(row[object_column])
            
            if self.add_relationship(subject_id, predicate, object_id):
                count += 1
        
        logger.info(f"Added {count}/{len(df)} relationships of type {predicate}")
        return count
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the populated ontology.
        
        Returns:
            Dictionary with counts of different entity types
        """
        stats = {
            'total_individuals': len(list(self.ontology.individuals())),
            'classes': len(list(self.ontology.classes())),
            'properties': len(list(self.ontology.properties()))
        }
        
        # Count individuals by class
        for onto_class in self.ontology.classes():
            class_name = onto_class.name
            count = len(list(onto_class.instances()))
            if count > 0:
                stats[f'individuals_{class_name}'] = count
        
        return stats
