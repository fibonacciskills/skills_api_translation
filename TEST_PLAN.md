# Test Plan: CASE to IEEE SCD Translator

## Overview
This test plan validates the correctness of translating 1EdTech CASE JSON documents to IEEE SCD JSON-LD format.

## "What Good Looks Like" Criteria

### ✅ Success Criteria
1. **Correct Mapping**: All CASE entities map to correct IEEE SCD types
   - CFDocument → scd:CompetencyFramework
   - CFItems → scd:CompetencyDefinition
   - CFAssociations → scd:ResourceAssociation

2. **Association Type Mapping**: Association types are correctly mapped
   - `isChildOf` → `hasPart`
   - `precedes` → `precedes`
   - `hasSkillLevel` → `competencyLevel`

3. **Identifier Preservation**: All identifiers are preserved as `@id` IRIs

4. **Valid JSON-LD Structure**: Output contains:
   - `@context` with scd namespace
   - `@graph` containing all translated entities

5. **Field Mapping**: All mapped fields are correctly translated
   - Optional fields only included if present in input
   - Field names match IEEE SCD vocabulary

6. **Graph Completeness**: All input entities appear in output graph

### ⚠️ Validation Requirements
1. **Missing CFItems**: Associations referencing non-existent items should be handled (warn or error)
2. **Cyclic Associations**: Circular references should be detected or handled gracefully
3. **Unknown AssociationType**: Unmapped association types should pass through unchanged

### 📋 JSON-LD Sanity Checks
1. Every entity has `@id`
2. Every entity has `@type`
3. All `@id` values are valid IRIs (relative or absolute)
4. `@context` is present and contains scd namespace
5. `@graph` contains all entities

---

## Manual Test Cases

### Test Case 1: Basic Translation
**Purpose**: Verify basic functionality with a simple, valid CASE document

**Steps**:
1. Start the API server: `python main.py`
2. Open `index.html` in browser
3. Load `example_case.json` (or paste minimal valid CASE JSON)
4. Click "Translate"
5. Verify progress indicators show all 3 steps
6. Check output panel shows valid JSON-LD

**Expected Results**:
- ✅ HTTP Status: 200 Success
- ✅ Output contains `@context` and `@graph`
- ✅ Exactly 1 CompetencyFramework in graph
- ✅ Number of CompetencyDefinitions matches number of CFItems
- ✅ Number of ResourceAssociations matches number of CFAssociations
- ✅ All association types are mapped correctly

**Validation Checks**:
- [ ] Framework has `scd:name` matching CASE title
- [ ] All items have `@id` matching their identifiers
- [ ] All associations reference valid `@id` values

---

### Test Case 2: Missing CFItems Validation
**Purpose**: Verify behavior when associations reference non-existent items

