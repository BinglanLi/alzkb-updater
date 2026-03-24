# AlzKB Source Database Critiques

This document provides a critique and summary for each source database identified for the AlzKB project, drawing from published peer-reviewed papers and the databases' respective websites. 

---

## 1. AOP-DB (Adverse Outcome Pathway Database)
- **Excerpt:** Developed by the EPA, AOP-DB integrates Adverse Outcome Pathway (AOP) knowledge with external biomedical databases. It facilitates the computational discovery of potential AOPs and relates them to chemical stressors and disease outcomes. 
- **Availability:** No (Inaccessible (Error: HTTPSConnectionPool(host='aopkb.bmap.clo))
- **Update Frequency:** semi-annual (Latest: V2, 2021-04-23)
- **Available Data:** 
  - *Nodes:* Drug, Pathway
  - *Edges:* geneInPathway, pathwayContainsGene
- **Tested Download Link:** https://aopkb.bmap.cloud/
- **Access Approach:** web-based downloads (typically TSV/SQL)

## 2. Bgee
- **Excerpt:** Bgee is a database for retrieval and comparison of gene expression patterns across multiple animal species. It curates RNA-Seq, microarray, in situ hybridization, and EST data to produce highly reliable presence/absence calls for gene expression in anatomy.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** Annual check (Latest: V15.1.1, 2023-11-14)
- **Available Data:** 
  - *Nodes:* None explicitly instantiated as new entities
  - *Edges:* bodyPartOverexpressesGene, bodyPartUnderexpressesGene (6.6M edges for humans)
- **Tested Download Link:** https://www.bgee.org/ftp/current/download/calls/expr_calls/Homo_sapiens_expr_simple.tsv.gz
- **Access Approach:** web-based downloads (TSV)

## 3. Disease Ontology (DO)
- **Excerpt:** The Human Disease Ontology provides a standardized ontological representation of human diseases. It unifies clinical vocabularies and links diseases to concepts like anatomy, genetics, and phenotypes to standardize disease representation across biomedical data.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** Ongoing, reviewed annually (Latest: V2024-03)
- **Available Data:** 
  - *Nodes:* Disease (12,012 nodes loaded)
  - *Edges:* diseaseLocalizesToAnatomy
- **Tested Download Link:** https://raw.githubusercontent.com/DiseaseOntology/HumanDiseaseOntology/main/src/ontology/doid.obo
- **Access Approach:** web-based downloads (OBO/OWL)

## 4. DisGeNET
- **Excerpt:** DisGeNET is a discovery platform containing one of the largest publicly available collections of genes and variants associated to human diseases. It aggregates data from expert-curated repositories, GWAS catalogs, animal models, and scientific literature.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** semi-annual (Latest: V7.0, 2020-05)
- **Available Data:** 
  - *Nodes:* Disease
  - *Edges:* geneAssociatesWithDisease
- **Tested Download Link:** https://www.disgenet.org/downloads
- **Access Approach:** Restful API

## 5. DrugBank
- **Excerpt:** DrugBank is a comprehensive, free-to-access, online database containing information on drugs and drug targets. As both a bioinformatics and a cheminformatics resource, it combines detailed drug data with comprehensive drug target information.
- **Availability:** Yes (Requires Login/Credentials (401))
- **Update Frequency:** semi-annual (Latest: V5.1.12, 2024-03-14)
- **Available Data:** 
  - *Nodes:* Drug (19,842 nodes loaded)
  - *Edges:* None generated directly by its base parser natively
- **Tested Download Link:** https://go.drugbank.com/releases/5-1-12/downloads/all-drug-links
- **Access Approach:** web-based downloads (XML/CSV)

## 6. EPA Computational Toxicology databases (DSSTox/AcTOR)
- **Excerpt:** DSSTox (Distributed Structure-Searchable Toxicity) and ACToR provide high-quality chemical structures and toxicity data linked to human health and environmental exposures. They serve as foundational data for predictive toxicology.
- **Availability:** No (Inaccessible HTTP (404))
- **Update Frequency:** N/A (Latest: N/A)
- **Available Data:** N/A (Used to augment properties in AlzKB rather than forming independent nodes/edges)
- **Tested Download Link:** https://comptox.epa.gov/dashboard/downloads
- **Access Approach:** web-based downloads

## 7. Gene Ontology (GO)
- **Excerpt:** The Gene Ontology project evaluates computational models of biological systems. It offers a structured, computable knowledge database describing the functions of genes and gene products (biological processes, molecular functions, and cellular components) across species.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** Annual check (Latest: V2024-04-24)
- **Available Data:** 
  - *Nodes:* BiologicalProcess, MolecularFunction, CellularComponent
  - *Edges:* geneParticipatesInBiologicalProcess, geneHasMolecularFunction, geneAssociatedWithCellularComponent
- **Tested Download Link:** http://current.geneontology.org/ontology/go-basic.obo
- **Access Approach:** web-based downloads / public FTP (OBO/GAF)

## 8. GWAS Catalog
- **Excerpt:** The NHGRI-EBI GWAS Catalog is a curated, freely available database of human genome-wide association studies (GWAS). It provides a consistent, searchable, and quality-controlled repository of mapped trait-associated SNPs.
- **Availability:** No (Inaccessible HTTP (404))
- **Update Frequency:** Ongoing updates (Latest: V2024-02-11)
- **Available Data:** 
  - *Nodes:* (References existing terms)
  - *Edges:* geneAssociatesWithDisease
- **Tested Download Link:** https://www.ebi.ac.uk/gwas/api/search/downloads/full
- **Access Approach:** web-based downloads (TSV)

## 9. Human Reference Protein Interactome Mapping Project (HuRI)
- **Excerpt:** HuRI is a systematic map of human protein-protein interactions generated using high-throughput yeast two-hybrid screening. It provides a massive framework for understanding cellular organization and disease.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** Tied to major releases (Latest: HI-III-19)
- **Available Data:** 
  - *Edges:* geneInteractsWithGene
- **Tested Download Link:** http://www.interactome-atlas.org/data/HuRI.tsv
- **Access Approach:** web-based downloads (Integrated via Hetionet)

## 10. hetio-dag
- **Excerpt:** An internal compilation representing gene interactions structured as a directed acyclic graph for use in the Hetionet project space.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** Annual check (via Hetionet)
- **Available Data:** 
  - *Edges:* geneInteractsWithGene
- **Tested Download Link:** https://raw.githubusercontent.com/dhimmel/ppi/master/data/ppi-hetio-ind.tsv
- **Access Approach:** web-based downloads

## 11. Incomplete Interactome
- **Excerpt:** A specialized network modeling gene and protein interactions curated to highlight missing links in standard interactomes, originally aggregated for the Hetionet resource.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** Annual check (via Hetionet)
- **Available Data:** 
  - *Edges:* geneInteractsWithGene
- **Tested Download Link:** https://raw.githubusercontent.com/dhimmel/ppi/master/data/ppi-hetio-ind.tsv
- **Access Approach:** web-based downloads

## 12. LINCS L1000
- **Excerpt:** The Library of Integrated Network-Based Cellular Signatures (LINCS) L1000 project maps how cells respond to various chemical and genetic perturbations by measuring the expression of roughly 1,000 landmark genes.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** N/A (Latest: V2020)
- **Available Data:** 
  - *Edges:* compoundUpregulatesGene, compoundDownregulatesGene, geneRegulatesGene
- **Tested Download Link:** https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE92742
- **Access Approach:** web-based downloads (TSV from Hetionet parses)

## 13. NCBI MeSH
- **Excerpt:** Medical Subject Headings (MeSH) is a comprehensive controlled vocabulary for the purpose of indexing journal articles and books in the life sciences. AlzKB isolates the "C23" tree (Pathological Conditions, Signs and Symptoms) for clinical phenotyping.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** semi-annual (Latest: V2023-12)
- **Available Data:** 
  - *Nodes:* Symptom
- **Tested Download Link:** https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2023.xml
- **Access Approach:** web-based downloads (XML)

## 14. NCBI Gene (Entrez Gene)
- **Excerpt:** Entrez Gene is NCBI's database for gene-specific information. It provides unique identifiers, sequences, map locations, and summaries for genes from organisms across the taxonomy.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** Update daily (Downloaded May 13, 2024)
- **Available Data:** 
  - *Nodes:* Gene (approx. 193,790 catalogued entries)
- **Tested Download Link:** ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz
- **Access Approach:** public FTP (TSV/GZ format)

## 15. Pathway Interaction Database (PID)
- **Excerpt:** A previously curated collection of human signaling pathways. Due to its deprecation and integration into other sources (like NDEx or AOP-DB), it is no longer used natively here.
- **Availability:** No (Inaccessible (Error: HTTPSConnectionPool(host='bionet.ncpsb.o))
- **Update Frequency:** N/A
- **Available Data:** Pathway nodes, geneInPathway
- **Tested Download Link:** https://bionet.ncpsb.org.cn/batman-tcm/static/download/PID.txt
- **Access Approach:** N/A

## 16. PharmacotherapyDB
- **Excerpt:** PharmacotherapyDB compiles indication data distinguishing diseases a drug treats from those a drug prevents or palliates. Formulated originally to provide gold-standard edges for Hetionet.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** N/A (Latest: V2016-03-15)
- **Available Data:** 
  - *Edges:* drugTreatsDisease
- **Tested Download Link:** https://raw.githubusercontent.com/dhimmel/indications/master/catalog/indications.tsv
- **Access Approach:** web-based downloads

## 17. PubChem
- **Excerpt:** The world's largest collection of freely accessible chemical information. PubChem is utilized structurally to cross-reference drug identities and augment compound properties.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** Ongoing after release
- **Available Data:** Identifier mappings
- **Tested Download Link:** ftp://ftp.ncbi.nlm.nih.gov/pubchem/Compound/CURRENT-Full/SDF/
- **Access Approach:** web-based downloads

## 18. Reactome
- **Excerpt:** Reactome is a free, open-source, curated and peer-reviewed pathway database. Although heavily cited, direct Reactome parsing is a gap in AlzKB, relying instead on indirect pathways from AOP-DB.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** N/A
- **Available Data:** Pathway, geneInPathway
- **Tested Download Link:** https://reactome.org/download/current/ReactomePathways.txt
- **Access Approach:** N/A

## 19. SIDER
- **Excerpt:** The Side Effect Resource (SIDER) contains information on marketed medicines and their recorded adverse drug reactions, extracted from public documents and package inserts.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** Low (Latest: V4.1, 2015-10-21)
- **Available Data:** 
  - *Nodes:* SideEffect
  - *Edges:* compoundCausesSideEffect (153,663 edges)
- **Tested Download Link:** http://sideeffects.embl.de/media/download/meddra_all_se.tsv.gz
- **Access Approach:** web-based downloads (TSV)

## 20. TISSUES
- **Excerpt:** An integrated text-mining resource for tissue-specific gene expression. It is heavily superseded in the AlzKB architecture by Bgee’s more quantitative rankings.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** N/A
- **Available Data:** anatomyExpressesGene
- **Tested Download Link:** https://download.jensenlab.org/human_tissue_knowledge_full.tsv
- **Access Approach:** N/A

## 21. Uberon
- **Excerpt:** Uberon is an integrated cross-species anatomy ontology representing a variety of anatomical entities. Its structural hierarchy is widely used to standardize body parts in biological databases.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** Annual check (Latest: V2024-03-22)
- **Available Data:** 
  - *Nodes:* BodyPart
- **Tested Download Link:** http://purl.obolibrary.org/obo/uberon.obo
- **Access Approach:** web-based downloads (OBO)

## 22. WikiPathways
- **Excerpt:** An open, collaborative platform dedicated to the curation of biological pathways. Not accessed directly in AlzKB.
- **Availability:** No (Inaccessible HTTP (404))
- **Update Frequency:** N/A
- **Available Data:** Pathway, geneInPathway
- **Tested Download Link:** https://wikipathways-data.wmcloud.org/current/gmt/wikipathways-20240510-gmt-Homo_sapiens.gmt
- **Access Approach:** N/A

## 23. DrugCentral
- **Excerpt:** DrugCentral provides information on active ingredients, chemical entities, pharmaceutical products, MOA, and OMOP indications. It acts as a primary source for drug-disease palliative and therapeutic relationships in AlzKB.
- **Availability:** No (Inaccessible HTTP (404))
- **Update Frequency:** semi-annual (Latest: V 2023-11-01)
- **Available Data:** 
  - *Nodes:* PharmacologicClass
  - *Edges:* drugTreatsDisease, drugPalliatesDisease, drugInClass
- **Tested Download Link:** https://unmtid-dbs.net/download/drugcentral.dump.01012025.sql.gz
- **Access Approach:** web-based downloads (SQL dump)

## 24. BindingDB
- **Excerpt:** BindingDB is a web-accessible database of measured binding affinities, focusing chiefly on the interactions of proteins considered to be drug targets with small, drug-like molecules.
- **Availability:** No (Inaccessible HTTP (404))
- **Update Frequency:** semi-annual (Latest: V 2024-05)
- **Available Data:** 
  - *Edges:* chemicalBindsGene
- **Tested Download Link:** https://www.bindingdb.org/bind/downloads/BindingDB_All_2024m11.tsv.zip
- **Access Approach:** web-based downloads (TSV in zip)

## 25. MEDLINE
- **Excerpt:** MEDLINE is the NLM's premier bibliographic database. In this context, it is used for systematic literature mining to identify co-occurrences of diseases, symptoms, and anatomy using statistical filters (e.g., Fisher exact test).
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** Annual check (Latest: V 2024-02-05)
- **Available Data:** 
  - *Edges:* symptomManifestationOfDisease, diseaseLocalizesToAnatomy, diseaseAssociatesWithDisease
- **Tested Download Link:** ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/
- **Access Approach:** web-based downloads (TSV via Hetionet master)

## 26. Evolutionary Rate Covariation (ERC)
- **Excerpt:** ERC relies on the evolutionary signatures of protein-coding genes to predict functional interactions. Strongly co-evolving genes typically participate in the same cellular pathways.
- **Availability:** No (Inaccessible (Error: HTTPSConnectionPool(host='raw.githubuser))
- **Update Frequency:** Low (Latest: V 2015)
- **Available Data:** 
  - *Edges:* geneCovariesWithGene
- **Tested Download Link:** https://raw.githubusercontent.com/dhimmel/erc/master/data/erc_mam33-entrez-gt-0.6.tsv.gz
- **Access Approach:** web-based downloads (TSV)

## 27. LabeledIn
- **Excerpt:** Extracts indications for human drugs from FDA drug labels. 
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** N/A
- **Available Data:** drugTreatsDisease
- **Tested Download Link:** https://raw.githubusercontent.com/dhimmel/indications/master/catalog/indications.tsv
- **Access Approach:** N/A

## 28. MEDI
- **Excerpt:** An ensemble Medication Indication resource derived from clinical knowledge bases.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** N/A
- **Available Data:** drugTreatsDisease
- **Tested Download Link:** https://www.vumc.org/cpm/sites/default/files/public_files/MEDI_01212013.csv
- **Access Approach:** N/A

## 29. PREDICT
- **Excerpt:** An algorithm and associated dataset predicting novel drug indications.
- **Availability:** No (Inaccessible (Error: HTTPConnectionPool(host='predict.pharmac))
- **Update Frequency:** N/A
- **Available Data:** drugTreatsDisease
- **Tested Download Link:** http://predict.pharmaceutical-bioinformatics.de/
- **Access Approach:** N/A

## 30. ehrlink
- **Excerpt:** A resource linking drugs to diseases mined from electronic health records.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** N/A
- **Available Data:** drugTreatsDisease
- **Tested Download Link:** https://github.com/dhimmel/indications
- **Access Approach:** N/A

## 31. DISEASES (Jensen Lab)
- **Excerpt:** A database that integrates evidence on disease-gene associations from automatic text mining, manually curated literature, cancer mutation data, and GWAS studies.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** N/A
- **Available Data:** diseaseAssociatesWithGene
- **Tested Download Link:** https://download.jensenlab.org/human_disease_knowledge_full.tsv
- **Access Approach:** N/A

## 32. DOAF
- **Excerpt:** Disease Ontology Annotation Framework mining gene-disease relationships.
- **Availability:** No (Inaccessible (Error: HTTPConnectionPool(host='doaf.hgc.jp', p))
- **Update Frequency:** N/A
- **Available Data:** diseaseAssociatesWithGene
- **Tested Download Link:** http://doaf.hgc.jp/
- **Access Approach:** N/A

## 33. STARGEO
- **Excerpt:** A text-mining based approach looking for transcriptomic upregulation/downregulation in diseases.
- **Availability:** No (Inaccessible (Error: HTTPConnectionPool(host='stargeo.org', p))
- **Update Frequency:** N/A
- **Available Data:** diseaseRegulatesGene
- **Tested Download Link:** http://stargeo.org/
- **Access Approach:** N/A

## 34. ClinicalTrials.gov
- **Excerpt:** A database of privately and publicly funded clinical studies conducted around the world, maintained by the NLM. In this framework, it connects medical interventions to studied conditions.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** Ongoing
- **Available Data:** 
  - *Nodes:* ClinicalTrial
  - *Edges:* STUDIES_CONDITION, TESTS_INTERVENTION
- **Tested Download Link:** https://clinicaltrials.gov/api/v2/studies
- **Access Approach:** Restful API (API v2 JSON responses)

## 35. ClinPGx
- **Excerpt:** Successor to PharmGKB models, ClinPGx provides clinical pharmacogenomics knowledge linking genetic variants with varied host responses to pharmaceutical drugs.
- **Availability:** Yes (Requires API Key/Params (400))
- **Update Frequency:** Ongoing
- **Available Data:** 
  - *Nodes:* Variant, DrugLabel
  - *Edges:* AFFECTS_RESPONSE_TO, VARIANT_IN
- **Tested Download Link:** https://api.pharmgkb.org/v1/data/clinicalAnnotations
- **Access Approach:** Restful API (JSON responses)

## 36. DoRothEA (OmniPath)
- **Excerpt:** DoRothEA acts as a comprehensive resource containing transcription factor (TF) - target gene interactions, curated and scored based on supporting evidence across multiple sources.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** As per OmniPath releases
- **Available Data:** 
  - *Nodes:* TranscriptionFactor
  - *Edges:* transcriptionFactorInteractsWithGene
- **Tested Download Link:** https://omnipathdb.org/interactions?datasets=dorothea
- **Access Approach:** web-based downloads (via OmniPath REST endpoints usually converted to TSV)

## 37. PubTator Central
- **Excerpt:** PubTator Central is a web service for viewing and retrieving bio-concept annotations in full text biomedical articles. It provides high-throughput literature-mined relationships extracted via advanced NLP.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** High
- **Available Data:** 
  - *Edges:* diseaseAssociatesWithDisease, geneAssociatesWithDisease (Approx 69M+ edges)
- **Tested Download Link:** ftp://ftp.ncbi.nlm.nih.gov/pub/lu/PubTatorCentral/disease2pubtatorcentral.gz
- **Access Approach:** web-based downloads (FTP annotations)

## 38. CTD (Comparative Toxicogenomics Database)
- **Excerpt:** CTD promotes understanding of environmental exposures and their potential impacts on human health. It curates chemical-gene/protein interactions, chemical-disease, and gene-disease relationships.
- **Availability:** Yes (Available (200 OK))
- **Update Frequency:** Monthly
- **Available Data:** 
  - *Edges:* chemicalIncreasesExpression, chemicalDecreasesExpression
- **Tested Download Link:** http://ctdbase.org/reports/CTD_chem_gene_ixns.tsv.gz
- **Access Approach:** web-based downloads (TSV formatted dumps)

## 39. OMIM
- **Excerpt:** Online Mendelian Inheritance in Man (OMIM) is a comprehensive, authoritative compendium of human genes and genetic phenotypes that is freely available and updated daily.
- **Availability:** Yes (Requires API Key/Params (400))
- **Update Frequency:** Daily
- **Available Data:** 
  - *Nodes:* Disease, Gene
  - *Edges:* geneAssociatesWithDisease
- **Tested Download Link:** https://api.omim.org/api/clinicalSynopsis?mimNumber=100100&include=clinicalSynopsis&format=json
- **Access Approach:** Restful API (Requires OMIM API Key)
