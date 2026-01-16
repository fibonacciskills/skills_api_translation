# CASE 1.1 Translator

A minimal FastAPI service that translates 1EdTech CASE 1.1 JSON documents to:
- **IEEE SCD** JSON-LD format
- **ASN-CTDL** JSON-LD format

## Setup

1. **Install Python 3.11** (if not already installed)

2. **Create a virtual environment** (recommended):
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Service

Start the server:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload
```

The service will be available at `http://localhost:8000`

- **Web UI**: `http://localhost:8000/` (serves the interactive translator)
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- Translate endpoints:
  - `POST /translate` (Unified endpoint using HTTP Accept header for format selection)
  - `POST /translate/case-to-ieee` (IEEE SCD output, JSON body - deprecated, use `/translate` with Accept header)
  - `POST /translate/case-to-asn` (ASN-CTDL output, JSON body - deprecated, use `/translate` with Accept header)
  - `POST /translate/upload-file` (File upload endpoint, accepts .json, .csv, .xlsx, .xls files)
- Field mapping: `GET /field-mapping` (JSON endpoint with 3-way comparison)
- Field mapping CSV: `field_mapping.csv` (static CSV file viewable in GitHub)

## Web UI

A simple web interface is available for interactive translation:

1. **Start the API server** (see "Running the Service" above)

2. **Open the web UI**: Navigate to `http://localhost:8000/` in your browser

3. **Features**:
   - **Translator Tab**:
     - Format selector: Choose between IEEE SCD or ASN-CTDL output format
     - **File upload**: Upload a JSON file directly - automatically loads into editor and translates
     - Left panel: Editable CASE 1.1 JSON input (pre-loaded with example data)
     - Right panel: Read-only JSON-LD output (format depends on selection)
     - Translate button: Sends POST request to the appropriate API endpoint
     - Progress indicators: Shows "Parsing CASE", "Building graph", "Emitting JSON-LD"
     - Request/Response details: Expandable section showing HTTP status, request payload, and response payload
     - Syntax highlighting: JSON is color-coded for readability
     - Error display: Clear error messages shown in UI
     - Keyboard shortcut: Ctrl/Cmd + Enter to translate
   
   - **Field Mapping Tab**:
     - Complete 3-way mapping table: CASE 1.1 ↔ IEEE SCD ↔ ASN-CTDL
     - Shows mapped fields (with corresponding field names in each format)
     - Shows partially mapped fields (available in one format but not the other)
     - Shows format-specific fields (added during translation)
     - Organized by entity type: CFDocument, CFItem, CFAssociation
     - Color-coded badges for quick status identification

## Testing the API

### Quick Health Check

Test that the API is running:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","service":"CASE to IEEE SCD Translator"}
```

### Example Requests

#### 1. Translate using Accept Header (Recommended)

The API uses HTTP content negotiation with Accept headers to specify the desired output format:

**IEEE SCD:**
```bash
curl -X POST "http://localhost:8000/translate" \
  -H "Content-Type: application/json" \
  -H 'Accept: application/ld+json; profile="https://opensource.ieee.org/scd/scd/-/blob/main/resources/context.jsonld"' \
  -d @example_case.json
```

**ASN-CTDL:**
```bash
curl -X POST "http://localhost:8000/translate" \
  -H "Content-Type: application/json" \
  -H 'Accept: application/ld+json; profile="https://purl.org/ctdlasn/terms/"' \
  -d @example_case.json
```

The API returns `Content-Type` header with the same profile URI to indicate the format of the response.

#### 2. Translate to IEEE SCD (JSON body - Legacy endpoint)

```bash
curl -X POST "http://localhost:8000/translate/case-to-ieee" \
  -H "Content-Type: application/json" \
  -d @example_case.json
```

Save output to file:
```bash
curl -X POST "http://localhost:8000/translate/case-to-ieee" \
  -H "Content-Type: application/json" \
  -d @example_case.json \
  -o output_ieee_scd.json
```

#### 3. Translate to ASN-CTDL (JSON body - Legacy endpoint)

```bash
curl -X POST "http://localhost:8000/translate/case-to-asn" \
  -H "Content-Type: application/json" \
  -d @example_case.json
```

Save output to file:
```bash
curl -X POST "http://localhost:8000/translate/case-to-asn" \
  -H "Content-Type: application/json" \
  -d @example_case.json \
  -o output_asn_ctdl.json
```

#### 4. File Upload (supports Accept header or target_format parameter)

**Using Accept Header (Recommended):**
```bash
curl -X POST "http://localhost:8000/translate/upload-file" \
  -H 'Accept: application/ld+json; profile="https://opensource.ieee.org/scd/scd/-/blob/main/resources/context.jsonld"' \
  -F "file=@example_case.json"
```

**Using target_format parameter (Legacy):**
```bash
curl -X POST "http://localhost:8000/translate/upload-file" \
  -F "file=@example_case.json" \
  -F "target_format=ieee_scd"
```

The file upload endpoint supports multiple formats:
- **JSON**: CASE 1.1 format (.json)
- **CSV**: Tabular data with competency columns (.csv)
- **Excel**: Multi-sheet workbook (.xlsx, .xls)

Save output to file:
```bash
curl -X POST "http://localhost:8000/translate/upload-file" \
  -H 'Accept: application/ld+json; profile="https://opensource.ieee.org/scd/scd/-/blob/main/resources/context.jsonld"' \
  -F "file=@example_case.json" \
  -o output_ieee_scd.json
```

#### 5. File Upload to ASN-CTDL

```bash
curl -X POST "http://localhost:8000/translate/upload-file" \
  -F "file=@example_case.json" \
  -F "target_format=asn_ctdl"
