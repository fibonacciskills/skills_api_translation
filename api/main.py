"""
FastAPI service to translate 1EdTech CASE JSON to IEEE SCD JSON-LD.
"""
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
import uuid
import logging
import time
import os
import json
from pathlib import Path
import io
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CASE to IEEE SCD Translator",
    description="Translates 1EdTech CASE JSON documents to IEEE SCD JSON-LD format",
    version="1.0.0"
)

# Enable CORS for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for CASE input
class CFDocument(BaseModel):
    identifier: str
    uri: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    adoptionStatus: Optional[str] = None
    version: Optional[str] = None
    lastChangeDateTime: Optional[str] = None
    publisher: Optional[Dict[str, Any]] = None
    officialSourceURL: Optional[str] = None
    educationLevel: Optional[List[str]] = None
    subject: Optional[List[Dict[str, Any]]] = None
    rights: Optional[str] = None
    license: Optional[str] = None
    notes: Optional[str] = None


class CFItem(BaseModel):
    identifier: str
    uri: Optional[str] = None
    fullStatement: Optional[str] = None
    alternativeLabel: Optional[List[str]] = None
    CFItemType: Optional[str] = None
    hierarchyCode: Optional[str] = None
    abbreviatedStatement: Optional[str] = None
    conceptKeywords: Optional[List[str]] = None
    conceptKeywordsUri: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None
    language: Optional[str] = None
    educationLevel: Optional[List[str]] = None
    humanCodingScheme: Optional[str] = None


class CFAssociation(BaseModel):
    identifier: str
    uri: Optional[str] = None
    associationType: str
    originNodeURI: Dict[str, str]  # {identifier: "...", uri: "..."}
    destinationNodeURI: Dict[str, str]  # {identifier: "...", uri: "..."}
    CFDocumentURI: Optional[Dict[str, Any]] = None
    sequenceNumber: Optional[int] = None
    lastChangeDateTime: Optional[str] = None


class CASEInput(BaseModel):
    CFDocument: CFDocument
    CFItems: List[CFItem] = []
    CFAssociations: List[CFAssociation] = []


# Association type mappings for IEEE SCD
ASSOCIATION_TYPE_MAP_SCD = {
    "isChildOf": "hasPart",
    "precedes": "precedes",
    "hasSkillLevel": "competencyLevel"
}

# Association type mappings for ASN-CTDL (many map directly)
ASSOCIATION_TYPE_MAP_ASN = {
    "isChildOf": "isChildOf",  # Direct mapping!
    "precedes": "prerequisiteAlignment",  # ASN uses alignment property
    "hasSkillLevel": None  # May need special handling
}


def get_iri(identifier: str, uri: Optional[str] = None) -> str:
    """Generate IRI from identifier or use provided URI."""
    if uri:
        return uri
    # If no URI provided, create a simple IRI from the identifier
    return f"#{identifier}"


def translate_cf_document(cf_doc: CFDocument, target_format: str = "ieee_scd") -> Dict[str, Any]:
    """Translate CFDocument to target format (ieee_scd or asn_ctdl)."""
    framework_id = get_iri(cf_doc.identifier, cf_doc.uri)
    
    if target_format == "asn_ctdl":
        return translate_cf_document_asn(cf_doc, framework_id)
    else:
        return translate_cf_document_scd(cf_doc, framework_id)


def translate_cf_document_scd(cf_doc: CFDocument, framework_id: str) -> Dict[str, Any]:
    """Translate CFDocument to scd:CompetencyFramework."""
    result = {
        "@id": framework_id,
        "@type": "scd:CompetencyFramework"
    }
    
    if cf_doc.title:
        result["scd:name"] = cf_doc.title
    if cf_doc.description:
        result["scd:description"] = cf_doc.description
    if cf_doc.language:
        result["scd:language"] = cf_doc.language
    if cf_doc.version:
        result["scd:version"] = cf_doc.version
    if cf_doc.lastChangeDateTime:
        result["scd:dateModified"] = cf_doc.lastChangeDateTime
    if cf_doc.publisher:
        result["scd:publisher"] = cf_doc.publisher
    if cf_doc.officialSourceURL:
        result["scd:url"] = cf_doc.officialSourceURL
    
    return result


def translate_cf_document_asn(cf_doc: CFDocument, framework_id: str) -> Dict[str, Any]:
    """Translate CFDocument to ceasn:CompetencyFramework."""
    result = {
        "@id": framework_id,
        "@type": "ceasn:CompetencyFramework"
    }
    
    if cf_doc.identifier:
        # Use identifier as ceasn:identifier (URI)
        result["ceasn:identifier"] = framework_id
    if cf_doc.title:
        result["ceasn:name"] = cf_doc.title
    if cf_doc.description:
        result["ceasn:description"] = cf_doc.description
    if cf_doc.language:
        result["ceasn:inLanguage"] = cf_doc.language
    if cf_doc.version:
        # ASN doesn't have direct version field, could use codedNotation
        pass
    if cf_doc.lastChangeDateTime:
        result["ceasn:dateModified"] = cf_doc.lastChangeDateTime
    if cf_doc.publisher:
        result["ceasn:publisher"] = cf_doc.publisher
    if cf_doc.officialSourceURL:
        result["ceasn:source"] = cf_doc.officialSourceURL
    if cf_doc.rights:
        result["ceasn:rights"] = cf_doc.rights
    if cf_doc.license:
        result["ceasn:license"] = cf_doc.license
    if cf_doc.adoptionStatus:
        # Map to publicationStatusType if possible
        pass
    
    return result


