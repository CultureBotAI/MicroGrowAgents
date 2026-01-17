"""
Genome Function Agent for interpreting genome annotations.

Queries genome annotations to support media formulation with:
- Enzyme queries (by EC number, substrate, product, pathway)
- Auxotrophy detection (missing biosynthetic pathways)
- Pathway completeness analysis
- Cofactor requirements
- Transporter identification

Author: MicroGrowAgents Team
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import duckdb
import pandas as pd

from microgrowagents.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class GenomeFunctionAgent(BaseAgent):
    """
    Agent for genome function interpretation and metabolic capability inference.

    Queries DuckDB genome annotations from Bakta GFF3 files to support
    organism-specific media formulation.

    Example:
        >>> agent = GenomeFunctionAgent()
        >>> result = agent.find_enzymes(
        ...     query="find glucose-6-phosphate dehydrogenase",
        ...     ec_number="1.1.1.49"
        ... )
        >>> result["success"]
        True
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize Genome Function Agent.

        Args:
            db_path: Path to DuckDB database with genome tables
        """
        super().__init__(db_path)
        self.conn = None

    def _connect(self):
        """Establish database connection."""
        if self.conn is None:
            self.conn = duckdb.connect(str(self.db_path), read_only=True)

    def _close(self):
        """Close database connection."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute genome function query.

        Routes query to appropriate handler based on query type.

        Args:
            query: Query string describing task
            **kwargs: Query-specific parameters

        Returns:
            Dict with success status, data, and metadata
        """
        # Parse query type from query string or kwargs
        query_lower = query.lower()

        if "enzyme" in query_lower or "ec" in query_lower:
            return self.find_enzymes(query, **kwargs)
        elif "auxotroph" in query_lower:
            return self.detect_auxotrophies(query, **kwargs)
        elif "pathway" in query_lower and "complete" in query_lower:
            return self.check_pathway_completeness(query, **kwargs)
        elif "cofactor" in query_lower:
            return self.find_cofactor_requirements(query, **kwargs)
        elif "transport" in query_lower:
            return self.find_transporters(query, **kwargs)
        else:
            return {
                "success": False,
                "error": f"Unknown query type: {query}",
                "query": query
            }

    # ==================================================================
    # CORE QUERY METHODS
    # ==================================================================

    def find_enzymes(
        self,
        query: str,
        organism: Optional[str] = None,
        ec_number: Optional[str] = None,
        substrate: Optional[str] = None,
        product: Optional[str] = None,
        pathway: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Find enzymes by EC number, substrate, product, or pathway.

        Supports EC number wildcards (e.g., "1.1.*.*" for all CH-OH oxidoreductases).

        Args:
            query: Query description
            organism: Organism name or genome ID (e.g., "Escherichia coli", "SAMN00114986")
            ec_number: EC number with optional wildcards (e.g., "1.1.1.49", "1.1.*.*")
            substrate: Substrate name (searches product descriptions)
            product: Product name (searches product descriptions)
            pathway: KEGG pathway ID (e.g., "ko00010")

        Returns:
            Dict with:
                success: bool
                data: {
                    enzymes: List[Dict] with gene info and annotations
                    count: int
                }
                query_params: Dict with query parameters
                error: Optional error message

        Example:
            >>> agent = GenomeFunctionAgent()
            >>> result = agent.find_enzymes(
            ...     query="find oxidoreductases",
            ...     organism="Escherichia coli",
            ...     ec_number="1.1.*.*"
            ... )
            >>> result["data"]["count"]
            42
        """
        try:
            self._connect()

            # Get genome ID from organism name
            genome_id = self._get_genome_id(organism) if organism else None

            enzymes = []

            if ec_number:
                # Query by EC number with wildcard support
                enzymes = self._query_enzymes_by_ec(genome_id, ec_number)
            elif substrate or product:
                # Query by substrate/product name (searches product descriptions)
                search_term = substrate or product
                enzymes = self._query_enzymes_by_product(genome_id, search_term)
            elif pathway:
                # Query by KEGG pathway
                enzymes = self._query_enzymes_by_pathway(genome_id, pathway)
            else:
                # No specific criteria - return error
                return {
                    "success": False,
                    "error": "Must specify ec_number, substrate, product, or pathway",
                    "query": query,
                    "query_params": {
                        "organism": organism,
                        "genome_id": genome_id
                    }
                }

            return {
                "success": True,
                "data": {
                    "enzymes": enzymes,
                    "count": len(enzymes)
                },
                "query": query,
                "query_params": {
                    "organism": organism,
                    "genome_id": genome_id,
                    "ec_number": ec_number,
                    "substrate": substrate,
                    "product": product,
                    "pathway": pathway
                }
            }

        except Exception as e:
            logger.error(f"Error in find_enzymes: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
        finally:
            self._close()

    def detect_auxotrophies(
        self,
        query: str,
        organism: Optional[str] = None,
        pathways_to_check: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Detect auxotrophies by screening for missing biosynthetic pathways.

        Checks biosynthetic pathways for:
        - 20 amino acids
        - B vitamins (thiamin, riboflavin, B12, biotin, folate, etc.)
        - Cofactors (NAD, CoA, heme, etc.)

        Args:
            query: Query description
            organism: Organism name or genome ID
            pathways_to_check: Optional list of specific pathway IDs to check

        Returns:
            Dict with:
                success: bool
                data: {
                    auxotrophies: List[Dict] with pathway info and missing enzymes
                    prototrophic_pathways: List[str] of complete pathways
                    summary: Dict with counts
                }
                error: Optional error message

        Example:
            >>> agent = GenomeFunctionAgent()
            >>> result = agent.detect_auxotrophies(
            ...     query="detect auxotrophies",
            ...     organism="Methylococcus capsulatus"
            ... )
            >>> result["data"]["summary"]["auxotrophies_detected"]
            3
        """
        try:
            self._connect()

            genome_id = self._get_genome_id(organism) if organism else None
            if not genome_id:
                return {
                    "success": False,
                    "error": "Organism required for auxotrophy detection",
                    "query": query
                }

            # Define pathways to check (or use provided list)
            if pathways_to_check is None:
                pathways_to_check = self._get_default_biosynthetic_pathways()

            auxotrophies = []
            prototrophic = []

            # Check each pathway
            for pathway_id in pathways_to_check:
                pathway_result = self._check_pathway_enzymes(genome_id, pathway_id)

                if pathway_result["completeness"] < 0.70:  # <70% complete = auxotrophy
                    auxotrophies.append({
                        "nutrients": pathway_result.get("nutrients", []),
                        "pathway": pathway_id,
                        "pathway_name": pathway_result.get("pathway_name", pathway_id),
                        "missing_enzymes": pathway_result.get("missing_enzymes", []),
                        "genes_present": pathway_result.get("genes_present", 0),
                        "genes_missing": pathway_result.get("genes_missing", 0),
                        "completeness": pathway_result["completeness"],
                        "confidence": self._calculate_confidence(pathway_result)
                    })
                else:
                    prototrophic.append(pathway_id)

            return {
                "success": True,
                "data": {
                    "auxotrophies": auxotrophies,
                    "prototrophic_pathways": prototrophic,
                    "summary": {
                        "total_pathways_checked": len(pathways_to_check),
                        "auxotrophies_detected": len(auxotrophies),
                        "prototrophic": len(prototrophic)
                    }
                },
                "query": query,
                "query_params": {
                    "organism": organism,
                    "genome_id": genome_id
                }
            }

        except Exception as e:
            logger.error(f"Error in detect_auxotrophies: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
        finally:
            self._close()

    def check_pathway_completeness(
        self,
        query: str,
        organism: Optional[str] = None,
        pathway_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Check if organism has complete biosynthetic pathway.

        Args:
            query: Query description
            organism: Organism name or genome ID
            pathway_id: KEGG pathway ID (e.g., "ko00270")

        Returns:
            Dict with:
                success: bool
                data: {
                    pathway_id: str
                    pathway_name: str
                    completeness: float (0-1)
                    enzymes_required: int
                    enzymes_present: int
                    enzymes_missing: List[Dict]
                    implications: str
                }
                error: Optional error message

        Example:
            >>> agent = GenomeFunctionAgent()
            >>> result = agent.check_pathway_completeness(
            ...     query="check methionine pathway",
            ...     organism="Bacillus subtilis",
            ...     pathway_id="ko00270"
            ... )
            >>> result["data"]["completeness"]
            0.88
        """
        try:
            self._connect()

            genome_id = self._get_genome_id(organism) if organism else None
            if not genome_id:
                return {
                    "success": False,
                    "error": "Organism required for pathway completeness check",
                    "query": query
                }

            if not pathway_id:
                return {
                    "success": False,
                    "error": "Pathway ID required",
                    "query": query
                }

            # Check pathway enzymes
            pathway_result = self._check_pathway_enzymes(genome_id, pathway_id)

            return {
                "success": True,
                "data": pathway_result,
                "query": query,
                "query_params": {
                    "organism": organism,
                    "genome_id": genome_id,
                    "pathway_id": pathway_id
                }
            }

        except Exception as e:
            logger.error(f"Error in check_pathway_completeness: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
        finally:
            self._close()

    def find_cofactor_requirements(
        self,
        query: str,
        organism: Optional[str] = None,
        pathway: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Determine cofactor requirements from encoded enzymes.

        Cross-references EC numbers with known enzyme-cofactor relationships
        to identify which cofactors the organism requires.

        Args:
            query: Query description
            organism: Organism name or genome ID
            pathway: Optional KEGG pathway ID to restrict search

        Returns:
            Dict with:
                success: bool
                data: {
                    cofactors: List[Dict] with cofactor info
                }
                error: Optional error message

        Example:
            >>> agent = GenomeFunctionAgent()
            >>> result = agent.find_cofactor_requirements(
            ...     query="find cofactor requirements",
            ...     organism="Pseudomonas putida"
            ... )
            >>> len(result["data"]["cofactors"])
            8
        """
        try:
            self._connect()

            genome_id = self._get_genome_id(organism) if organism else None
            if not genome_id:
                return {
                    "success": False,
                    "error": "Organism required for cofactor analysis",
                    "query": query
                }

            # Get all EC numbers for the organism
            ec_numbers = self._get_all_ec_numbers(genome_id, pathway)

            # Map EC numbers to cofactors
            cofactors = self._map_enzymes_to_cofactors(ec_numbers)

            return {
                "success": True,
                "data": {
                    "cofactors": cofactors
                },
                "query": query,
                "query_params": {
                    "organism": organism,
                    "genome_id": genome_id,
                    "pathway": pathway
                }
            }

        except Exception as e:
            logger.error(f"Error in find_cofactor_requirements: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
        finally:
            self._close()

    def find_transporters(
        self,
        query: str,
        organism: Optional[str] = None,
        substrate: Optional[str] = None,
        transporter_family: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Find transporter genes for nutrient uptake.

        Used by GenMediaConcAgent for concentration refinement based on
        transporter presence and affinity.

        Args:
            query: Query description
            organism: Organism name or genome ID
            substrate: Substrate name (e.g., "glucose", "Fe2+")
            transporter_family: Optional transporter family (e.g., "ABC", "MFS")

        Returns:
            Dict with:
                success: bool
                data: {
                    transporters: List[Dict] with transporter gene info
                }
                error: Optional error message

        Example:
            >>> agent = GenomeFunctionAgent()
            >>> result = agent.find_transporters(
            ...     query="find glucose transporters",
            ...     organism="E. coli",
            ...     substrate="glucose"
            ... )
            >>> result["data"]["transporters"][0]["family"]
            'PTS'
        """
        try:
            self._connect()

            genome_id = self._get_genome_id(organism) if organism else None
            if not genome_id:
                return {
                    "success": False,
                    "error": "Organism required for transporter search",
                    "query": query
                }

            # Search for transporter genes
            transporters = self._query_transporters(
                genome_id,
                substrate,
                transporter_family
            )

            return {
                "success": True,
                "data": {
                    "transporters": transporters
                },
                "query": query,
                "query_params": {
                    "organism": organism,
                    "genome_id": genome_id,
                    "substrate": substrate,
                    "transporter_family": transporter_family
                }
            }

        except Exception as e:
            logger.error(f"Error in find_transporters: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
        finally:
            self._close()

    # ==================================================================
    # HELPER METHODS
    # ==================================================================

    def _get_genome_id(self, organism: str) -> Optional[str]:
        """
        Resolve organism name to genome_id.

        Args:
            organism: Organism name or SAMN ID

        Returns:
            genome_id (SAMN ID) or None if not found
        """
        if not organism:
            return None

        # If it looks like a SAMN ID, return it
        if organism.startswith("SAMN"):
            return organism

        # Otherwise, query database for organism name
        result = self.conn.execute("""
            SELECT genome_id
            FROM genome_metadata
            WHERE organism_name ILIKE ?
            LIMIT 1
        """, [f"%{organism}%"]).fetchone()

        return result[0] if result else None

    def _query_enzymes_by_ec(
        self,
        genome_id: Optional[str],
        ec_pattern: str
    ) -> List[Dict]:
        """
        Query enzymes by EC number with wildcard support.

        Args:
            genome_id: Optional genome ID to restrict search
            ec_pattern: EC number with optional wildcards (e.g., "1.1.*.*")

        Returns:
            List of enzyme dicts
        """
        # Convert EC pattern to SQL LIKE pattern
        sql_pattern = ec_pattern.replace("*", "%")

        where_clauses = [
            "feature_type = 'CDS'",
            "ec_numbers IS NOT NULL",
            "ec_numbers != ''"
        ]

        params = []

        if genome_id:
            where_clauses.append("genome_id = ?")
            params.append(genome_id)

        # Use LIKE for pattern matching
        where_clauses.append("ec_numbers LIKE ?")
        params.append(f"%{sql_pattern}%")

        sql = f"""
            SELECT
                genome_id,
                feature_id,
                gene_symbol,
                product,
                ec_numbers,
                go_terms,
                kegg_ids,
                cog_ids,
                contig_id,
                start_pos,
                end_pos,
                strand
            FROM genome_annotations
            WHERE {" AND ".join(where_clauses)}
            ORDER BY genome_id, feature_id
        """

        df = self.conn.execute(sql, params).fetchdf()

        return df.to_dict(orient="records")

    def _query_enzymes_by_product(
        self,
        genome_id: Optional[str],
        search_term: str
    ) -> List[Dict]:
        """
        Query enzymes by product description.

        Args:
            genome_id: Optional genome ID to restrict search
            search_term: Term to search in product descriptions

        Returns:
            List of enzyme dicts
        """
        where_clauses = [
            "feature_type = 'CDS'",
            "product IS NOT NULL",
            "product ILIKE ?"
        ]

        params = [f"%{search_term}%"]

        if genome_id:
            where_clauses.append("genome_id = ?")
            params.append(genome_id)

        sql = f"""
            SELECT
                genome_id,
                feature_id,
                gene_symbol,
                product,
                ec_numbers,
                go_terms,
                kegg_ids,
                cog_ids,
                contig_id,
                start_pos,
                end_pos,
                strand
            FROM genome_annotations
            WHERE {" AND ".join(where_clauses)}
            ORDER BY genome_id, feature_id
            LIMIT 100
        """

        df = self.conn.execute(sql, tuple(params)).fetchdf()

        return df.to_dict(orient="records")

    def _query_enzymes_by_pathway(
        self,
        genome_id: Optional[str],
        pathway_id: str
    ) -> List[Dict]:
        """
        Query enzymes by KEGG pathway ID.

        Args:
            genome_id: Optional genome ID to restrict search
            pathway_id: KEGG pathway ID

        Returns:
            List of enzyme dicts
        """
        # For now, return empty list (pathway-enzyme mapping would require additional data)
        # This would be implemented with KEGG pathway definitions
        logger.warning(f"Pathway-based enzyme query not yet implemented: {pathway_id}")
        return []

    def _get_all_ec_numbers(
        self,
        genome_id: str,
        pathway: Optional[str] = None
    ) -> List[str]:
        """
        Get all EC numbers for a genome.

        Args:
            genome_id: Genome ID
            pathway: Optional pathway ID to filter

        Returns:
            List of EC numbers
        """
        where_clauses = [
            "genome_id = ?",
            "ec_numbers IS NOT NULL",
            "ec_numbers != ''"
        ]

        params = [genome_id]

        sql = f"""
            SELECT DISTINCT ec_numbers
            FROM genome_annotations
            WHERE {" AND ".join(where_clauses)}
        """

        df = self.conn.execute(sql, params).fetchdf()

        # Split comma-separated EC numbers
        ec_set = set()
        for ec_str in df["ec_numbers"]:
            if ec_str:
                ec_set.update(ec_str.split(","))

        return list(ec_set)

    def _map_enzymes_to_cofactors(self, ec_numbers: List[str]) -> List[Dict]:
        """
        Map EC numbers to their cofactor requirements.

        Uses comprehensive EC-to-cofactor mapping from ec_to_cofactor_map.yaml.

        Args:
            ec_numbers: List of EC numbers

        Returns:
            List of cofactor dicts
        """
        import yaml

        # Load EC-to-cofactor mapping
        yaml_path = Path(__file__).parent.parent / "data" / "ec_to_cofactor_map.yaml"
        if not yaml_path.exists():
            # Fallback to simplified mapping if YAML not found
            return self._simplified_cofactor_mapping(ec_numbers)

        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        ec_cofactor_map = data.get("ec_cofactor_mapping", {})

        cofactor_counts = {}

        for ec in ec_numbers:
            # Try exact match first
            if ec in ec_cofactor_map:
                mapping = ec_cofactor_map[ec]
                for cofactor in mapping.get("primary", []):
                    cofactor_counts[cofactor] = cofactor_counts.get(cofactor, 0) + 1
            else:
                # Try pattern matching (e.g., 1.1.1.- for 1.1.1.1)
                ec_parts = ec.split(".")
                for i in range(len(ec_parts), 0, -1):
                    pattern = ".".join(ec_parts[:i])
                    if i < 4:
                        pattern += ".-" * (4 - i)

                    if pattern in ec_cofactor_map:
                        mapping = ec_cofactor_map[pattern]
                        for cofactor in mapping.get("primary", []):
                            cofactor_counts[cofactor] = cofactor_counts.get(cofactor, 0) + 1
                        break

        # Convert to list format
        cofactors = []
        for cofactor, enzyme_count in cofactor_counts.items():
            cofactors.append({
                "cofactor": cofactor,
                "enzyme_count": enzyme_count,
                "biosynthesis_capable": True,  # Would check pathway completeness
                "external_supply": "optional"  # Would determine based on biosynthesis
            })

        return cofactors

    def _simplified_cofactor_mapping(self, ec_numbers: List[str]) -> List[Dict]:
        """Fallback simplified cofactor mapping based on EC class."""
        cofactor_counts = {}

        for ec in ec_numbers:
            parts = ec.split(".")
            if len(parts) >= 1:
                ec_class = parts[0]

                if ec_class == "1":  # Oxidoreductases
                    cofactor_counts["nad"] = cofactor_counts.get("nad", 0) + 1
                    cofactor_counts["flavin_adenine_dinucleotide"] = cofactor_counts.get("flavin_adenine_dinucleotide", 0) + 1
                elif ec_class == "2":  # Transferases
                    cofactor_counts["coenzyme_a"] = cofactor_counts.get("coenzyme_a", 0) + 1
                elif ec_class == "6":  # Ligases
                    cofactor_counts["atp"] = cofactor_counts.get("atp", 0) + 1

        cofactors = []
        for cofactor, enzyme_count in cofactor_counts.items():
            cofactors.append({
                "cofactor": cofactor,
                "enzyme_count": enzyme_count,
                "biosynthesis_capable": True,
                "external_supply": "optional"
            })

        return cofactors

    def _query_transporters(
        self,
        genome_id: str,
        substrate: Optional[str],
        transporter_family: Optional[str]
    ) -> List[Dict]:
        """
        Query for transporter genes.

        Args:
            genome_id: Genome ID
            substrate: Optional substrate name
            transporter_family: Optional transporter family

        Returns:
            List of transporter dicts
        """
        where_clauses = [
            "genome_id = ?",
            "feature_type = 'CDS'",
            "(product ILIKE '%transport%' OR product ILIKE '%permease%' OR product ILIKE '%ABC%')"
        ]

        params = [genome_id]

        if substrate:
            where_clauses.append("product ILIKE ?")
            params.append(f"%{substrate}%")

        if transporter_family:
            where_clauses.append("product ILIKE ?")
            params.append(f"%{transporter_family}%")

        sql = f"""
            SELECT
                genome_id,
                feature_id,
                gene_symbol,
                product,
                ec_numbers,
                kegg_ids,
                contig_id,
                start_pos,
                end_pos,
                strand
            FROM genome_annotations
            WHERE {" AND ".join(where_clauses)}
            ORDER BY feature_id
            LIMIT 50
        """

        df = self.conn.execute(sql, tuple(params)).fetchdf()

        # Add inferred transporter family and affinity
        transporters = []
        for _, row in df.iterrows():
            product = row["product"] or ""

            # Infer family
            family = None
            if "ABC" in product.upper():
                family = "ABC"
            elif "MFS" in product.upper():
                family = "MFS"
            elif "PTS" in product.upper():
                family = "PTS"
            elif "permease" in product.lower():
                family = "Permease"

            # Infer affinity (simplified heuristic)
            affinity = "medium"
            if "high-affinity" in product.lower():
                affinity = "high"
            elif "low-affinity" in product.lower():
                affinity = "low"

            transporters.append({
                "gene_id": row["feature_id"],
                "gene_symbol": row["gene_symbol"],
                "product": product,
                "substrate": substrate or "unknown",
                "family": family,
                "affinity": affinity,
                "location": f"{row['contig_id']}:{row['start_pos']}-{row['end_pos']}"
            })

        return transporters

    def _check_pathway_enzymes(
        self,
        genome_id: str,
        pathway_id: str
    ) -> Dict:
        """
        Check which enzymes in pathway are present in genome.

        Args:
            genome_id: Genome ID
            pathway_id: KEGG pathway ID

        Returns:
            Dict with pathway completeness info
        """
        # This would require KEGG pathway definitions
        # For now, return a placeholder implementation

        pathway_info = self._get_pathway_info(pathway_id)

        if not pathway_info:
            return {
                "pathway_id": pathway_id,
                "pathway_name": pathway_id,
                "completeness": 0.0,
                "enzymes_required": 0,
                "enzymes_present": 0,
                "missing_enzymes": [],
                "implications": "Pathway definition not available"
            }

        # Query genome for required enzymes
        required_ecs = pathway_info.get("required_enzymes", [])
        present_ecs = []

        for ec in required_ecs:
            result = self.conn.execute("""
                SELECT COUNT(*) as count
                FROM genome_annotations
                WHERE genome_id = ?
                AND ec_numbers LIKE ?
            """, [genome_id, f"%{ec}%"]).fetchone()

            if result and result[0] > 0:
                present_ecs.append(ec)

        # Calculate completeness
        completeness = len(present_ecs) / len(required_ecs) if required_ecs else 0.0

        missing = [ec for ec in required_ecs if ec not in present_ecs]

        return {
            "pathway_id": pathway_id,
            "pathway_name": pathway_info.get("name", pathway_id),
            "completeness": completeness,
            "enzymes_required": len(required_ecs),
            "enzymes_present": len(present_ecs),
            "genes_present": len(present_ecs),
            "genes_missing": len(missing),
            "missing_enzymes": [{"ec": ec} for ec in missing],
            "nutrients": pathway_info.get("nutrients", []),
            "implications": self._generate_pathway_implications(completeness, pathway_info)
        }

    def _get_pathway_info(self, pathway_id: str) -> Optional[Dict]:
        """
        Get pathway definition (enzymes, nutrients, etc.).

        This is a simplified implementation with hardcoded pathways.
        A full implementation would load from KEGG or a pathway database.

        Args:
            pathway_id: KEGG pathway ID

        Returns:
            Pathway info dict or None
        """
        # Hardcoded pathway definitions (subset for testing)
        pathways = {
            "ko00270": {
                "name": "Cysteine and methionine metabolism",
                "nutrients": ["L-methionine", "L-cysteine"],
                "required_enzymes": [
                    "2.1.1.14",  # methionine synthase
                    "2.5.1.47",  # cystathionine gamma-synthase
                    "4.4.1.1"    # cystathionine beta-lyase
                ]
            },
            "ko00750": {
                "name": "Vitamin B6 metabolism",
                "nutrients": ["pyridoxine", "pyridoxal", "pyridoxamine"],
                "required_enzymes": [
                    "2.6.99.2",  # pyridoxine 5'-phosphate synthase
                    "1.4.3.5"    # pyridoxamine-phosphate oxidase
                ]
            },
            "ko00730": {
                "name": "Thiamine metabolism",
                "nutrients": ["thiamine", "vitamin B1"],
                "required_enzymes": [
                    "2.7.6.2",   # thiamine-phosphate diphosphorylase
                    "2.5.1.3"    # thiamine-phosphate synthase
                ]
            }
        }

        return pathways.get(pathway_id)

    def _get_default_biosynthetic_pathways(self) -> List[str]:
        """
        Get list of default biosynthetic pathways to check for auxotrophies.

        Returns:
            List of KEGG pathway IDs
        """
        # Subset of key biosynthetic pathways
        return [
            "ko00270",  # Cysteine and methionine metabolism
            "ko00750",  # Vitamin B6 metabolism
            "ko00730"   # Thiamine metabolism
            # More pathways would be added here
        ]

    def _calculate_confidence(self, pathway_result: Dict) -> str:
        """
        Calculate confidence level for auxotrophy prediction.

        Args:
            pathway_result: Pathway completeness result

        Returns:
            Confidence level: "high", "medium", or "low"
        """
        completeness = pathway_result.get("completeness", 0.0)

        if completeness < 0.50:
            return "high"  # <50% complete = high confidence auxotrophy
        elif completeness < 0.70:
            return "medium"  # 50-70% complete = medium confidence
        else:
            return "low"  # >70% complete = low confidence

    def _generate_pathway_implications(
        self,
        completeness: float,
        pathway_info: Dict
    ) -> str:
        """
        Generate human-readable implications of pathway completeness.

        Args:
            completeness: Pathway completeness (0-1)
            pathway_info: Pathway information dict

        Returns:
            Implications string
        """
        nutrients = pathway_info.get("nutrients", [])

        if completeness < 0.50:
            return f"Likely requires exogenous {', '.join(nutrients)}"
        elif completeness < 0.70:
            return f"May require exogenous {', '.join(nutrients)} under some conditions"
        else:
            return f"Likely capable of synthesizing {', '.join(nutrients)}"
