"""
Ontology module for AlzKB v2.

This module provides functionality for working with the AlzKB OWL ontology,
including loading, populating, and querying the ontology.
"""

from .alzkb_populator import AlzKBOntologyPopulator, get_default_configs

__all__ = ['AlzKBOntologyPopulator', 'get_default_configs']
