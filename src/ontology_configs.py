"""
AlzKB Ontology Population Configurations

This file defines the ista configurations for populating the AlzKB ontology.

Config keys use format: {source_name}.{data_name}
Property names are strings that will be resolved to ontology objects at runtime.
Each config includes source_filename to be self-contained.

Data types:
- 'node': Use populate_nodes() / parse_node_type()
- 'relationship': Use populate_relationships() / parse_relationship_type()
"""

# Define constants for filename stems
# AOPDB
AOPDB_AOPS = 'aops'
AOPDB_PATHWAYS = 'pathways'
AOPDB_GENE_PATHWAY_RELATIONSHIPS = 'gene_pathway_relationships'
AOPDB_DRUGS = 'drugs'
# DisGeNET
DISGENET_DISEASE_CLASSIFICATIONS = 'disease_classifications'
DISGENET_DISEASE_MAPPINGS = 'disease_mappings'
DISGENET_GENE_DISEASE_ASSOCIATIONS = 'gene_disease_associations'
# DrugBank
DRUGBANK_DRUGS = 'drugs'
# NCBI Gene
NCBI_GENES = 'genes'
# DoRothEA
DOROTHEA_TRANSCRIPTION_FACTORS = 'transcription_factors'
DOROTHEA_TF_GENE_INTERACTIONS = 'tf_gene_interactions'


# AOPDB_TABLE_MAPPING: KEY = source filename stem; VALUE = AOPDB table name
AOPDB_TABLE_MAPPING = {
    AOPDB_AOPS: 'aop_info',
    AOPDB_PATHWAYS: 'pathway_gene',
    AOPDB_GENE_PATHWAY_RELATIONSHIPS: 'pathway_gene',
    AOPDB_DRUGS: 'chemical_info',
}


