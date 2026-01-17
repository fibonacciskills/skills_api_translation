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
  - `POST /translate/case-to-ieee` (IEEE SCD output, JSON body)
  - `POST /translate/case-to-asn` (ASN-CTDL output, JSON body)
  - `POST /translate/upload-file` (File upload endpoint, accepts .json file)
- Field mapping: `GET /field-mapping` (JSON endpoint with 3-way comparison)

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

#### 1. Translate to IEEE SCD (JSON body)

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

#### 2. Translate to ASN-CTDL (JSON body)

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

#### 3. File Upload to IEEE SCD

```bash
curl -X POST "http://localhost:8000/translate/upload-file" \
  -F "file=@example_case.json" \
  -F "target_format=ieee_scd"
```

Save output to file:
```bash
curl -X POST "http://localhost:8000/translate/upload-file" \
  -F "file=@example_case.json" \
  -F "target_format=ieee_scd" \
  -o output_ieee_scd.json
```

#### 4. File Upload to ASN-CTDL

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

#### 5. View Field Mappings

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
- **IEEE SCD format**: Systems using the Shareable Competency Definition vocabulary
- **ASN-CTDL format**: Systems using the ASN vocabulary

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

