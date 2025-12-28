"""Test KG (Knowledge Graph) database schema creation.

This tests the 4 new KG tables and 8 indexes for KG-Microbe integration:
- kg_nodes: 1.5M nodes (biolink categories)
- kg_edges: 5.1M edges (biolink predicates)
- kg_hierarchies: Materialized transitive closure
- kg_predicate_index: Edge type statistics
"""

import duckdb
import pytest
from pathlib import Path

from microgrowagents.database.schema import create_schema, drop_schema


@pytest.fixture
def test_db(tmp_path):
    """Create test database."""
    db_path = tmp_path / "test_kg.duckdb"
    conn = duckdb.connect(str(db_path))
    yield conn
    conn.close()


class TestKGTableCreation:
    """Test that KG tables are created correctly."""

    def test_kg_nodes_table_exists(self, test_db):
        """Test that kg_nodes table is created."""
        create_schema(test_db)

        tables = test_db.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        assert "kg_nodes" in table_names, "kg_nodes table not created"

    def test_kg_edges_table_exists(self, test_db):
        """Test that kg_edges table is created."""
        create_schema(test_db)

        tables = test_db.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        assert "kg_edges" in table_names, "kg_edges table not created"

    def test_kg_hierarchies_table_exists(self, test_db):
        """Test that kg_hierarchies table is created."""
        create_schema(test_db)

        tables = test_db.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        assert "kg_hierarchies" in table_names, "kg_hierarchies table not created"

    def test_kg_predicate_index_table_exists(self, test_db):
        """Test that kg_predicate_index table is created."""
        create_schema(test_db)

        tables = test_db.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        assert "kg_predicate_index" in table_names, "kg_predicate_index table not created"

    def test_all_kg_tables_created(self, test_db):
        """Test that all 4 KG tables are created together."""
        create_schema(test_db)

        tables = test_db.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        kg_tables = ["kg_nodes", "kg_edges", "kg_hierarchies", "kg_predicate_index"]

        for table in kg_tables:
            assert table in table_names, f"KG table {table} not created"


class TestKGNodeSchema:
    """Test kg_nodes table schema and constraints."""

    def test_kg_nodes_has_required_columns(self, test_db):
        """Test that kg_nodes has all required columns."""
        create_schema(test_db)

        columns = test_db.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'kg_nodes'"
        ).fetchall()
        column_names = [c[0] for c in columns]

        required_columns = [
            "id",
            "category",
            "name",
            "description",
            "xref",
            "synonym",
            "iri",
            "provided_by",
            "deprecated",
            "subsets",
        ]

        for col in required_columns:
            assert col in column_names, f"Column {col} missing from kg_nodes"

    def test_kg_nodes_primary_key(self, test_db):
        """Test that kg_nodes has id as primary key."""
        create_schema(test_db)

        # Try inserting duplicate IDs - should fail
        test_db.execute(
            "INSERT INTO kg_nodes (id, category) VALUES ('CHEBI:16828', 'biolink:ChemicalSubstance')"
        )

        with pytest.raises(duckdb.ConstraintException):
            test_db.execute(
                "INSERT INTO kg_nodes (id, category) VALUES ('CHEBI:16828', 'biolink:ChemicalSubstance')"
            )

    def test_kg_nodes_category_not_null(self, test_db):
        """Test that category is NOT NULL."""
        create_schema(test_db)

        with pytest.raises(duckdb.ConstraintException):
            test_db.execute("INSERT INTO kg_nodes (id) VALUES ('CHEBI:16828')")

    def test_kg_nodes_deprecated_default_false(self, test_db):
        """Test that deprecated defaults to FALSE."""
        create_schema(test_db)

        test_db.execute(
            "INSERT INTO kg_nodes (id, category) VALUES ('CHEBI:16828', 'biolink:ChemicalSubstance')"
        )

        result = test_db.execute(
            "SELECT deprecated FROM kg_nodes WHERE id = 'CHEBI:16828'"
        ).fetchone()

        assert result[0] is False, "deprecated should default to FALSE"

    def test_kg_nodes_can_insert_full_row(self, test_db):
        """Test inserting a complete node row."""
        create_schema(test_db)

        test_db.execute(
            """
            INSERT INTO kg_nodes (id, category, name, description, xref, synonym, iri, provided_by, deprecated, subsets)
            VALUES (
                'CHEBI:16828',
                'biolink:ChemicalSubstance',
                'heme',
                'A complex metal ion...',
                'KEGG:C00032|PubChem:26945',
                'haem|protoheme',
                'http://purl.obolibrary.org/obo/CHEBI_16828',
                'chebi',
                FALSE,
                'subset1,subset2'
            )
            """
        )

        result = test_db.execute(
            "SELECT * FROM kg_nodes WHERE id = 'CHEBI:16828'"
        ).fetchone()

        assert result[0] == "CHEBI:16828"
        assert result[1] == "biolink:ChemicalSubstance"
        assert result[2] == "heme"


