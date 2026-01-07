#!/usr/bin/env python3
"""
Generate CSV files from field mapping data.
This script extracts the field mapping data and creates CSV files that can be viewed in GitHub.
"""

import csv
import json
from pathlib import Path

# Field mapping data (extracted from api/main.py)
FIELD_MAPPING_DATA = {
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
            "asn_ctdl_field": None,
            "mapped": True,
            "notes": "Used to generate @id IRI"
        },
        {
            "case_1_1_field": "uri",
            "ieee_scd_field": "@id",
            "asn_ctdl_field": None,
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
            "asn_ctdl_field": None,
            "mapped": True,
            "notes": "Used to generate @id IRI"
        },
        {
            "case_1_1_field": "uri",
            "ieee_scd_field": "@id",
            "asn_ctdl_field": None,
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


def write_csv_file(data: list, filename: str, entity_type: str):
    """Write field mapping data to a CSV file."""
    if not data:
        return
    
    # Prepare CSV rows
    rows = []
    for item in data:
        row = {
            "Entity Type": entity_type,
            "CASE 1.1 Field": item.get("case_1_1_field") or "",
            "IEEE SCD Field": item.get("ieee_scd_field") or "",
            "ASN-CTDL Field": item.get("asn_ctdl_field") or "",
            "Mapped": "Yes" if item.get("mapped") else "No",
            "Notes": item.get("notes") or ""
        }
        rows.append(row)
    
    # Write to CSV
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["Entity Type", "CASE 1.1 Field", "IEEE SCD Field", "ASN-CTDL Field", "Mapped", "Notes"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Created {filename} with {len(rows)} rows")


def main():
    """Generate CSV files for field mappings."""
    # Create combined CSV with all mappings
    all_rows = []
    
    entity_type_map = {
        "cfDocument": "CFDocument → scd:CompetencyFramework / ceasn:CompetencyFramework",
        "cfItem": "CFItem → scd:CompetencyDefinition / ceasn:Competency",
        "cfAssociation": "CFAssociation → scd:ResourceAssociation / ceasn:Competency Properties",
        "format_specific": "Format-Specific Fields (Added by Translator)"
    }
    
    for key, entity_type in entity_type_map.items():
        for item in FIELD_MAPPING_DATA[key]:
            row = {
                "Entity Type": entity_type,
                "CASE 1.1 Field": item.get("case_1_1_field") or "",
                "IEEE SCD Field": item.get("ieee_scd_field") or "",
                "ASN-CTDL Field": item.get("asn_ctdl_field") or "",
                "Mapped": "Yes" if item.get("mapped") else "No",
                "Notes": item.get("notes") or ""
            }
            all_rows.append(row)
    
    # Write combined CSV
    combined_filename = "field_mapping.csv"
    with open(combined_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["Entity Type", "CASE 1.1 Field", "IEEE SCD Field", "ASN-CTDL Field", "Mapped", "Notes"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"Created {combined_filename} with {len(all_rows)} total rows")
    print("\nField mapping CSV files generated successfully!")
    print(f"View the file in GitHub: {combined_filename}")


if __name__ == "__main__":
    main()

