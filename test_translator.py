"""
Automated tests for CASE to IEEE SCD Translator.

Run with: pytest test_translator.py -v
"""
import pytest
from fastapi.testclient import TestClient
from main import app, translate_case_to_ieee, CASEInput, CFDocument, CFItem, CFAssociation

client = TestClient(app)


# Test fixtures
@pytest.fixture
def minimal_case():
    """Minimal valid CASE document."""
    return {
        "CFDocument": {
            "identifier": "framework-001",
            "title": "Test Framework"
        },
        "CFItems": [],
        "CFAssociations": []
    }


@pytest.fixture
def full_case():
    """CASE document with all fields populated."""
    return {
        "CFDocument": {
            "identifier": "framework-001",
            "uri": "http://example.org/frameworks/framework-001",
            "title": "Test Framework",
            "description": "A test framework",
            "language": "en-US",
            "version": "1.0.0",
            "lastChangeDateTime": "2024-01-01T00:00:00Z",
            "publisher": {"name": "Test Publisher"},
            "officialSourceURL": "http://example.org/frameworks/framework-001"
        },
        "CFItems": [
            {
                "identifier": "item-001",
                "uri": "http://example.org/items/item-001",
                "fullStatement": "Test competency",
                "abbreviatedStatement": "Test",
                "CFItemType": "Competency",
                "hierarchyCode": "1.1",
                "conceptKeywords": ["test", "competency"],
                "language": "en-US"
            },
            {
                "identifier": "item-002",
                "fullStatement": "Another competency",
                "CFItemType": "Competency"
            }
        ],
        "CFAssociations": [
            {
                "identifier": "assoc-001",
                "associationType": "isChildOf",
                "originNodeURI": {
                    "identifier": "item-002",
                    "uri": "http://example.org/items/item-002"
                },
                "destinationNodeURI": {
                    "identifier": "item-001",
                    "uri": "http://example.org/items/item-001"
                },
                "sequenceNumber": 1,
                "lastChangeDateTime": "2024-01-01T00:00:00Z"
            },
            {
                "identifier": "assoc-002",
                "associationType": "precedes",
                "originNodeURI": {"identifier": "item-001"},
                "destinationNodeURI": {"identifier": "item-002"}
            }
        ]
    }


@pytest.fixture
def case_with_missing_items():
    """CASE document with associations referencing non-existent items."""
    return {
        "CFDocument": {
            "identifier": "framework-001",
            "title": "Test Framework"
        },
        "CFItems": [
            {
                "identifier": "item-001",
                "fullStatement": "Only item"
            }
        ],
        "CFAssociations": [
            {
                "identifier": "assoc-001",
                "associationType": "isChildOf",
                "originNodeURI": {"identifier": "item-001"},
                "destinationNodeURI": {"identifier": "item-999"}  # Doesn't exist
            }
        ]
    }


@pytest.fixture
def case_with_cyclic_associations():
    """CASE document with circular references."""
    return {
        "CFDocument": {
            "identifier": "framework-001",
            "title": "Test Framework"
        },
        "CFItems": [
            {"identifier": "item-a", "fullStatement": "Item A"},
            {"identifier": "item-b", "fullStatement": "Item B"}
        ],
        "CFAssociations": [
            {
                "identifier": "assoc-001",
                "associationType": "precedes",
                "originNodeURI": {"identifier": "item-a"},
                "destinationNodeURI": {"identifier": "item-b"}
            },
            {
                "identifier": "assoc-002",
                "associationType": "precedes",
                "originNodeURI": {"identifier": "item-b"},
                "destinationNodeURI": {"identifier": "item-a"}  # Cycle
            }
        ]
    }


@pytest.fixture
def case_with_unknown_association_type():
    """CASE document with unmapped association type."""
    return {
        "CFDocument": {
            "identifier": "framework-001",
            "title": "Test Framework"
        },
        "CFItems": [
            {"identifier": "item-001", "fullStatement": "Item 1"},
            {"identifier": "item-002", "fullStatement": "Item 2"}
        ],
        "CFAssociations": [
            {
                "identifier": "assoc-001",
                "associationType": "customType",  # Not in mapping
                "originNodeURI": {"identifier": "item-001"},
                "destinationNodeURI": {"identifier": "item-002"}
            }
        ]
    }


# ============================================================================
# API Endpoint Tests
# ============================================================================

def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