class TestKGEdgeSchema:
    """Test kg_edges table schema and constraints."""

    def test_kg_edges_has_required_columns(self, test_db):
        """Test that kg_edges has all required columns."""
        create_schema(test_db)

        columns = test_db.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'kg_edges'"
        ).fetchall()
        column_names = [c[0] for c in columns]

        required_columns = [
            "id",
            "subject",
            "predicate",
            "object",
            "relation",
            "knowledge_source",
            "primary_knowledge_source",
        ]

        for col in required_columns:
            assert col in column_names, f"Column {col} missing from kg_edges"

    def test_kg_edges_primary_key(self, test_db):
        """Test that kg_edges has id as primary key."""
        create_schema(test_db)

        test_db.execute(
            """
            INSERT INTO kg_edges (id, subject, predicate, object)
            VALUES ('edge1', 'CHEBI:16828', 'biolink:subclass_of', 'CHEBI:15841')
            """
        )

        with pytest.raises(duckdb.ConstraintException):
            test_db.execute(
                """
                INSERT INTO kg_edges (id, subject, predicate, object)
                VALUES ('edge1', 'CHEBI:16828', 'biolink:subclass_of', 'CHEBI:15841')
                """
            )

    def test_kg_edges_required_fields_not_null(self, test_db):
        """Test that subject, predicate, object are NOT NULL."""
        create_schema(test_db)

        # Missing subject
        with pytest.raises(duckdb.ConstraintException):
            test_db.execute(
                "INSERT INTO kg_edges (id, predicate, object) VALUES ('edge1', 'biolink:subclass_of', 'CHEBI:15841')"
            )

        # Missing predicate
        with pytest.raises(duckdb.ConstraintException):
            test_db.execute(
                "INSERT INTO kg_edges (id, subject, object) VALUES ('edge2', 'CHEBI:16828', 'CHEBI:15841')"
            )

        # Missing object
        with pytest.raises(duckdb.ConstraintException):
            test_db.execute(
                "INSERT INTO kg_edges (id, subject, predicate) VALUES ('edge3', 'CHEBI:16828', 'biolink:subclass_of')"
            )

    def test_kg_edges_can_insert_full_row(self, test_db):
        """Test inserting a complete edge row."""
        create_schema(test_db)

        test_db.execute(
            """
            INSERT INTO kg_edges (id, subject, predicate, object, relation, knowledge_source, primary_knowledge_source)
            VALUES (
                'edge_12345',
                'CHEBI:16828',
                'biolink:subclass_of',
                'CHEBI:15841',
                'rdfs:subClassOf',
                'infores:chebi',
                'infores:chebi'
            )
            """
        )

        result = test_db.execute(
            "SELECT * FROM kg_edges WHERE id = 'edge_12345'"
        ).fetchone()

        assert result[0] == "edge_12345"
        assert result[1] == "CHEBI:16828"
        assert result[2] == "biolink:subclass_of"
        assert result[3] == "CHEBI:15841"