def translate_cf_item(cf_item: CFItem, base_iri: Optional[str] = None, target_format: str = "ieee_scd") -> Dict[str, Any]:
    """Translate CFItem to target format (ieee_scd or asn_ctdl)."""
    item_id = get_iri(cf_item.identifier, cf_item.uri)
    if base_iri and not cf_item.uri:
        item_id = f"{base_iri}#{cf_item.identifier}"
    
    if target_format == "asn_ctdl":
        return translate_cf_item_asn(cf_item, item_id)
    else:
        return translate_cf_item_scd(cf_item, item_id)


def translate_cf_item_scd(cf_item: CFItem, item_id: str) -> Dict[str, Any]:
    """Translate CFItem to scd:CompetencyDefinition."""
    result = {
        "@id": item_id,
        "@type": "scd:CompetencyDefinition"
    }
    
    if cf_item.fullStatement:
        result["scd:statement"] = cf_item.fullStatement
    if cf_item.abbreviatedStatement:
        result["scd:abbreviatedStatement"] = cf_item.abbreviatedStatement
    if cf_item.alternativeLabel:
        result["scd:alternativeLabel"] = cf_item.alternativeLabel
    if cf_item.conceptKeywords:
        result["scd:conceptKeyword"] = cf_item.conceptKeywords
    if cf_item.hierarchyCode:
        result["scd:hierarchyCode"] = cf_item.hierarchyCode
    if cf_item.humanCodingScheme:
        result["scd:humanCodingScheme"] = cf_item.humanCodingScheme
    if cf_item.CFItemType:
        result["scd:competencyCategory"] = cf_item.CFItemType
    if cf_item.language:
        result["scd:language"] = cf_item.language
    if cf_item.educationLevel:
        result["scd:educationLevel"] = cf_item.educationLevel
    
    return result


def translate_cf_item_asn(cf_item: CFItem, item_id: str) -> Dict[str, Any]:
    """Translate CFItem to ceasn:Competency."""
    result = {
        "@id": item_id,
        "@type": "ceasn:Competency"
    }
    
    if cf_item.identifier:
        result["ceasn:identifier"] = item_id
    if cf_item.fullStatement:
        result["ceasn:competencyText"] = cf_item.fullStatement
    if cf_item.abbreviatedStatement:
        result["ceasn:competencyLabel"] = cf_item.abbreviatedStatement
    if cf_item.alternativeLabel:
        # ASN uses skos:altLabel
        result["skos:altLabel"] = cf_item.alternativeLabel
    if cf_item.conceptKeywords:
        result["ceasn:conceptKeyword"] = cf_item.conceptKeywords
    if cf_item.hierarchyCode:
        result["ceasn:codedNotation"] = cf_item.hierarchyCode
    if cf_item.humanCodingScheme:
        result["ceasn:codedNotation"] = cf_item.humanCodingScheme  # Could use altCodedNotation
    if cf_item.CFItemType:
        result["ceasn:competencyCategory"] = cf_item.CFItemType
    if cf_item.language:
        result["ceasn:inLanguage"] = cf_item.language
    if cf_item.educationLevel:
        result["ceasn:educationLevelType"] = cf_item.educationLevel  # Note: ASN expects skos:Concept
    
    return result


def translate_cf_association(
    cf_assoc: CFAssociation,
    base_iri: Optional[str] = None,
    target_format: str = "ieee_scd"
) -> List[Dict[str, Any]]:
    """Translate CFAssociation to target format. Returns list (ASN may create multiple statements)."""
    if target_format == "asn_ctdl":
        return translate_cf_association_asn(cf_assoc, base_iri)
    else:
        return [translate_cf_association_scd(cf_assoc, base_iri)]