def test_basic_translation(minimal_case):
    """Test basic translation with minimal valid input."""
    response = client.post("/translate/case-to-ieee", json=minimal_case)
    assert response.status_code == 200
    
    data = response.json()
    assert "@context" in data
    assert "@graph" in data
    assert isinstance(data["@graph"], list)
    assert len(data["@graph"]) == 1  # Just the framework


def test_full_case_translation(full_case):
    """Test translation with all fields populated."""
    response = client.post("/translate/case-to-ieee", json=full_case)
    assert response.status_code == 200
    
    data = response.json()
    graph = data["@graph"]
    
    # Should have: 1 framework + 2 items + 2 associations = 5 items
    assert len(graph) == 5
    
    # Find framework
    frameworks = [item for item in graph if item.get("@type") == "scd:CompetencyFramework"]
    assert len(frameworks) == 1
    framework = frameworks[0]
    assert framework["scd:name"] == "Test Framework"
    assert framework["scd:description"] == "A test framework"
    assert framework["scd:version"] == "1.0.0"
    
    # Find items
    items = [item for item in graph if item.get("@type") == "scd:CompetencyDefinition"]
    assert len(items) == 2
    
    # Find associations
    associations = [item for item in graph if item.get("@type") == "scd:ResourceAssociation"]
    assert len(associations) == 2


def test_missing_items_validation(case_with_missing_items):
    """Test that associations with missing items are handled."""
    response = client.post("/translate/case-to-ieee", json=case_with_missing_items)
    assert response.status_code == 200
    
    data = response.json()
    graph = data["@graph"]
    
    # Should have: 1 framework + 1 item + 1 association = 3 items
    assert len(graph) == 3
    
    # Find the association
    associations = [item for item in graph if item.get("@type") == "scd:ResourceAssociation"]
    assert len(associations) == 1
    
    assoc = associations[0]
    target_id = assoc["scd:targetNode"]["@id"]
    
    # Check if target exists in graph
    item_ids = [item["@id"] for item in graph if item.get("@type") == "scd:CompetencyDefinition"]
    # This association references item-999 which doesn't exist
    # The translation still succeeds, but target_id won't be in item_ids
    assert target_id not in item_ids  # This validates the missing item scenario


def test_cyclic_associations(case_with_cyclic_associations):
    """Test that cyclic associations are handled gracefully."""
    response = client.post("/translate/case-to-ieee", json=case_with_cyclic_associations)
    assert response.status_code == 200
    
    data = response.json()
    graph = data["@graph"]
    
    # Should have: 1 framework + 2 items + 2 associations = 5 items
    assert len(graph) == 5
    
    associations = [item for item in graph if item.get("@type") == "scd:ResourceAssociation"]
    assert len(associations) == 2
    
    # Verify both associations exist (cycles are allowed)
    assoc_ids = [assoc["@id"] for assoc in associations]
    assert len(assoc_ids) == 2


def test_unknown_association_type(case_with_unknown_association_type):
    """Test that unmapped association types pass through unchanged."""
    response = client.post("/translate/case-to-ieee", json=case_with_unknown_association_type)
    assert response.status_code == 200
    
    data = response.json()
    graph = data["@graph"]
    
    associations = [item for item in graph if item.get("@type") == "scd:ResourceAssociation"]
    assert len(associations) == 1
    
    assoc = associations[0]
    # Unknown type should pass through unchanged
    assert assoc["scd:relationType"] == "customType"


def test_invalid_input():
    """Test handling of invalid input."""
    response = client.post("/translate/case-to-ieee", json={"invalid": "data"})
    assert response.status_code == 422  # Validation error


def test_empty_items_arrays():
    """Test document with empty items and associations arrays."""
    case = {
        "CFDocument": {"identifier": "framework-001", "title": "Test"},
        "CFItems": [],
        "CFAssociations": []
    }
    response = client.post("/translate/case-to-ieee", json=case)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["@graph"]) == 1  # Only framework


# ============================================================================
# Mapping Correctness Tests
# ============================================================================