```

Save output to file:
```bash
curl -X POST "http://localhost:8000/translate/upload-file" \
  -F "file=@example_case.json" \
  -F "target_format=asn_ctdl" \
  -o output_asn_ctdl.json
```

#### 6. View Field Mappings

Get the complete field mapping reference:
```bash
curl http://localhost:8000/field-mapping | python -m json.tool
```

Or save to file:
```bash
curl http://localhost:8000/field-mapping -o field_mappings.json
```

### Testing with Your Own Files

Replace `example_case.json` with your own CASE file:

```bash
# Translate your file to IEEE SCD
curl -X POST "http://localhost:8000/translate/upload-file" \
  -F "file=@your_case_file.json" \
  -F "target_format=ieee_scd" \
  -o your_output_ieee.json

# Translate your file to ASN-CTDL
curl -X POST "http://localhost:8000/translate/upload-file" \
  -F "file=@your_case_file.json" \
  -F "target_format=asn_ctdl" \
  -o your_output_asn.json
```

### Testing Output Format

The API returns valid JSON-LD that can be directly uploaded to systems expecting:
- **IEEE SCD format**: Systems using the Skill Credential vocabulary
- **ASN-CTDL format**: Systems using the CASE/ASN vocabulary

Output structure:
```json
{
  "@context": {
    "scd": "https://w3id.org/skill-credential/",
    "@vocab": "https://w3id.org/skill-credential/"
  },
  "@graph": [
    {
      "@id": "...",
      "@type": "scd:CompetencyFramework",
      ...
    },
    ...
  ]
}
```

This format is ready for direct import into systems that accept JSON-LD with `@context` and `@graph`.

### Viewing API Documentation

Once the server is running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **Alternative Docs**: `http://localhost:8000/redoc`

These provide interactive forms to test the API directly in your browser.

## Example CASE JSON

See `example_case.json` for a sample CASE document structure.

## How the Translation API Works

The translation API uses **static table mapping** - a deterministic, rule-based approach with hardcoded field mappings and translation functions. This is not machine learning or dynamic lookup; it's a straightforward one-to-one field mapping system.

### Translation Architecture

The translation process works in three stages:

1. **Entity Translation**: Each CASE entity type maps to a specific target entity type
   - `CFDocument` → `scd:CompetencyFramework` (IEEE SCD) or `ceasn:CompetencyFramework` (ASN-CTDL)
   - `CFItem` → `scd:CompetencyDefinition` (IEEE SCD) or `ceasn:Competency` (ASN-CTDL)
   - `CFAssociation` → `scd:ResourceAssociation` (IEEE SCD) or direct properties on competencies (ASN-CTDL)

2. **Field Mapping**: Each source field maps directly to a target field using hardcoded mappings
   - Example: `title` → `scd:name` (IEEE SCD) or `ceasn:name` (ASN-CTDL)
   - Example: `fullStatement` → `scd:statement` (IEEE SCD) or `ceasn:competencyText` (ASN-CTDL)
   - See `field_mapping.csv` or `/field-mapping` endpoint for complete mappings

3. **Association Type Mapping**: CASE association types map to target relationship types using static dictionaries:
   ```python
   # IEEE SCD mappings
   "isChildOf" → "hasPart"
   "precedes" → "precedes"
   "hasSkillLevel" → "competencyLevel"
   
   # ASN-CTDL mappings
   "isChildOf" → "ceasn:isChildOf" (direct property)
   "precedes" → "ceasn:prerequisiteAlignment"
   ```

### Translation Process Flow

1. **Parse Input**: CASE JSON is parsed and validated using Pydantic models
2. **Entity Translation**: Each entity (CFDocument, CFItem, CFAssociation) is translated using format-specific functions
3. **Field Mapping**: Source fields are conditionally mapped to target fields (only if present in source)
4. **IRI Generation**: Identifiers are converted to `@id` IRIs (using provided URI or generating from identifier)
5. **Graph Assembly**: All translated entities are assembled into a `@graph` array
6. **Context Addition**: Format-specific `@context` is added with appropriate namespace URIs
7. **Response**: JSON-LD document is returned with appropriate `Content-Type` header including profile URI

### Key Characteristics

- **Deterministic**: Same input always produces same output
- **Static Mappings**: All field mappings are hardcoded in translation functions
- **Conditional**: Fields are only included if present in source (no defaults)
- **Preserves Structure**: Identifiers, relationships, and data types are preserved
- **Format-Specific**: Different logic for IEEE SCD vs ASN-CTDL (e.g., associations handled differently)

### Mapping Tables

The complete field mappings are available in two formats:
- **CSV**: `field_mapping.csv` (viewable in GitHub)
- **JSON**: `GET /field-mapping` API endpoint

These show every CASE field, its mapping to IEEE SCD and ASN-CTDL, whether it's mapped, and notes about the mapping.

## Translation Rules

### IEEE SCD Format:
- **CFDocument** → `scd:CompetencyFramework`
- **CFItems** → `scd:CompetencyDefinition`
- **CFAssociations** → `scd:ResourceAssociation`
- **Association Type Mappings**:
  - `isChildOf` → `hasPart`
  - `precedes` → `precedes`
  - `hasSkillLevel` → `competencyLevel`

### ASN-CTDL Format:
- **CFDocument** → `ceasn:CompetencyFramework`
- **CFItems** → `ceasn:Competency`
- **CFAssociations** → Direct properties on `ceasn:Competency` objects
- **Association Type Mappings**:
  - `isChildOf` → `ceasn:isChildOf` (direct property)
  - `precedes` → `ceasn:prerequisiteAlignment`
  - `hasSkillLevel` → `asn:hasProgressionLevel`

Both formats preserve identifiers as `@id` IRIs and output valid JSON-LD documents with `@context` and `@graph`.