**Steps**:
1. Create a CASE document with:
   - 1 CFItem with identifier "item-1"
   - 1 CFAssociation referencing "item-2" (doesn't exist)
2. Send POST request to `/translate/case-to-ieee`
3. Check response and logs

**Expected Results**:
- ⚠️ Translation completes (current behavior)
- ⚠️ Association is created but references missing item
- ⚠️ Logs should warn about missing item (or test should catch it)

**Validation Checks**:
- [ ] Response is valid JSON-LD
- [ ] Association exists with `@id` pointing to non-existent item
- [ ] Graph integrity check: all referenced items exist

---

### Test Case 3: Cyclic Associations
**Purpose**: Verify handling of circular references in associations

**Steps**:
1. Create a CASE document with cyclic associations:
   - Item A → precedes → Item B
   - Item B → precedes → Item A
2. Send POST request
3. Check response

**Expected Results**:
- ✅ Translation completes successfully
- ✅ Both associations are created
- ✅ Graph is valid (cycles are allowed in directed graphs)

**Validation Checks**:
- [ ] Both associations appear in graph
- [ ] Source/target nodes correctly reference item @ids
- [ ] No infinite loops during processing

---

### Test Case 4: Unknown AssociationType
**Purpose**: Verify unmapped association types pass through

**Steps**:
1. Create a CASE document with associationType "customType" (not in mapping)
2. Send POST request
3. Inspect output

**Expected Results**:
- ✅ Translation completes
- ✅ Association uses "customType" as-is (not mapped)
- ✅ Association still created as ResourceAssociation

**Validation Checks**:
- [ ] `scd:relationType` = "customType" (original value)
- [ ] Association is valid ResourceAssociation

---

### Test Case 5: Empty Document
**Purpose**: Verify edge case with minimal document

**Steps**:
1. Create CASE with:
   - CFDocument (required fields only)
   - Empty CFItems array
   - Empty CFAssociations array
2. Send POST request

**Expected Results**:
- ✅ Translation succeeds
- ✅ Graph contains only the framework
- ✅ `@graph` has exactly 1 item

**Validation Checks**:
- [ ] Framework is present with correct `@type`
- [ ] No CompetencyDefinitions
- [ ] No ResourceAssociations

---

### Test Case 6: JSON-LD Structure Validation
**Purpose**: Verify output conforms to JSON-LD structure

**Steps**:
1. Translate a valid CASE document
2. Inspect output structure

**Expected Results**:
- ✅ Root object has `@context` and `@graph`
- ✅ `@context.scd` = "https://w3id.org/skill-credential/"
- ✅ All graph items have `@id` and `@type`
- ✅ All `@id` values are strings

**Validation Checks**:
- [ ] `@context` exists and has scd namespace
- [ ] `@graph` is an array
- [ ] Every item in graph has `@id` (string)
- [ ] Every item in graph has `@type` (string)
- [ ] No duplicate `@id` values

---

### Test Case 7: Field Preservation
**Purpose**: Verify all optional fields are correctly mapped

**Steps**:
1. Create CASE with all optional fields populated:
   - CFDocument: title, description, version, publisher, etc.
   - CFItem: fullStatement, abbreviatedStatement, conceptKeywords, etc.
   - CFAssociation: sequenceNumber, lastChangeDateTime
2. Translate and inspect output

**Expected Results**:
- ✅ All populated fields appear in output
- ✅ Field names match expected IEEE SCD vocabulary
- ✅ Field values are preserved correctly

**Validation Checks**:
- [ ] Framework has scd:name, scd:description, scd:version
- [ ] Items have scd:statement, scd:abbreviatedStatement
- [ ] Associations have scd:sequenceNumber, scd:dateModified

---

### Test Case 8: IRI Generation
**Purpose**: Verify IRI generation from URIs and identifiers

**Steps**:
1. Create CASE with:
   - CFDocument with URI
   - Some items with URIs, some without
   - Associations mixing URI and identifier references
2. Translate and check all `@id` values

**Expected Results**:
- ✅ Items with URIs use URI as `@id`
- ✅ Items without URIs use identifier-based `@id`
- ✅ Base IRI is used when available

**Validation Checks**:
- [ ] All `@id` values are valid (non-empty strings)
- [ ] URI-based items use full URI
- [ ] Identifier-based items use consistent format

---

## Test Data Files

- `test_data/minimal_case.json` - Minimal valid CASE document
- `test_data/full_case.json` - CASE with all fields populated
- `test_data/missing_items_case.json` - Associations with missing items
- `test_data/cyclic_associations_case.json` - Circular references
- `test_data/unknown_association_type_case.json` - Unmapped association type
- `test_data/empty_case.json` - Document with no items/associations

---

## Running Tests

### Manual Tests
1. Start server: `python main.py`
2. Follow test cases above using UI or curl
3. Verify results match expected outcomes

### Automated Tests
```bash
# Install test dependencies
pip install pytest httpx

# Run all tests
pytest test_translator.py -v

# Run with coverage
pytest test_translator.py --cov=main --cov-report=term-missing

# Run specific test
pytest test_translator.py::test_basic_translation -v
```

---

## Known Limitations

1. **Missing Items**: Currently no validation for associations referencing non-existent items
2. **Cycles**: Cycles are allowed but not detected/warned
3. **Association Type Validation**: Unknown types pass through without validation

These may be acceptable depending on requirements, but should be documented.

