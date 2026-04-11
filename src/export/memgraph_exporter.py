"""
Memgraph-compatible CSV exporter for the KG pipeline.

Extracts typed nodes and relationships from the populated OWL ontology
and writes per-type CSV files suitable for Memgraph's LOAD CSV.

Output files:
    nodes_{NodeType}.csv   — One file per node type with id, properties, :LABEL
    edges_{RelType}.csv    — One file per relationship type with :START_ID, :END_ID, :TYPE
"""

import csv
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from rdflib import Graph, Namespace, RDF, RDFS, OWL

logger = logging.getLogger(__name__)


class MemgraphExporter:
    """
    Export a populated OWL ontology to Memgraph-compatible CSV files.

    Reads the RDF/XML file, classifies individuals by their OWL class,
    extracts data properties, and writes typed CSV files.

    Args:
        rdf_files: List of populated RDF file paths.
        output_dir: Directory to write CSV files.
    """

    def __init__(self, rdf_files: List[str], output_dir: str):
        self.rdf_files = rdf_files
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.graph = Graph()

        for rdf_file in rdf_files:
            logger.info(f"Loading RDF: {rdf_file}")
            self.graph.parse(rdf_file, format="xml")
        logger.info(f"Loaded {len(self.graph)} triples")

    def export(self) -> dict:
        """
        Export nodes and edges to typed CSV files.

        Returns:
            {"nodes_count": int, "edges_count": int, "output_files": [str]}
        """
        output_files = []
        total_nodes = 0
        total_edges = 0

        # Detect the ontology namespace from the RDF
        ontology_ns = self._detect_namespace()

        # --- Export nodes ---
        nodes_by_type = self._extract_nodes(ontology_ns)
        for node_type, nodes in nodes_by_type.items():
            filename = f"nodes_{node_type}.csv"
            filepath = self.output_dir / filename
            self._write_node_csv(filepath, nodes, node_type)
            total_nodes += len(nodes)
            output_files.append(str(filepath))
            logger.info(f"  Exported {len(nodes)} {node_type} nodes -> {filename}")

        # --- Export edges ---
        edges_by_type = self._extract_edges(ontology_ns)
        for rel_type, edges in edges_by_type.items():
            filename = f"edges_{rel_type}.csv"
            filepath = self.output_dir / filename
            self._write_edge_csv(filepath, edges, rel_type)
            total_edges += len(edges)
            output_files.append(str(filepath))
            logger.info(f"  Exported {len(edges)} {rel_type} edges -> {filename}")

        logger.info(f"Total: {total_nodes} nodes, {total_edges} edges, "
                     f"{len(output_files)} files")

        return {
            "nodes_count": total_nodes,
            "edges_count": total_edges,
            "output_files": output_files,
        }

    def _detect_namespace(self) -> Optional[Namespace]:
        """Detect the ontology namespace from the loaded graph."""
        # Look for the ontology IRI
        for s, p, o in self.graph.triples((None, RDF.type, OWL.Ontology)):
            ns = str(s)
            if not ns.endswith("#"):
                ns += "#"
            logger.info(f"Detected ontology namespace: {ns}")
            return Namespace(ns)

        # Fallback: look for the most common namespace among individuals
        ns_counts = defaultdict(int)
        for s, p, o in self.graph.triples((None, RDF.type, OWL.NamedIndividual)):
            uri = str(s)
            if "#" in uri:
                ns_counts[uri.rsplit("#", 1)[0] + "#"] += 1

        if ns_counts:
            ns = max(ns_counts, key=ns_counts.get)
            logger.info(f"Inferred ontology namespace: {ns}")
            return Namespace(ns)

        logger.warning("Could not detect ontology namespace")
        return None

    def _extract_nodes(self, ontology_ns: Optional[Namespace]) -> Dict[str, list]:
        """
        Extract nodes grouped by their OWL class type.

        Returns:
            Dict mapping class name -> list of node dicts.
        """
        nodes_by_type = defaultdict(list)

        # Find all named individuals and their types
        for individual in self.graph.subjects(RDF.type, OWL.NamedIndividual):
            ind_uri = str(individual)

            # Get the OWL class(es) for this individual
            node_types = []
            for _, _, obj in self.graph.triples((individual, RDF.type, None)):
                obj_str = str(obj)
                if obj_str == str(OWL.NamedIndividual):
                    continue
                # Extract class name from URI
                if "#" in obj_str:
                    class_name = obj_str.rsplit("#", 1)[1]
                elif "/" in obj_str:
                    class_name = obj_str.rsplit("/", 1)[1]
                else:
                    class_name = obj_str
                node_types.append(class_name)

            if not node_types:
                continue

            # Extract local name as node ID
            if "#" in ind_uri:
                node_id = ind_uri.rsplit("#", 1)[1]
            elif "/" in ind_uri:
                node_id = ind_uri.rsplit("/", 1)[1]
            else:
                node_id = ind_uri

            # Extract data properties
            properties = {"id": node_id, "uri": ind_uri}
            for pred, obj in self.graph.predicate_objects(individual):
                pred_str = str(pred)
                # Skip RDF/OWL built-in predicates
                if any(pred_str.startswith(ns) for ns in [str(RDF), str(RDFS), str(OWL)]):
                    continue
                # Only data properties (literal values)
                if hasattr(obj, "toPython"):
                    prop_name = pred_str.rsplit("#", 1)[1] if "#" in pred_str else pred_str
                    properties[prop_name] = str(obj)

            # Add to each type
            for nt in node_types:
                nodes_by_type[nt].append(properties)

        return dict(nodes_by_type)

    def _extract_edges(self, ontology_ns: Optional[Namespace]) -> Dict[str, list]:
        """
        Extract edges (object property assertions) grouped by relationship type.

        Returns:
            Dict mapping relationship name -> list of edge dicts.
        """
        edges_by_type = defaultdict(list)

        # Get all object properties defined in the ontology
        obj_properties = set()
        for prop in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            obj_properties.add(str(prop))

        # Also collect properties used in actual triples between individuals
        individual_uris = set(
            str(s) for s in self.graph.subjects(RDF.type, OWL.NamedIndividual)
        )

        for s, p, o in self.graph:
            s_str, p_str, o_str = str(s), str(p), str(o)

            # Skip built-in predicates
            if any(p_str.startswith(ns) for ns in [str(RDF), str(RDFS), str(OWL)]):
                continue

            # Only edges between individuals (object properties)
            if s_str not in individual_uris or o_str not in individual_uris:
                continue

            # Extract names
            def _local_name(uri):
                if "#" in uri:
                    return uri.rsplit("#", 1)[1]
                if "/" in uri:
                    return uri.rsplit("/", 1)[1]
                return uri

            rel_type = _local_name(p_str)
            start_id = _local_name(s_str)
            end_id = _local_name(o_str)

            edges_by_type[rel_type].append({
                "start_id": start_id,
                "end_id": end_id,
                "start_uri": s_str,
                "end_uri": o_str,
            })

        return dict(edges_by_type)

    def _write_node_csv(self, filepath: Path, nodes: list, node_type: str):
        """Write a node CSV file."""
        if not nodes:
            return

        # Collect all property keys across all nodes of this type
        all_keys = set()
        for node in nodes:
            all_keys.update(node.keys())

        # Order: id first, then sorted property names
        all_keys.discard("id")
        all_keys.discard("uri")
        columns = ["id"] + sorted(all_keys) + ["uri"]

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            for node in nodes:
                writer.writerow(node)

    def _write_edge_csv(self, filepath: Path, edges: list, rel_type: str):
        """Write an edge CSV file."""
        if not edges:
            return

        columns = ["start_id", "end_id", "start_uri", "end_uri"]

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for edge in edges:
                writer.writerow(edge)