def translate_cf_association_scd(cf_assoc: CFAssociation, base_iri: Optional[str] = None) -> Dict[str, Any]:
    """Translate CFAssociation to scd:ResourceAssociation."""
    assoc_id = get_iri(cf_assoc.identifier, cf_assoc.uri)
    if base_iri and not cf_assoc.uri:
        assoc_id = f"{base_iri}#{cf_assoc.identifier}"
    
    # Map association type
    scd_type = ASSOCIATION_TYPE_MAP_SCD.get(cf_assoc.associationType, cf_assoc.associationType)
    
    # Get origin and destination IRIs
    origin_id = get_iri(
        cf_assoc.originNodeURI.get("identifier", ""),
        cf_assoc.originNodeURI.get("uri")
    )
    if base_iri and not cf_assoc.originNodeURI.get("uri"):
        origin_id = f"{base_iri}#{cf_assoc.originNodeURI.get('identifier', '')}"
    
    dest_id = get_iri(
        cf_assoc.destinationNodeURI.get("identifier", ""),
        cf_assoc.destinationNodeURI.get("uri")
    )
    if base_iri and not cf_assoc.destinationNodeURI.get("uri"):
        dest_id = f"{base_iri}#{cf_assoc.destinationNodeURI.get('identifier', '')}"
    
    result = {
        "@id": assoc_id,
        "@type": "scd:ResourceAssociation",
        "scd:relationType": scd_type,
        "scd:sourceNode": {"@id": origin_id},
        "scd:targetNode": {"@id": dest_id}
    }
    
    if cf_assoc.sequenceNumber is not None:
        result["scd:sequenceNumber"] = cf_assoc.sequenceNumber
    if cf_assoc.lastChangeDateTime:
        result["scd:dateModified"] = cf_assoc.lastChangeDateTime
    
    return result


