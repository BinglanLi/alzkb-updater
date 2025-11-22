"""
Ontology module for AlzKB v2.

This module provides functionality for working with the AlzKB OWL ontology,
including loading, populating, and querying the ontology.
"""

from .ontology_manager import OntologyManager
from .ontology_populator import OntologyPopulator

__all__ = ['OntologyManager', 'OntologyPopulator']
