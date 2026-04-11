---
name: ontology-protocol
description: Use this when defining disease scope and maintaining the OWL ontology
---

<overview>
You own `config/databases.yaml` and work with the reference OWL ontology file `data/ontology/alzkb_v2.rdf`.

You are responsible for:
- Defining the disease scope
- Ensuring the 100% compliance with the reference OWL ontology.
- Mainting (updating, fixing, removing) ontology entities and properties per user request.
</overview>


<example>

## Example disease scope fields
- `primary_terms`: lowercase search strings used by API-based parsers (DisGeNET).
- `umls_cuis`, `doid_ids`, `mesh_ids`: cross-references used by parsers that filter
  by disease identifier.
- `drug_names`: known drugs for this disease, used by DrugBank post-filtering.

</example>

<ensure-compliance>
(STRICT) only modify the reference OWL ontology file upon user's request.
- Check against the reference OWL ontology file for valid classes and properties.
- Only modify `project.yaml`; never edit Python parser source.
</ensure-compliance>