def test_association_type_mapping():
    """Test that association types are correctly mapped."""
    case = {
        "CFDocument": {"identifier": "framework-001", "title": "Test"},
        "CFItems": [
            {"identifier": "item-1", "fullStatement": "Item 1"},
            {"identifier": "item-2", "fullStatement": "Item 2"},
            {"identifier": "item-3", "fullStatement": "Item 3"}
        ],
        "CFAssociations": [
            {
                "identifier": "assoc-1",
                "associationType": "isChildOf",
                "originNodeURI": {"identifier": "item-1"},
                "destinationNodeURI": {"identifier": "item-2"}
            },
            {
                "identifier": "assoc-2",
                "associationType": "precedes",
                "originNodeURI": {"identifier": "item-2"},
                "destinationNodeURI": {"identifier": "item-3"}
            },
            {
                "identifier": "assoc-3",
                "associationType": "hasSkillLevel",
                "originNodeURI": {"identifier": "item-1"},
                "destinationNodeURI": {"identifier": "item-3"}
            }
        ]
    }
    
    response = client.post("/translate/case-to-ieee", json=case)
    assert response.status_code == 200
    
    data = response.json()
    associations = [item for item in data["@graph"] if item.get("@type") == "scd:ResourceAssociation"]
    
    # Check mappings
    mapping_map = {
        "isChildOf": "hasPart",
        "precedes": "precedes",
        "hasSkillLevel": "competencyLevel"
    }
    
    for assoc in associations:
        orig_type = None
        for assoc_data in case["CFAssociations"]:
            if assoc["@id"].endswith(assoc_data["identifier"]) or assoc["@id"] == assoc_data.get("uri", f"#{assoc_data['identifier']}"):
                orig_type = assoc_data["associationType"]
                break
        
        if orig_type in mapping_map:
            assert assoc["scd:relationType"] == mapping_map[orig_type]


def test_field_mapping():
    """Test that CASE fields map correctly to IEEE SCD fields."""
    case = {
        "CFDocument": {
            "identifier": "framework-001",
            "title": "Framework Title",
            "description": "Framework Description",
            "version": "1.0"
        },
        "CFItems": [
            {
                "identifier": "item-001",
                "fullStatement": "Full statement",
                "abbreviatedStatement": "Abbr",
                "conceptKeywords": ["keyword1", "keyword2"]
            }
        ],
        "CFAssociations": []
    }
    
    response = client.post("/translate/case-to-ieee", json=case)
    assert response.status_code == 200
    
    data = response.json()
    graph = data["@graph"]
    
    framework = [item for item in graph if item.get("@type") == "scd:CompetencyFramework"][0]
    assert framework["scd:name"] == "Framework Title"
    assert framework["scd:description"] == "Framework Description"
    assert framework["scd:version"] == "1.0"
    
    item = [item for item in graph if item.get("@type") == "scd:CompetencyDefinition"][0]
    assert item["scd:statement"] == "Full statement"
    assert item["scd:abbreviatedStatement"] == "Abbr"
    assert item["scd:conceptKeyword"] == ["keyword1", "keyword2"]


# ============================================================================
# JSON-LD Structure Validation Tests
# ============================================================================

def test_jsonld_structure(minimal_case):
    """Test that output conforms to JSON-LD structure requirements."""
    response = client.post("/translate/case-to-ieee", json=minimal_case)
    assert response.status_code == 200
    
    data = response.json()
    
    # Check root structure
    assert "@context" in data
    assert "@graph" in data
    
    # Check @context
    context = data["@context"]
    assert "scd" in context
    assert context["scd"] == "https://w3id.org/skill-credential/"
    
    # Check @graph
    graph = data["@graph"]
    assert isinstance(graph, list)
    assert len(graph) > 0
    
    # Check every item in graph
    item_ids = set()
    for item in graph:
        # Every item must have @id
        assert "@id" in item
        assert isinstance(item["@id"], str)
        assert len(item["@id"]) > 0
        
        # Every item must have @type
        assert "@type" in item
        assert isinstance(item["@type"], str)
        
        # No duplicate @id values
        item_id = item["@id"]
        assert item_id not in item_ids, f"Duplicate @id found: {item_id}"
        item_ids.add(item_id)


def test_iri_generation():
    """Test IRI generation from URIs and identifiers."""
    case = {
        "CFDocument": {
            "identifier": "framework-001",
            "uri": "http://example.org/frameworks/framework-001"
        },
        "CFItems": [
            {
                "identifier": "item-001",
                "uri": "http://example.org/items/item-001"
            },
            {
                "identifier": "item-002",
                # No URI - should use identifier-based IRI
            }
        ],
        "CFAssociations": []
    }
    
    response = client.post("/translate/case-to-ieee", json=case)
    assert response.status_code == 200
    
    data = response.json()
    graph = data["@graph"]
    
    framework = [item for item in graph if item.get("@type") == "scd:CompetencyFramework"][0]
    assert framework["@id"] == "http://example.org/frameworks/framework-001"
    
    items = [item for item in graph if item.get("@type") == "scd:CompetencyDefinition"]
    item_with_uri = [item for item in items if "item-001" in item["@id"]][0]
    assert item_with_uri["@id"] == "http://example.org/items/item-001"
    
    item_without_uri = [item for item in items if "item-002" in item["@id"]][0]
    # Should use identifier-based IRI (format depends on base_iri logic)
    assert item_without_uri["@id"] is not None
    assert len(item_without_uri["@id"]) > 0