def translate_cf_association_asn(cf_assoc: CFAssociation, base_iri: Optional[str] = None) -> List[Dict[str, Any]]:
    """Translate CFAssociation to ASN-CTDL format. May return multiple statements."""
    # Get origin and destination IRIs
    origin_id = get_iri(
        cf_assoc.originNodeURI.get("identifier", ""),
        cf_assoc.originNodeURI.get("uri")
    )
    if base_iri and not cf_assoc.originNodeURI.get("uri"):
        origin_id = f"{base_iri}#{cf_assoc.originNodeURI.get('identifier', '')}"
    
    dest_id = get_iri(
        cf_assoc.destinationNodeURI.get("identifier", ""),
        cf_assoc.destinationNodeURI.get("uri")
    )
    if base_iri and not cf_assoc.destinationNodeURI.get("uri"):
        dest_id = f"{base_iri}#{cf_assoc.destinationNodeURI.get('identifier', '')}"
    
    results = []
    
    # ASN uses direct properties on Competency, not separate association objects
    if cf_assoc.associationType == "isChildOf":
        # Add isChildOf to origin competency (would need to update the competency)
        # For now, we'll create a statement that shows the relationship
        origin_competency = {
            "@id": origin_id,
            "ceasn:isChildOf": {"@id": dest_id}
        }
        results.append(origin_competency)
    elif cf_assoc.associationType == "precedes":
        # Use prerequisiteAlignment
        origin_competency = {
            "@id": origin_id,
            "ceasn:prerequisiteAlignment": {"@id": dest_id}
        }
        results.append(origin_competency)
    else:
        # For other types, add as comment/note
        origin_competency = {
            "@id": origin_id,
            "ceasn:comment": f"Association {cf_assoc.associationType} to {dest_id}"
        }
        results.append(origin_competency)
    
    return results


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web UI."""
    # Look for index.html in parent directory (root) for Vercel deployment
    html_path = Path(__file__).parent.parent / "index.html"
    if not html_path.exists():
        # Fallback to same directory
        html_path = Path(__file__).parent / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    return HTMLResponse(
        content="<h1>CASE to IEEE SCD Translator</h1><p>index.html not found. API available at <a href='/docs'>/docs</a></p>",
        status_code=404
    )


@app.get("/example_case.json")
async def example_case():
    """Serve the example CASE JSON file."""
    # Look for example_case.json in parent directory (root) for Vercel deployment
    json_path = Path(__file__).parent.parent / "example_case.json"
    if not json_path.exists():
        # Fallback to same directory
        json_path = Path(__file__).parent / "example_case.json"
    if json_path.exists():
        return FileResponse(json_path, media_type="application/json")
    raise HTTPException(status_code=404, detail="example_case.json not found")


@app.get("/field-mapping")
async def get_field_mapping():
    """
    Return comprehensive field mapping between CASE 1.1, IEEE SCD, and ASN-CTDL.
    Shows both mapped fields and unmapped fields for all three formats.
    """
    return {
        "cfDocument": [
            {
                "case_1_1_field": "identifier",
                "ieee_scd_field": "@id",
                "asn_ctdl_field": "ceasn:identifier (@id)",
                "mapped": True,
                "notes": "Used to generate @id IRI (same in both formats)"
            },
            {
                "case_1_1_field": "uri",
                "ieee_scd_field": "@id",
                "asn_ctdl_field": "@id",
                "mapped": True,
                "notes": "Used as @id IRI if provided (same in both formats)"
            },
            {
                "case_1_1_field": "title",
                "ieee_scd_field": "scd:name",
                "asn_ctdl_field": "ceasn:name",
                "mapped": True,
                "notes": "Direct mapping (same concept, different namespace)"
            },
            {
                "case_1_1_field": "description",
                "ieee_scd_field": "scd:description",
                "asn_ctdl_field": "ceasn:description",
                "mapped": True,
                "notes": "Direct mapping (same in both formats)"
            },
            {
                "case_1_1_field": "language",
                "ieee_scd_field": "scd:language",
                "asn_ctdl_field": "ceasn:inLanguage",
                "mapped": True,
                "notes": "IEEE SCD: language; ASN-CTDL: inLanguage"
            },
            {
                "case_1_1_field": "version",
                "ieee_scd_field": "scd:version",
                "asn_ctdl_field": None,
                "mapped": True,
                "notes": "IEEE SCD: version; ASN-CTDL: No direct equivalent"
            },
            {
                "case_1_1_field": "lastChangeDateTime",
                "ieee_scd_field": "scd:dateModified",
                "asn_ctdl_field": "ceasn:dateModified",
                "mapped": True,
                "notes": "Direct mapping (same in both formats)"
            },
            {
                "case_1_1_field": "publisher",
                "ieee_scd_field": "scd:publisher",
                "asn_ctdl_field": "ceasn:publisher",
                "mapped": True,
                "notes": "Direct mapping (object preserved as-is, same in both)"
            },
            {
                "case_1_1_field": "officialSourceURL",
                "ieee_scd_field": "scd:url",
                "asn_ctdl_field": "ceasn:source",
                "mapped": True,
                "notes": "IEEE SCD: url; ASN-CTDL: source"
            },
            {
                "case_1_1_field": "adoptionStatus",
                "ieee_scd_field": None,
                "asn_ctdl_field": "ceasn:publicationStatusType",
                "mapped": False,
                "notes": "IEEE SCD: No equivalent; ASN-CTDL: publicationStatusType"
            },
            {
                "case_1_1_field": "educationLevel",
                "ieee_scd_field": None,
                "asn_ctdl_field": "ceasn:educationLevelType",
                "mapped": False,
                "notes": "IEEE SCD: No equivalent at framework level; ASN-CTDL: educationLevelType"
            },
            {
                "case_1_1_field": "subject",
                "ieee_scd_field": None,
                "asn_ctdl_field": "ceasn:localSubject",
                "mapped": False,
                "notes": "IEEE SCD: No equivalent; ASN-CTDL: localSubject"
            },
            {
                "case_1_1_field": "rights",
                "ieee_scd_field": None,
                "asn_ctdl_field": "ceasn:rights",
                "mapped": False,
                "notes": "IEEE SCD: No equivalent; ASN-CTDL: rights"
            },
            {
                "case_1_1_field": "license",
                "ieee_scd_field": None,
                "asn_ctdl_field": "ceasn:license",
                "mapped": False,
                "notes": "IEEE SCD: No equivalent; ASN-CTDL: license"
            },
            {
                "case_1_1_field": "notes",
                "ieee_scd_field": None,
                "asn_ctdl_field": "ceasn:comment",
                "mapped": False,
                "notes": "IEEE SCD: No equivalent; ASN-CTDL: comment"
            }
        ],
        "cfItem": [
            {
                "case_1_1_field": "identifier",
                "ieee_scd_field": "@id",
                "mapped": True,
                "notes": "Used to generate @id IRI"
            },
            {
                "case_1_1_field": "uri",
                "ieee_scd_field": "@id",
                "mapped": True,
                "notes": "Used as @id IRI if provided"
            },
            {
                "case_1_1_field": "fullStatement",
                "ieee_scd_field": "scd:statement",
                "asn_ctdl_field": "ceasn:competencyText",
                "mapped": True,
                "notes": "IEEE SCD: statement; ASN-CTDL: competencyText"
            },
            {
                "case_1_1_field": "abbreviatedStatement",
                "ieee_scd_field": "scd:abbreviatedStatement",
                "asn_ctdl_field": "ceasn:competencyLabel",
                "mapped": True,
                "notes": "IEEE SCD: abbreviatedStatement; ASN-CTDL: competencyLabel"
            },
            {
                "case_1_1_field": "alternativeLabel",
                "ieee_scd_field": "scd:alternativeLabel",
                "asn_ctdl_field": "skos:altLabel",
                "mapped": True,
                "notes": "IEEE SCD: alternativeLabel; ASN-CTDL: skos:altLabel"
            },
            {
                "case_1_1_field": "conceptKeywords",
                "ieee_scd_field": "scd:conceptKeyword",
                "asn_ctdl_field": "ceasn:conceptKeyword",
                "mapped": True,
                "notes": "Direct mapping (same in both formats, array)"
            },
            {
                "case_1_1_field": "hierarchyCode",
                "ieee_scd_field": "scd:hierarchyCode",
                "asn_ctdl_field": "ceasn:codedNotation",
                "mapped": True,
                "notes": "IEEE SCD: hierarchyCode; ASN-CTDL: codedNotation"
            },
            {
                "case_1_1_field": "humanCodingScheme",
                "ieee_scd_field": "scd:humanCodingScheme",
                "asn_ctdl_field": "ceasn:codedNotation",
                "mapped": True,
                "notes": "IEEE SCD: humanCodingScheme; ASN-CTDL: codedNotation (or altCodedNotation)"
            },
            {
                "case_1_1_field": "CFItemType",
                "ieee_scd_field": "scd:competencyCategory",
                "asn_ctdl_field": "ceasn:competencyCategory",
                "mapped": True,
                "notes": "Direct mapping (same in both formats)"
            },
            {
                "case_1_1_field": "language",
                "ieee_scd_field": "scd:language",
                "asn_ctdl_field": "ceasn:inLanguage",
                "mapped": True,
                "notes": "IEEE SCD: language; ASN-CTDL: inLanguage"
            },
            {
                "case_1_1_field": "educationLevel",
                "ieee_scd_field": "scd:educationLevel",
                "asn_ctdl_field": "ceasn:educationLevelType",
                "mapped": True,
                "notes": "IEEE SCD: educationLevel; ASN-CTDL: educationLevelType (expects skos:Concept)"
            },
            {
                "case_1_1_field": "conceptKeywordsUri",
                "ieee_scd_field": None,
                "asn_ctdl_field": "ceasn:conceptTerm",
                "mapped": False,
                "notes": "IEEE SCD: No equivalent; ASN-CTDL: conceptTerm (skos:Concept)"
            },
            {
                "case_1_1_field": "notes",
                "ieee_scd_field": None,
                "asn_ctdl_field": "ceasn:comment",
                "mapped": False,
                "notes": "IEEE SCD: No equivalent; ASN-CTDL: comment"
            }
        ],
        "cfAssociation": [
            {
                "case_1_1_field": "identifier",
                "ieee_scd_field": "@id",
                "mapped": True,
                "notes": "Used to generate @id IRI"
            },
            {
                "case_1_1_field": "uri",
                "ieee_scd_field": "@id",
                "mapped": True,
                "notes": "Used as @id IRI if provided"
            },
            {
                "case_1_1_field": "associationType (isChildOf)",
                "ieee_scd_field": "scd:relationType = hasPart",
                "asn_ctdl_field": "ceasn:isChildOf (property on Competency)",
                "mapped": True,
                "notes": "IEEE SCD: hasPart (separate ResourceAssociation); ASN-CTDL: isChildOf (direct property)"
            },
            {
                "case_1_1_field": "associationType (precedes)",
                "ieee_scd_field": "scd:relationType = precedes",
                "asn_ctdl_field": "ceasn:prerequisiteAlignment",
                "mapped": True,
                "notes": "IEEE SCD: precedes; ASN-CTDL: prerequisiteAlignment"
            },
            {
                "case_1_1_field": "associationType (hasSkillLevel)",
                "ieee_scd_field": "scd:relationType = competencyLevel",
                "asn_ctdl_field": "asn:hasProgressionLevel",
                "mapped": True,
                "notes": "IEEE SCD: competencyLevel; ASN-CTDL: hasProgressionLevel (references progression model)"
            },
            {
                "case_1_1_field": "associationType (other)",
                "ieee_scd_field": "scd:relationType",
                "asn_ctdl_field": "Various alignment properties (alignTo, alignFrom, etc.)",
                "mapped": True,
                "notes": "IEEE SCD: Unmapped types pass through; ASN-CTDL: Various alignment properties available"
            },
            {
                "case_1_1_field": "originNodeURI",
                "ieee_scd_field": "scd:sourceNode.@id",
                "asn_ctdl_field": "Property on origin Competency",
                "mapped": True,
                "notes": "IEEE SCD: sourceNode in ResourceAssociation; ASN-CTDL: Direct property on Competency"
            },
            {
                "case_1_1_field": "destinationNodeURI",
                "ieee_scd_field": "scd:targetNode.@id",
                "asn_ctdl_field": "Value of property on origin Competency",
                "mapped": True,
                "notes": "IEEE SCD: targetNode in ResourceAssociation; ASN-CTDL: Value of relationship property"
            },
            {
                "case_1_1_field": "sequenceNumber",
                "ieee_scd_field": "scd:sequenceNumber",
                "asn_ctdl_field": "ceasn:listID",
                "mapped": True,
                "notes": "IEEE SCD: sequenceNumber; ASN-CTDL: listID (alphanumeric position)"
            },
            {
                "case_1_1_field": "lastChangeDateTime",
                "ieee_scd_field": "scd:dateModified",
                "asn_ctdl_field": "ceasn:dateModified",
                "mapped": True,
                "notes": "Direct mapping (same in both formats)"
            },
            {
                "case_1_1_field": "CFDocumentURI",
                "ieee_scd_field": None,
                "asn_ctdl_field": "ceasn:isPartOf",
                "mapped": False,
                "notes": "IEEE SCD: No equivalent; ASN-CTDL: isPartOf (framework reference)"
            }
        ],
        "format_specific": [
            {
                "case_1_1_field": None,
                "ieee_scd_field": "@type",
                "asn_ctdl_field": "@type",
                "mapped": False,
                "notes": "Both formats add @type: SCD (scd:CompetencyFramework, scd:CompetencyDefinition, scd:ResourceAssociation); ASN (ceasn:CompetencyFramework, ceasn:Competency)"
            },
            {
                "case_1_1_field": None,
                "ieee_scd_field": "@context",
                "asn_ctdl_field": "@context",
                "mapped": False,
                "notes": "Both formats add @context: SCD uses scd namespace; ASN uses ceasn and skos namespaces"
            },
            {
                "case_1_1_field": None,
                "ieee_scd_field": "@graph",
                "asn_ctdl_field": "@graph",
                "mapped": False,
                "notes": "Both formats use @graph to contain all translated entities"
            },
            {
                "case_1_1_field": None,
                "ieee_scd_field": "scd:ResourceAssociation",
                "asn_ctdl_field": None,
                "mapped": False,
                "notes": "IEEE SCD: Separate association objects; ASN-CTDL: Relationships are direct properties on Competency"
            },
            {
                "case_1_1_field": None,
                "ieee_scd_field": None,
                "asn_ctdl_field": "ceasn:hasChild",
                "mapped": False,
                "notes": "ASN-CTDL only: Inverse of isChildOf, indicates child competencies"
            },
            {
                "case_1_1_field": None,
                "ieee_scd_field": None,
                "asn_ctdl_field": "ceasn:alignTo / ceasn:alignFrom",
                "mapped": False,
                "notes": "ASN-CTDL only: Alignment properties for equivalency assertions"
            }
        ]
    }


def detect_file_format(filename: str) -> str:
    """Detect file format based on file extension."""
    filename_lower = filename.lower()
    if filename_lower.endswith(('.json', '.jsonld')):
        return 'json'
    elif filename_lower.endswith(('.csv',)):
        return 'csv'
    elif filename_lower.endswith(('.xlsx', '.xls')):
        return 'excel'
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported formats: .json, .csv, .xlsx, .xls"
        )


def convert_csv_to_case(content: bytes, filename: str) -> Dict[str, Any]:
    """Convert CSV file to CASE format."""
    if not PANDAS_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="CSV support requires pandas library. Please install: pip install pandas"
        )
    
    try:
        # Read CSV into pandas DataFrame
        df = pd.read_csv(io.BytesIO(content))
        
        # Expected CSV columns (flexible - will use what's available):
        # Required: identifier, title (for CFDocument)
        # Optional: fullStatement, abbreviatedStatement, etc. (for CFItems)
        
        # Check if this is a framework document or items list
        if 'CFDocument' in df.columns or all(col in df.columns for col in ['identifier', 'title']):
            # This looks like a framework document row
            doc_row = df.iloc[0] if len(df) > 0 else {}
            cf_document = {
                "identifier": str(doc_row.get('identifier', doc_row.get('CFDocument.identifier', 'framework-001'))),
                "title": str(doc_row.get('title', doc_row.get('CFDocument.title', 'Untitled Framework')))
            }
            
            # Add optional fields if present
            for field in ['description', 'language', 'version', 'lastChangeDateTime', 'officialSourceURL']:
                if field in doc_row and pd.notna(doc_row[field]):
                    cf_document[field] = str(doc_row[field])
        else:
            # Default framework document
            cf_document = {
                "identifier": "csv-import-001",
                "title": filename.replace('.csv', '')
            }
        
        # Convert rows to CFItems
        cf_items = []
        for idx, row in df.iterrows():
            if 'identifier' in row and pd.notna(row.get('identifier')):
                item = {
                    "identifier": str(row['identifier'])
                }
                
                # Map common CSV columns to CFItem fields
                field_mapping = {
                    'fullStatement': 'fullStatement',
                    'statement': 'fullStatement',
                    'abbreviatedStatement': 'abbreviatedStatement',
                    'label': 'abbreviatedStatement',
                    'CFItemType': 'CFItemType',
                    'type': 'CFItemType',
                    'hierarchyCode': 'hierarchyCode',
                    'code': 'hierarchyCode',
                    'description': 'notes',
                    'notes': 'notes'
                }
                
                for csv_col, case_field in field_mapping.items():
                    if csv_col in row and pd.notna(row[csv_col]):
                        item[case_field] = str(row[csv_col])
                
                cf_items.append(item)
        
        return {
            "CFDocument": cf_document,
            "CFItems": cf_items,
            "CFAssociations": []
        }
    except Exception as e:
        logger.error(f"CSV conversion error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error converting CSV to CASE format: {str(e)}"
        )


def convert_excel_to_case(content: bytes, filename: str) -> Dict[str, Any]:
    """Convert Excel file to CASE format."""
    if not PANDAS_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Excel support requires pandas and openpyxl libraries. Please install: pip install pandas openpyxl"
        )
    
    try:
        # Read Excel file - try to read multiple sheets
        excel_file = pd.ExcelFile(io.BytesIO(content))
        
        # Look for sheets named 'CFDocument', 'CFItems', 'CFAssociations' or use first sheet
        cf_document_data = None
        cf_items_data = None
        cf_associations_data = None
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            if sheet_name.lower() in ['cfdocument', 'document', 'framework']:
                cf_document_data = df
            elif sheet_name.lower() in ['cfitems', 'items', 'competencies', 'skills']:
                cf_items_data = df
            elif sheet_name.lower() in ['cfassociations', 'associations', 'relationships']:
                cf_associations_data = df
        
        # If no named sheets found, use first sheet for items
        if cf_items_data is None and len(excel_file.sheet_names) > 0:
            cf_items_data = pd.read_excel(excel_file, sheet_name=excel_file.sheet_names[0])
        
        # Build CFDocument
        if cf_document_data is not None and len(cf_document_data) > 0:
            doc_row = cf_document_data.iloc[0]
            cf_document = {
                "identifier": str(doc_row.get('identifier', 'excel-import-001')),
                "title": str(doc_row.get('title', filename.replace('.xlsx', '').replace('.xls', '')))
            }
            
            for field in ['description', 'language', 'version', 'lastChangeDateTime', 'officialSourceURL']:
                if field in doc_row and pd.notna(doc_row[field]):
                    cf_document[field] = str(doc_row[field])
        else:
            cf_document = {
                "identifier": "excel-import-001",
                "title": filename.replace('.xlsx', '').replace('.xls', '')
            }
        
        # Build CFItems
        cf_items = []
        if cf_items_data is not None:
            for idx, row in cf_items_data.iterrows():
                if 'identifier' in row and pd.notna(row.get('identifier')):
                    item = {"identifier": str(row['identifier'])}
                    
                    field_mapping = {
                        'fullStatement': 'fullStatement',
                        'statement': 'fullStatement',
                        'abbreviatedStatement': 'abbreviatedStatement',
                        'label': 'abbreviatedStatement',
                        'CFItemType': 'CFItemType',
                        'type': 'CFItemType',
                        'hierarchyCode': 'hierarchyCode',
                        'code': 'hierarchyCode'
                    }
                    
                    for excel_col, case_field in field_mapping.items():
                        if excel_col in row and pd.notna(row[excel_col]):
                            item[case_field] = str(row[excel_col])
                    
                    cf_items.append(item)
        
        # Build CFAssociations
        cf_associations = []
        if cf_associations_data is not None:
            for idx, row in cf_associations_data.iterrows():
                if all(col in row for col in ['identifier', 'associationType', 'originNodeURI', 'destinationNodeURI']):
                    assoc = {
                        "identifier": str(row['identifier']),
                        "associationType": str(row['associationType']),
                        "originNodeURI": {
                            "identifier": str(row.get('originNodeURI', row.get('originIdentifier', '')))
                        },
                        "destinationNodeURI": {
                            "identifier": str(row.get('destinationNodeURI', row.get('destinationIdentifier', '')))
                        }
                    }
                    cf_associations.append(assoc)
        
        return {
            "CFDocument": cf_document,
            "CFItems": cf_items,
            "CFAssociations": cf_associations
        }
    except Exception as e:
        logger.error(f"Excel conversion error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error converting Excel to CASE format: {str(e)}"
        )


def parse_uploaded_file(content: bytes, filename: str, file_format: Optional[str] = None) -> Dict[str, Any]:
    """Parse uploaded file and convert to CASE format."""
    if file_format is None:
        file_format = detect_file_format(filename)
    
    if file_format == 'json':
        try:
            return json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON in file: {str(e)}")
        except UnicodeDecodeError as e:
            raise HTTPException(status_code=400, detail=f"File encoding error: {str(e)}")
    elif file_format == 'csv':
        return convert_csv_to_case(content, filename)
    elif file_format == 'excel':
        return convert_excel_to_case(content, filename)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file_format}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "CASE to IEEE SCD Translator"}


def translate_case_document(case_input: CASEInput, target_format: str = "ieee_scd"):
    """Common translation logic for both formats."""
    start_time = time.time()
    
    logger.info(f"Starting CASE to {target_format.upper()} translation")
    
    # Extract base IRI from CFDocument if available
    base_iri = case_input.CFDocument.uri or f"#{case_input.CFDocument.identifier}"
    if base_iri.startswith("#"):
        base_iri = base_iri[1:] if len(base_iri) > 1 else None
    
    # Translate CFDocument
    logger.info(f"Translating CFDocument: {case_input.CFDocument.identifier}")
    framework = translate_cf_document(case_input.CFDocument, target_format)
    
    # Translate CFItems
    num_items = len(case_input.CFItems)
    logger.info(f"Translating {num_items} CFItems")
    competencies = [
        translate_cf_item(item, base_iri, target_format) for item in case_input.CFItems
    ]
    logger.info(f"Successfully processed {num_items} CFItems")
    
    # Translate CFAssociations
    num_associations = len(case_input.CFAssociations)
    logger.info(f"Translating {num_associations} CFAssociations")
    association_results = []
    for assoc in case_input.CFAssociations:
        assoc_translations = translate_cf_association(assoc, base_iri, target_format)
        association_results.extend(assoc_translations)
    logger.info(f"Successfully processed {num_associations} CFAssociations")
    
    # Build context based on target format
    if target_format == "asn_ctdl":
        context = {
            "ceasn": "https://purl.org/ctdlasn/terms/",
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "@vocab": "https://purl.org/ctdlasn/terms/"
        }
    else:
        context = {
            "scd": "https://w3id.org/skill-credential/",
            "@vocab": "https://w3id.org/skill-credential/"
        }
    
    # For ASN-CTDL, associations are embedded in competencies, so we need to merge
    if target_format == "asn_ctdl":
        # Create a map of competencies by ID
        competency_map = {comp["@id"]: comp for comp in competencies}
        
        # Merge association data into competencies
        for assoc_data in association_results:
            comp_id = assoc_data["@id"]
            if comp_id in competency_map:
                # Merge properties
                for key, value in assoc_data.items():
                    if key != "@id" and key != "@type":
                        if key in competency_map[comp_id]:
                            # Handle multiple values
                            if not isinstance(competency_map[comp_id][key], list):
                                competency_map[comp_id][key] = [competency_map[comp_id][key]]
                            if isinstance(value, list):
                                competency_map[comp_id][key].extend(value)
                            else:
                                competency_map[comp_id][key].append(value)
                        else:
                            competency_map[comp_id][key] = value
        
        competencies = list(competency_map.values())
        graph = [framework] + competencies
    else:
        graph = [framework] + competencies + association_results
    
    # Build the final JSON-LD document
    result = {
        "@context": context,
        "@graph": graph
    }
    
    elapsed_time = time.time() - start_time
    logger.info(f"Translation completed in {elapsed_time:.3f} seconds")
    logger.info(f"Summary: {num_items} items, {num_associations} associations processed")
    
    return result


@app.post("/translate/case-to-ieee")
async def translate_case_to_ieee(case_input: CASEInput):
    """
    Translate a CASE JSON document to IEEE SCD JSON-LD format.
    
    Accepts a full CASE document with CFDocument, CFItems, and CFAssociations.
    Returns a JSON-LD document with @context and @graph containing the translated data.
    """
    try:
        return translate_case_document(case_input, "ieee_scd")
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Translation error: {str(e)}")


@app.post("/translate/case-to-asn")
async def translate_case_to_asn(case_input: CASEInput):
    """
    Translate a CASE JSON document to ASN-CTDL JSON-LD format.
    
    Accepts a full CASE document with CFDocument, CFItems, and CFAssociations.
    Returns a JSON-LD document with @context and @graph containing the translated data.
    """
    try:
        return translate_case_document(case_input, "asn_ctdl")
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Translation error: {str(e)}")


@app.post("/translate/upload-file")
async def translate_uploaded_file(
    file: UploadFile = File(..., description="Input file to translate (JSON, CSV, or Excel)"),
    target_format: str = Form("ieee_scd", description="Target format: 'ieee_scd' or 'asn_ctdl'"),
    input_format: Optional[str] = Form(None, description="Input format override: 'json', 'csv', or 'excel' (auto-detected if not specified)")
):
    """
    Translate an input file to IEEE SCD or ASN-CTDL JSON-LD format.
    
    Accepts multiple file formats:
    - JSON: CASE 1.1 format (.json)
    - CSV: Tabular data with columns for competencies (.csv)
    - Excel: Multi-sheet workbook with CFDocument, CFItems, CFAssociations sheets (.xlsx, .xls)
    
    Returns a JSON-LD document with @context and @graph containing the translated data.
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Read file content
        content = await file.read()
        
        # Detect or use specified format
        detected_format = input_format or detect_file_format(file.filename)
        
        # Parse file based on format
        try:
            case_data = parse_uploaded_file(content, file.filename, detected_format)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"File parsing error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail=f"Error parsing {detected_format.upper()} file: {str(e)}"
            )
        
        # Validate target format
        if target_format not in ["ieee_scd", "asn_ctdl"]:
            raise HTTPException(status_code=400, detail="target_format must be 'ieee_scd' or 'asn_ctdl'")
        
        # Parse as CASEInput
        try:
            case_input = CASEInput(**case_data)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid CASE document structure after conversion: {str(e)}. Please check your input file format."
            )
        
        # Translate
        result = translate_case_document(case_input, target_format)
        
        # Return result
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File translation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