ONTOLOGY_CONFIGS = {
    # =========================================================================
    # AOP-DB - Adverse Outcome Pathway Database
    # =========================================================================
    f'aopdb.{AOPDB_DRUGS}': {
        'data_type': 'node',
        'node_type': 'Drug',
        'source_filename': f'{AOPDB_DRUGS}.tsv',
        'parse_config': {
            'headers': True,
            'iri_column_name': 'DTX_id',
            'data_property_map': {
                'ChemicalID': 'xrefMeSH',
                'source_database': 'sourceDatabase',
            },
            'merge_column': {
                'source_column_name': 'DTX_id',
                'data_property': 'xrefDTXSID',
            },
        },
        'merge': True,
        'skip': False,
    },
    f'aopdb.{AOPDB_PATHWAYS}': {
        'data_type': 'node',
        'node_type': 'Pathway',
        'source_filename': f'{AOPDB_PATHWAYS}.tsv',
        'parse_config': {
            'headers': True,
            'iri_column_name': 'path_name',
            'data_property_map': {
                'path_id': 'pathwayId',
                'path_name': 'pathwayName',
                'ext_source': 'sourceDatabase',
                'source_database': 'sourceDatabase',
            },
        },
        'merge': False,
        'skip': False,
    },
    f'aopdb.{AOPDB_GENE_PATHWAY_RELATIONSHIPS}': {
        'data_type': 'relationship',
        'relationship_type': 'geneInPathway',
        'inverse_relationship_type': 'pathwayContainsGene', # not PathwayContainsGene
        'source_filename': f'{AOPDB_GENE_PATHWAY_RELATIONSHIPS}.tsv',
        'parse_config': {
            'headers': True,
            'subject_node_type': 'Gene',
            'subject_column_name': 'entrez',
            'subject_match_property': 'xrefNcbiGene',
            'object_node_type': 'Pathway',
            'object_column_name': 'path_name',
            'object_match_property': 'pathwayName',
        },
        'merge': False,
        'skip': False,
    },

    # =========================================================================
    # DisGeNET - Gene-Disease Associations
    # =========================================================================
    f'disgenet.{DISGENET_DISEASE_CLASSIFICATIONS}': {
        'data_type': 'node',
        'node_type': 'Disease',
        'source_filename': f'{DISGENET_DISEASE_CLASSIFICATIONS}.tsv',
        'parse_config': {
            'headers': True,
            'iri_column_name': 'diseaseId',
            'data_property_map': {
                'diseaseId': 'xrefUmlsCUI',
                'diseaseName': 'commonName',
                'sourceDatabase': 'sourceDatabase',
            },
        },
        'merge': False,
        'skip': False,
    },
    f'disgenet.{DISGENET_DISEASE_MAPPINGS}': {
        'data_type': 'node',
        'node_type': 'Disease',
        'source_filename': f'{DISGENET_DISEASE_MAPPINGS}.tsv',
        'parse_config': {
            'headers': True,
            'iri_column_name': 'diseaseId',
            'filter_column': 'DO',
            'filter_value': '0',
            'merge_column': {
                'source_column_name': 'diseaseId',
                'data_property': 'xrefUmlsCUI',
                'sourceDatabase': 'sourceDatabase',
            },
            'data_property_map': {
                'DO': 'xrefDiseaseOntology',
            },
        },
        'merge': True,
        'skip': False,
    },
    f'disgenet.{DISGENET_GENE_DISEASE_ASSOCIATIONS}': {
        'data_type': 'relationship',
        'relationship_type': 'geneAssociatesWithDisease',
        'source_filename': f'{DISGENET_GENE_DISEASE_ASSOCIATIONS}.tsv',
        'parse_config': {
            'headers': True,
            'subject_node_type': 'Gene',
            'subject_column_name': 'geneSymbol',
            'subject_match_property': 'geneSymbol',
            'object_node_type': 'Disease',
            'object_column_name': 'diseaseId',
            'object_match_property': 'xrefUmlsCUI',
            'filter_column': 'diseaseType',
            'filter_value': 'disease',
        },
        'merge': False,
        'skip': False,
    },

    # =========================================================================
    # DrugBank - Drug Information
    # =========================================================================
    f'drugbank.{DRUGBANK_DRUGS}': {
        'data_type': 'node',
        'node_type': 'Drug',
        'source_filename': f'{DRUGBANK_DRUGS}.tsv',
        'parse_config': {
            'headers': True,
            'iri_column_name': 'drugbank_id',
            'data_property_map': {
                'drugbank_id': 'xrefDrugbank',
                'cas_number': 'xrefCasRN',
                'drug_name': 'commonName',
                'source_database': 'sourceDatabase',
            },
            'merge_column': {
                'source_column_name': 'cas_number',
                'data_property': 'xrefCasRN',
            },
        },
        'merge': True,
        'skip': False,
    },

    # =========================================================================
    # NCBI Gene - Gene Information
    # =========================================================================
    f'ncbigene.{NCBI_GENES}': {
        'data_type': 'node',
        'node_type': 'Gene',
        'source_filename': f'{NCBI_GENES}.tsv',
        'parse_config': {
            'headers': True,
            'iri_column_name': 'Symbol',
            'compound_fields': {
                'dbXrefs': {'delimiter': '|', 'field_split_prefix': ':'},
            },
            'data_property_map': {
                'GeneID': 'xrefNcbiGene',
                'Symbol': 'geneSymbol',
                'type_of_gene': 'typeOfGene',
                'Full_name_from_nomenclature_authority': 'commonName',
                'xref_MIM': 'xrefOMIM',
                'xref_HGNC': 'xrefHGNC',
                'xref_Ensembl': 'xrefEnsembl',
                'chromosome': 'chromosome',
                'source_database': 'sourceDatabase',
            },
        },
        'merge': False,
        'skip': False,
    },

    # =========================================================================
    # DoRothEA - Transcription Factor Regulatory Network
    # =========================================================================
    f'dorothea.{DOROTHEA_TRANSCRIPTION_FACTORS}': {
        'data_type': 'node',
        'node_type': 'TranscriptionFactor',
        'source_filename': f'{DOROTHEA_TRANSCRIPTION_FACTORS}.tsv',
        'parse_config': {
            'headers': True,
            'iri_column_name': 'tf_symbol',
            'data_property_map': {
                'tf_symbol': 'TF',
                'source_database': 'sourceDatabase',
            },
        },
        'merge': True,
        'skip': False,
    },
    
    f'dorothea.{DOROTHEA_TF_GENE_INTERACTIONS}': {
        'data_type': 'relationship',
        'relationship_type': 'transcriptionFactorInteractsWithGene',
        'source_filename': f'{DOROTHEA_TF_GENE_INTERACTIONS}.tsv',
        'parse_config': {
            'headers': True,
            'subject_node_type': 'TranscriptionFactor',
            'subject_column_name': 'tf_symbol',
            'subject_match_property': 'TF',
            'object_node_type': 'Gene',
            'object_column_name': 'target_gene',
            'object_match_property': 'geneSymbol',
        },
        'merge': False,
        'skip': False,
    },

    # =========================================================================
    # Disease Ontology - Disease Nodes (commented out - not yet implemented)
    # =========================================================================
    # 'disease_ontology.disease_nodes': {
    #     'data_type': 'node',
    #     'node_type': 'Disease',
    #     'source_filename': 'disease_nodes.tsv',
    #     'parse_config': {
    #         'headers': True,
    #         'iri_column_name': 'doid',
    #         'data_property_map': {
    #             'name': 'commonName',
    #             'definition': 'definition',
    #         },
    #     },
    #     'merge': False,
    #     'skip': False,
    # },
    # 'disease_ontology.disease_anatomy': {
    #     'data_type': 'relationship',
    #     'relationship_type': 'diseaseLocalizesToAnatomy',
    #     'source_filename': 'disease_anatomy.tsv',
    #     'parse_config': {
    #         'headers': True,
    #         'subject_node_type': 'Disease',
    #         'subject_column_name': 'disease_id',
    #         'subject_match_property': 'diseaseOntologyId',
    #         'object_node_type': 'BodyPart',
    #         'object_column_name': 'anatomy_id',
    #         'object_match_property': 'uberonId',
    #     },
    #     'merge': False,
    #     'skip': False,
    # },

    # =========================================================================
    # Gene Ontology - GO Terms and Gene Associations (commented out)
    # =========================================================================
    # 'gene_ontology.biological_process_nodes': {
    #     'data_type': 'node',
    #     'node_type': 'BiologicalProcess',
    #     'source_filename': 'biological_process_nodes.tsv',
    #     'parse_config': {
    #         'headers': True,
    #         'iri_column_name': 'go_id',
    #         'data_property_map': {
    #             'name': 'commonName',
    #             'definition': 'definition',
    #         },
    #     },
    #     'merge': False,
    #     'skip': False,
    # },
    # 'gene_ontology.gene_bp_associations': {
    #     'data_type': 'relationship',
    #     'relationship_type': 'geneParticipatesInBiologicalProcess',
    #     'source_filename': 'gene_bp_associations.tsv',
    #     'parse_config': {
    #         'headers': True,
    #         'subject_node_type': 'Gene',
    #         'subject_column_name': 'gene_id',
    #         'subject_match_property': 'xrefNcbiGene',
    #         'object_node_type': 'BiologicalProcess',
    #         'object_column_name': 'go_id',
    #         'object_match_property': 'geneOntologyId',
    #     },
    #     'merge': False,
    #     'skip': False,
    # },

    # =========================================================================
    # Uberon - Anatomy/BodyPart Nodes (commented out)
    # =========================================================================
    # 'uberon.anatomy_nodes': {
    #     'data_type': 'node',
    #     'node_type': 'BodyPart',
    #     'source_filename': 'anatomy_nodes.tsv',
    #     'parse_config': {
    #         'headers': True,
    #         'iri_column_name': 'uberon_id',
    #         'data_property_map': {
    #             'name': 'commonName',
    #             'definition': 'definition',
    #         },
    #     },
    #     'merge': False,
    #     'skip': False,
    # },

    # =========================================================================
    # MeSH - Symptom Nodes (commented out)
    # =========================================================================
    # 'mesh.symptom_nodes': {
    #     'data_type': 'node',
    #     'node_type': 'Symptom',
    #     'source_filename': 'symptom_nodes.tsv',
    #     'parse_config': {
    #         'headers': True,
    #         'iri_column_name': 'mesh_id',
    #         'data_property_map': {
    #             'name': 'commonName',
    #             'tree_numbers': 'meshTreeNumber',
    #         },
    #     },
    #     'merge': False,
    #     'skip': False,
    # },

    # =========================================================================
    # GWAS Catalog - Gene-Disease Associations (commented out)
    # =========================================================================
    # 'gwas.gene_disease_associations': {
    #     'data_type': 'relationship',
    #     'relationship_type': 'geneAssociatesWithDisease',
    #     'source_filename': 'gene_disease_associations.tsv',
    #     'parse_config': {
    #         'headers': True,
    #         'subject_node_type': 'Gene',
    #         'subject_column_name': 'gene_symbol',
    #         'subject_match_property': 'geneSymbol',
    #         'object_node_type': 'Disease',
    #         'object_column_name': 'disease_id',
    #         'object_match_property': 'diseaseOntologyId',
    #     },
    #     'merge': False,
    #     'skip': False,
    # },

    # =========================================================================
    # DrugCentral - Drug-Disease Relationships (commented out)
    # =========================================================================
    # 'drugcentral.drug_treats_disease': {
    #     'data_type': 'relationship',
    #     'relationship_type': 'drugTreatsDisease',
    #     'source_filename': 'drug_treats_disease.tsv',
    #     'parse_config': {
    #         'headers': True,
    #         'subject_node_type': 'Drug',
    #         'subject_column_name': 'drug_id',
    #         'subject_match_property': 'drugbankId',
    #         'object_node_type': 'Disease',
    #         'object_column_name': 'disease_id',
    #         'object_match_property': 'diseaseOntologyId',
    #     },
    #     'merge': False,
    #     'skip': False,
    # },

    # =========================================================================
    # BindingDB - Drug-Gene Binding (commented out)
    # =========================================================================
    # 'bindingdb.drug_binds_gene': {
    #     'data_type': 'relationship',
    #     'relationship_type': 'chemicalBindsGene',
    #     'source_filename': 'drug_binds_gene.tsv',
    #     'parse_config': {
    #         'headers': True,
    #         'subject_node_type': 'Drug',
    #         'subject_column_name': 'drug_id',
    #         'subject_match_property': 'drugbankId',
    #         'object_node_type': 'Gene',
    #         'object_column_name': 'gene_symbol',
    #         'object_match_property': 'geneSymbol',
    #     },
    #     'merge': False,
    #     'skip': False,
    # },

    # =========================================================================
    # Bgee - Gene Expression in Anatomy (commented out)
    # =========================================================================
    # 'bgee.bodypart_overexpresses_gene': {
    #     'data_type': 'relationship',
    #     'relationship_type': 'bodyPartOverexpressesGene',
    #     'source_filename': 'bodypart_overexpresses_gene.tsv',
    #     'parse_config': {
    #         'headers': True,
    #         'subject_node_type': 'BodyPart',
    #         'subject_column_name': 'anatomy_id',
    #         'subject_match_property': 'uberonId',
    #         'object_node_type': 'Gene',
    #         'object_column_name': 'gene_id',
    #         'object_match_property': 'xrefNcbiGene',
    #     },
    #     'merge': False,
    #     'skip': False,
    # },

    # =========================================================================
    # CTD - Chemical-Gene Expression Interactions (commented out)
    # =========================================================================
    # 'ctd.chemical_increases_expression': {
    #     'data_type': 'relationship',
    #     'relationship_type': 'chemicalIncreasesExpression',
    #     'source_filename': 'chemical_increases_expression.tsv',
    #     'parse_config': {
    #         'headers': True,
    #         'subject_node_type': 'Drug',
    #         'subject_column_name': 'chemical_id',
    #         'subject_match_property': 'drugbankId',
    #         'object_node_type': 'Gene',
    #         'object_column_name': 'gene_id',
    #         'object_match_property': 'xrefNcbiGene',
    #     },
    #     'merge': False,
    #     'skip': False,
    # },

    # =========================================================================
    # Hetionet Precomputed - Gene-Gene Relationships (commented out)
    # =========================================================================
    # 'hetionet_precomputed.gene_interacts': {
    #     'data_type': 'relationship',
    #     'relationship_type': 'geneInteractsWithGene',
    #     'source_filename': 'gene_interacts.tsv',
    #     'parse_config': {
    #         'headers': True,
    #         'subject_node_type': 'Gene',
    #         'subject_column_name': 'source_gene',
    #         'subject_match_property': 'xrefNcbiGene',
    #         'object_node_type': 'Gene',
    #         'object_column_name': 'target_gene',
    #         'object_match_property': 'xrefNcbiGene',
    #     },
    #     'merge': False,
    #     'skip': False,
    # },

    # =========================================================================
    # PubTator/MEDLINE - Literature Co-occurrence (commented out)
    # =========================================================================
    # 'pubtator.disease_disease_cooccurrence': {
    #     'data_type': 'relationship',
    #     'relationship_type': 'diseaseAssociatesWithDisease',
    #     'source_filename': 'disease_disease_cooccurrence.tsv',
    #     'parse_config': {
    #         'headers': True,
    #         'subject_node_type': 'Disease',
    #         'subject_column_name': 'disease1_id',
    #         'subject_match_property': 'diseaseOntologyId',
    #         'object_node_type': 'Disease',
    #         'object_column_name': 'disease2_id',
    #         'object_match_property': 'diseaseOntologyId',
    #     },
    #     'merge': False,
    #     'skip': False,
    # },
}