class TestKGHierarchySchema:
    """Test kg_hierarchies table schema."""

    def test_kg_hierarchies_has_required_columns(self, test_db):
        """Test that kg_hierarchies has all required columns."""
        create_schema(test_db)

        columns = test_db.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'kg_hierarchies'"
        ).fetchall()
        column_names = [c[0] for c in columns]

        required_columns = ["ancestor_id", "descendant_id", "path_length", "path"]

        for col in required_columns:
            assert col in column_names, f"Column {col} missing from kg_hierarchies"

    def test_kg_hierarchies_composite_primary_key(self, test_db):
        """Test that (ancestor_id, descendant_id) is the primary key."""
        create_schema(test_db)

        test_db.execute(
            """
            INSERT INTO kg_hierarchies (ancestor_id, descendant_id, path_length, path)
            VALUES ('CHEBI:24431', 'CHEBI:16828', 2, 'CHEBI:24431|CHEBI:15841|CHEBI:16828')
            """
        )

        # Duplicate (ancestor_id, descendant_id) should fail
        with pytest.raises(duckdb.ConstraintException):
            test_db.execute(
                """
                INSERT INTO kg_hierarchies (ancestor_id, descendant_id, path_length, path)
                VALUES ('CHEBI:24431', 'CHEBI:16828', 2, 'CHEBI:24431|CHEBI:15841|CHEBI:16828')
                """
            )

    def test_kg_hierarchies_can_insert_row(self, test_db):
        """Test inserting hierarchy data."""
        create_schema(test_db)

        test_db.execute(
            """
            INSERT INTO kg_hierarchies (ancestor_id, descendant_id, path_length, path)
            VALUES ('CHEBI:24431', 'CHEBI:16828', 2, 'CHEBI:24431|CHEBI:15841|CHEBI:16828')
            """
        )

        result = test_db.execute(
            "SELECT * FROM kg_hierarchies WHERE ancestor_id = 'CHEBI:24431'"
        ).fetchone()

        assert result[0] == "CHEBI:24431"
        assert result[1] == "CHEBI:16828"
        assert result[2] == 2
        assert "CHEBI:15841" in result[3]


class TestKGPredicateIndexSchema:
    """Test kg_predicate_index table schema."""

    def test_kg_predicate_index_has_required_columns(self, test_db):
        """Test that kg_predicate_index has all required columns."""
        create_schema(test_db)

        columns = test_db.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'kg_predicate_index'"
        ).fetchall()
        column_names = [c[0] for c in columns]

        required_columns = [
            "predicate",
            "edge_count",
            "description",
            "domain_category",
            "range_category",
        ]

        for col in required_columns:
            assert col in column_names, f"Column {col} missing from kg_predicate_index"

    def test_kg_predicate_index_primary_key(self, test_db):
        """Test that predicate is the primary key."""
        create_schema(test_db)

        test_db.execute(
            """
            INSERT INTO kg_predicate_index (predicate, edge_count)
            VALUES ('biolink:subclass_of', 1574819)
            """
        )

        with pytest.raises(duckdb.ConstraintException):
            test_db.execute(
                """
                INSERT INTO kg_predicate_index (predicate, edge_count)
                VALUES ('biolink:subclass_of', 1574819)
                """
            )

    def test_kg_predicate_index_can_insert_full_row(self, test_db):
        """Test inserting predicate statistics."""
        create_schema(test_db)

        test_db.execute(
            """
            INSERT INTO kg_predicate_index (predicate, edge_count, description, domain_category, range_category)
            VALUES (
                'biolink:subclass_of',
                1574819,
                'Hierarchical subclass relationship',
                'biolink:ChemicalSubstance',
                'biolink:ChemicalSubstance'
            )
            """
        )

        result = test_db.execute(
            "SELECT * FROM kg_predicate_index WHERE predicate = 'biolink:subclass_of'"
        ).fetchone()

        assert result[0] == "biolink:subclass_of"
        assert result[1] == 1574819
        assert "Hierarchical" in result[2]


