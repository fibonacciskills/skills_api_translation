# Testing Guide

Quick reference for running tests on the CASE to IEEE SCD Translator.

## Setup

Install test dependencies:
```bash
pip install -r requirements.txt
```

## Running Tests

### Run All Tests
```bash
pytest test_translator.py -v
```

### Run Specific Test
```bash
pytest test_translator.py::test_basic_translation -v
```

### Run with Coverage
```bash
pytest test_translator.py --cov=main --cov-report=term-missing
```

### Run Specific Test Category
```bash
# Just mapping tests
pytest test_translator.py -k "mapping" -v

# Just JSON-LD structure tests
pytest test_translator.py -k "jsonld" -v

# Just validation tests
pytest test_translator.py -k "validation" -v
```

## Test Coverage

The test suite includes:

1. **API Endpoint Tests**
   - Health check
   - Basic translation
   - Full document translation
   - Invalid input handling

2. **Mapping Correctness Tests**
   - Association type mapping (isChildOf → hasPart, etc.)
   - Field mapping (title → scd:name, etc.)

3. **Validation Tests**
   - Missing CFItems (associations referencing non-existent items)
   - Cyclic associations
   - Unknown association types

4. **JSON-LD Structure Tests**
   - @context and @graph presence
   - All entities have @id and @type
   - No duplicate @id values
   - Valid IRI format

5. **Edge Case Tests**
   - Empty arrays
   - Optional fields omitted
   - Large documents (100+ items)

## Manual Testing

See `TEST_PLAN.md` for detailed manual test cases you can follow step-by-step.

## Expected Test Results

All tests should pass. If any fail:

1. Check that the API server dependencies are installed
2. Verify the main.py code matches the test expectations
3. Review test output for specific assertion failures

## Test Output Example

```
test_translator.py::test_health_endpoint PASSED
test_translator.py::test_basic_translation PASSED
test_translator.py::test_full_case_translation PASSED
test_translator.py::test_missing_items_validation PASSED
test_translator.py::test_cyclic_associations PASSED
test_translator.py::test_unknown_association_type PASSED
...
```