def test_graph_completeness(full_case):
    """Test that all input entities appear in output graph."""
    response = client.post("/translate/case-to-ieee", json=full_case)
    assert response.status_code == 200
    
    data = response.json()
    graph = data["@graph"]
    
    # Count entities by type
    frameworks = [item for item in graph if item.get("@type") == "scd:CompetencyFramework"]
    items = [item for item in graph if item.get("@type") == "scd:CompetencyDefinition"]
    associations = [item for item in graph if item.get("@type") == "scd:ResourceAssociation"]
    
    assert len(frameworks) == 1
    assert len(items) == len(full_case["CFItems"])
    assert len(associations) == len(full_case["CFAssociations"])


# ============================================================================
# Edge Case Tests
# ============================================================================

def test_optional_fields_omitted():
    """Test that optional fields are omitted when not present."""
    case = {
        "CFDocument": {"identifier": "framework-001"},  # Minimal document
        "CFItems": [
            {"identifier": "item-001"}  # Minimal item
        ],
        "CFAssociations": []
    }
    
    response = client.post("/translate/case-to-ieee", json=case)
    assert response.status_code == 200
    
    data = response.json()
    graph = data["@graph"]
    
    framework = [item for item in graph if item.get("@type") == "scd:CompetencyFramework"][0]
    # Optional fields should not be present
    assert "scd:name" not in framework or framework.get("scd:name") is None
    
    item = [item for item in graph if item.get("@type") == "scd:CompetencyDefinition"][0]
    # Optional fields should not be present
    assert "scd:statement" not in item or item.get("scd:statement") is None


def test_large_document():
    """Test translation with many items and associations."""
    case = {
        "CFDocument": {"identifier": "framework-001", "title": "Large Framework"},
        "CFItems": [
            {"identifier": f"item-{i:03d}", "fullStatement": f"Item {i}"}
            for i in range(100)
        ],
        "CFAssociations": [
            {
                "identifier": f"assoc-{i:03d}",
                "associationType": "precedes",
                "originNodeURI": {"identifier": f"item-{i:03d}"},
                "destinationNodeURI": {"identifier": f"item-{(i+1) % 100:03d}"}
            }
            for i in range(100)
        ]
    }
    
    response = client.post("/translate/case-to-ieee", json=case)
    assert response.status_code == 200
    
    data = response.json()
    graph = data["@graph"]
    
    # Should have: 1 framework + 100 items + 100 associations = 201 items
    assert len(graph) == 201


# ============================================================================
# Validation Helper Functions
# ============================================================================

def validate_missing_items(data, case_input):
    """Helper to validate if associations reference missing items."""
    graph = data["@graph"]
    items = {item["@id"] for item in graph if item.get("@type") == "scd:CompetencyDefinition"}
    items.update(item["@id"] for item in graph if item.get("@type") == "scd:CompetencyFramework")
    
    associations = [item for item in graph if item.get("@type") == "scd:ResourceAssociation"]
    missing_refs = []
    
    for assoc in associations:
        source_id = assoc.get("scd:sourceNode", {}).get("@id")
        target_id = assoc.get("scd:targetNode", {}).get("@id")
        
        if source_id and source_id not in items:
            missing_refs.append(f"Source node {source_id} not found")
        if target_id and target_id not in items:
            missing_refs.append(f"Target node {target_id} not found")
    
    return missing_refs


def test_validation_helper_missing_items(case_with_missing_items):
    """Test the missing items validation helper."""
    response = client.post("/translate/case-to-ieee", json=case_with_missing_items)
    assert response.status_code == 200
    
    data = response.json()
    missing_refs = validate_missing_items(data, case_with_missing_items)
    
    # Should detect the missing item reference
    assert len(missing_refs) > 0
    assert any("item-999" in ref for ref in missing_refs)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