class TestKGIndexes:
    """Test that all 8 critical indexes are created for KG tables."""

    def test_all_kg_indexes_created(self, test_db):
        """Test that all 8 KG indexes exist."""
        create_schema(test_db)

        indexes = test_db.execute(
            "SELECT indexname FROM pg_catalog.pg_indexes WHERE schemaname = 'main'"
        ).fetchall()
        index_names = [i[0] for i in indexes]

        expected_kg_indexes = [
            "idx_kg_nodes_category",
            "idx_kg_nodes_name",
            "idx_kg_edges_subject",
            "idx_kg_edges_object",
            "idx_kg_edges_predicate",
            "idx_kg_edges_subj_pred",
            "idx_kg_edges_pred_obj",
            "idx_kg_hier_ancestor",
        ]

        for index in expected_kg_indexes:
            assert index in index_names, f"Index {index} not created"

    def test_kg_nodes_category_index(self, test_db):
        """Test category index on kg_nodes."""
        create_schema(test_db)

        indexes = test_db.execute(
            "SELECT indexname FROM pg_catalog.pg_indexes WHERE tablename = 'kg_nodes'"
        ).fetchall()
        index_names = [i[0] for i in indexes]

        assert "idx_kg_nodes_category" in index_names

    def test_kg_nodes_name_index(self, test_db):
        """Test name index on kg_nodes."""
        create_schema(test_db)

        indexes = test_db.execute(
            "SELECT indexname FROM pg_catalog.pg_indexes WHERE tablename = 'kg_nodes'"
        ).fetchall()
        index_names = [i[0] for i in indexes]

        assert "idx_kg_nodes_name" in index_names

    def test_kg_edges_subject_index(self, test_db):
        """Test subject index on kg_edges."""
        create_schema(test_db)

        indexes = test_db.execute(
            "SELECT indexname FROM pg_catalog.pg_indexes WHERE tablename = 'kg_edges'"
        ).fetchall()
        index_names = [i[0] for i in indexes]

        assert "idx_kg_edges_subject" in index_names

    def test_kg_edges_object_index(self, test_db):
        """Test object index on kg_edges."""
        create_schema(test_db)

        indexes = test_db.execute(
            "SELECT indexname FROM pg_catalog.pg_indexes WHERE tablename = 'kg_edges'"
        ).fetchall()
        index_names = [i[0] for i in indexes]

        assert "idx_kg_edges_object" in index_names

    def test_kg_edges_predicate_index(self, test_db):
        """Test predicate index on kg_edges."""
        create_schema(test_db)

        indexes = test_db.execute(
            "SELECT indexname FROM pg_catalog.pg_indexes WHERE tablename = 'kg_edges'"
        ).fetchall()
        index_names = [i[0] for i in indexes]

        assert "idx_kg_edges_predicate" in index_names

    def test_kg_edges_composite_subject_predicate_index(self, test_db):
        """Test composite (subject, predicate) index on kg_edges."""
        create_schema(test_db)

        indexes = test_db.execute(
            "SELECT indexname FROM pg_catalog.pg_indexes WHERE tablename = 'kg_edges'"
        ).fetchall()
        index_names = [i[0] for i in indexes]

        assert "idx_kg_edges_subj_pred" in index_names

    def test_kg_edges_composite_predicate_object_index(self, test_db):
        """Test composite (predicate, object) index on kg_edges."""
        create_schema(test_db)

        indexes = test_db.execute(
            "SELECT indexname FROM pg_catalog.pg_indexes WHERE tablename = 'kg_edges'"
        ).fetchall()
        index_names = [i[0] for i in indexes]

        assert "idx_kg_edges_pred_obj" in index_names

    def test_kg_hierarchies_ancestor_index(self, test_db):
        """Test ancestor_id index on kg_hierarchies."""
        create_schema(test_db)

        indexes = test_db.execute(
            "SELECT indexname FROM pg_catalog.pg_indexes WHERE tablename = 'kg_hierarchies'"
        ).fetchall()
        index_names = [i[0] for i in indexes]

        assert "idx_kg_hier_ancestor" in index_names


class TestKGSchemaIntegration:
    """Test integration of KG schema with existing schema."""

    def test_kg_schema_coexists_with_existing_tables(self, test_db):
        """Test that KG tables are created alongside existing tables."""
        create_schema(test_db)

        tables = test_db.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        # Existing tables should still be there
        existing_tables = ["media", "ingredients", "media_ingredients"]
        for table in existing_tables:
            assert table in table_names, f"Existing table {table} missing"

        # KG tables should be added
        kg_tables = ["kg_nodes", "kg_edges", "kg_hierarchies", "kg_predicate_index"]
        for table in kg_tables:
            assert table in table_names, f"KG table {table} missing"

    def test_drop_schema_removes_kg_tables(self, test_db):
        """Test that drop_schema removes KG tables."""
        create_schema(test_db)
        drop_schema(test_db)

        tables = test_db.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()

        assert len(tables) == 0, "All tables (including KG) should be dropped"


class TestKGDataQueries:
    """Test that we can query KG data after insertion."""

    def test_query_nodes_by_category(self, test_db):
        """Test querying nodes by category using index."""
        create_schema(test_db)

        # Insert test data
        test_db.execute(
            """
            INSERT INTO kg_nodes (id, category, name) VALUES
            ('CHEBI:16828', 'biolink:ChemicalSubstance', 'heme'),
            ('CHEBI:15377', 'biolink:ChemicalSubstance', 'water'),
            ('NCBITaxon:562', 'biolink:OrganismTaxon', 'Escherichia coli')
            """
        )

        # Query by category (should use idx_kg_nodes_category)
        result = test_db.execute(
            "SELECT COUNT(*) FROM kg_nodes WHERE category = 'biolink:ChemicalSubstance'"
        ).fetchone()

        assert result[0] == 2

    def test_query_edges_by_subject_and_predicate(self, test_db):
        """Test querying edges using composite index."""
        create_schema(test_db)

        # Insert test data
        test_db.execute(
            """
            INSERT INTO kg_edges (id, subject, predicate, object) VALUES
            ('e1', 'CHEBI:16828', 'biolink:subclass_of', 'CHEBI:15841'),
            ('e2', 'CHEBI:16828', 'biolink:subclass_of', 'CHEBI:24431'),
            ('e3', 'CHEBI:16828', 'biolink:has_role', 'CHEBI:51460')
            """
        )

        # Query by subject and predicate (should use idx_kg_edges_subj_pred)
        result = test_db.execute(
            """
            SELECT COUNT(*) FROM kg_edges
            WHERE subject = 'CHEBI:16828' AND predicate = 'biolink:subclass_of'
            """
        ).fetchone()

        assert result[0] == 2

    def test_query_edges_by_predicate_and_object(self, test_db):
        """Test reverse edge lookup using composite index."""
        create_schema(test_db)

        # Insert test data
        test_db.execute(
            """
            INSERT INTO kg_edges (id, subject, predicate, object) VALUES
            ('e1', 'CHEBI:16828', 'biolink:subclass_of', 'CHEBI:24431'),
            ('e2', 'CHEBI:15841', 'biolink:subclass_of', 'CHEBI:24431'),
            ('e3', 'CHEBI:51460', 'biolink:subclass_of', 'CHEBI:24431')
            """
        )

        # Query by predicate and object (should use idx_kg_edges_pred_obj)
        # This is the "reverse lookup" - find all subjects with this object
        result = test_db.execute(
            """
            SELECT COUNT(*) FROM kg_edges
            WHERE predicate = 'biolink:subclass_of' AND object = 'CHEBI:24431'
            """
        ).fetchone()

        assert result[0] == 3

    def test_query_hierarchies(self, test_db):
        """Test querying transitive hierarchies."""
        create_schema(test_db)

        # Insert test hierarchy data
        test_db.execute(
            """
            INSERT INTO kg_hierarchies (ancestor_id, descendant_id, path_length, path) VALUES
            ('CHEBI:24431', 'CHEBI:16828', 2, 'CHEBI:24431|CHEBI:15841|CHEBI:16828'),
            ('CHEBI:24431', 'CHEBI:15841', 1, 'CHEBI:24431|CHEBI:15841'),
            ('CHEBI:50860', 'CHEBI:16828', 3, 'CHEBI:50860|CHEBI:24431|CHEBI:15841|CHEBI:16828')
            """
        )

        # Find all ancestors of CHEBI:16828
        result = test_db.execute(
            """
            SELECT ancestor_id, path_length FROM kg_hierarchies
            WHERE descendant_id = 'CHEBI:16828'
            ORDER BY path_length
            """
        ).fetchall()

        assert len(result) == 2
        assert result[0][0] == "CHEBI:24431"
        assert result[0][1] == 2
