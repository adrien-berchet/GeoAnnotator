/**
 * Modal component for displaying detailed format information.
 * Shows schema, structure, and examples for each export/import format.
 */

import React from "react";
import "./FormatDetailsModal.css";

export type FormatType = "geojson" | "gpx" | "kml" | "csv" | "zip";

interface FormatDetailsModalProps {
  format: FormatType | null;
  onClose: () => void;
}

interface FormatDetail {
  name: string;
  description: string;
  schema: string;
  example?: string;
  isBinary?: boolean;
}

const FORMAT_DETAILS: Record<FormatType, FormatDetail> = {
  geojson: {
    name: "GeoJSON",
    description:
      "Standard geographic data interchange format based on JSON. Supports all point data, tags, point types, and annotation metadata.",
    schema: `{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "point-uuid",
      "geometry": {
        "type": "Point",
        "coordinates": [longitude, latitude]
      },
      "properties": {
        "title": "string",
        "description": "string",
        "is_public": boolean,
        "owner": "username",
        "tags": ["tag1", "tag2"],
        "point_type": "type-name",
        "point_type_icon": "icon-name",
        "created_at": "ISO-8601-datetime",
        "updated_at": "ISO-8601-datetime",
        "annotations": [
          {
            "id": "annotation-uuid",
            "type": "text|image|document",
            "text_content": "string (for text annotations)",
            "file_name": "filename (for file annotations)",
            "created_at": "ISO-8601-datetime"
          }
        ]
      }
    }
  ]
}`,
    example: `{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "geometry": {
        "type": "Point",
        "coordinates": [2.3522, 48.8566]
      },
      "properties": {
        "title": "Eiffel Tower",
        "description": "Iconic iron lattice tower in Paris",
        "is_public": true,
        "owner": "johndoe",
        "tags": ["landmark", "paris", "tourism"],
        "point_type": "Monument",
        "point_type_icon": "monument",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "annotations": [
          {
            "id": "660e8400-e29b-41d4-a716-446655440001",
            "type": "text",
            "text_content": "Visited on a sunny day!",
            "file_name": null,
            "created_at": "2024-01-15T11:00:00Z"
          }
        ]
      }
    }
  ]
}`,
  },
  gpx: {
    name: "GPX",
    description:
      "GPS Exchange Format - XML-based format compatible with most GPS devices and mapping software. Contains waypoints with basic point information.",
    schema: `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="GeoAnnotator">
  <metadata>
    <name>Export name</name>
    <desc>Description</desc>
    <time>ISO-8601-datetime</time>
  </metadata>
  <wpt lat="latitude" lon="longitude">
    <name>Point title</name>
    <desc>Point description</desc>
    <time>ISO-8601-datetime</time>
  </wpt>
  <!-- More waypoints... -->
</gpx>`,
    example: `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="GeoAnnotator">
  <metadata>
    <name>GeoAnnotator Export</name>
    <desc>Exported 1 points from GeoAnnotator</desc>
    <time>2024-01-15T10:30:00Z</time>
  </metadata>
  <wpt lat="48.8566" lon="2.3522">
    <name>Eiffel Tower</name>
    <desc>Iconic iron lattice tower in Paris</desc>
    <time>2024-01-15T10:30:00Z</time>
  </wpt>
</gpx>`,
  },
  kml: {
    name: "KML",
    description:
      "Keyhole Markup Language - Google Earth format. Great for visualization in Google Earth and Google Maps. Supports extended data for additional properties.",
    schema: `<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Point title</name>
      <description>Point description</description>
      <Point>
        <coordinates>longitude,latitude,0</coordinates>
      </Point>
      <ExtendedData>
        <Data name="owner">
          <value>username</value>
        </Data>
        <Data name="is_public">
          <value>true/false</value>
        </Data>
        <Data name="tags">
          <value>tag1, tag2</value>
        </Data>
        <Data name="point_type">
          <value>type-name</value>
        </Data>
      </ExtendedData>
    </Placemark>
  </Document>
</kml>`,
    example: `<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Eiffel Tower</name>
      <description>Iconic iron lattice tower in Paris</description>
      <Point>
        <coordinates>2.3522,48.8566,0</coordinates>
      </Point>
      <ExtendedData>
        <Data name="owner">
          <value>johndoe</value>
        </Data>
        <Data name="is_public">
          <value>true</value>
        </Data>
        <Data name="tags">
          <value>landmark, paris, tourism</value>
        </Data>
        <Data name="point_type">
          <value>Monument</value>
        </Data>
      </ExtendedData>
    </Placemark>
  </Document>
</kml>`,
  },
  csv: {
    name: "CSV",
    description:
      "Comma-Separated Values - Simple spreadsheet format. Easy to edit in Excel, Google Sheets, or any text editor. Tags are separated by pipe (|) characters.",
    schema: `id,title,description,latitude,longitude,is_public,owner,tags,point_type,created_at,updated_at
uuid,string,string,decimal,decimal,boolean,string,tag1|tag2,string,ISO-8601,ISO-8601`,
    example: `id,title,description,latitude,longitude,is_public,owner,tags,point_type,created_at,updated_at
550e8400-e29b-41d4-a716-446655440000,Eiffel Tower,Iconic iron lattice tower in Paris,48.8566,2.3522,True,johndoe,landmark|paris|tourism,Monument,2024-01-15T10:30:00Z,2024-01-15T10:30:00Z`,
  },
  zip: {
    name: "ZIP Archive",
    description:
      "Complete backup archive containing GeoJSON data and all annotation files (images, documents, etc.). This is the recommended format for backing up your data with all attachments.",
    schema: `Archive structure:
├── points.geojson          # GeoJSON file with all point data
└── annotations/            # Folder containing annotation files
    ├── {point-id}/         # Subfolder per point
    │   ├── image1.jpg      # Image annotations
    │   ├── document.pdf    # Document annotations
    │   └── ...
    └── ...

The points.geojson file follows the same schema as the GeoJSON format,
with file references in the annotations array pointing to files in the
annotations/ directory.`,
    isBinary: true,
  },
};

export function FormatDetailsModal({
  format,
  onClose,
}: FormatDetailsModalProps) {
  if (!format) return null;

  const details = FORMAT_DETAILS[format];

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      onClose();
    }
  };

  return (
    <div
      className="format-modal-backdrop"
      onClick={handleBackdropClick}
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-labelledby="format-modal-title"
    >
      <div className="format-modal">
        <div className="format-modal-header">
          <h2 id="format-modal-title">{details.name} Format</h2>
          <button
            onClick={onClose}
            className="format-modal-close"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        <div className="format-modal-content">
          <section className="format-section">
            <h3>Description</h3>
            <p>{details.description}</p>
          </section>

          <section className="format-section">
            <h3>{details.isBinary ? "Structure" : "Schema"}</h3>
            <pre className="format-code">
              <code>{details.schema}</code>
            </pre>
          </section>

          {details.example && !details.isBinary && (
            <section className="format-section">
              <h3>Example</h3>
              <pre className="format-code">
                <code>{details.example}</code>
              </pre>
            </section>
          )}

          {details.isBinary && (
            <section className="format-section format-note">
              <p>
                <strong>Note:</strong> ZIP is a binary archive format. Code
                examples are not applicable. The archive contains a GeoJSON file
                and associated annotation files organized in a directory
                structure as shown above.
              </p>
            </section>
          )}
        </div>

        <div className="format-modal-footer">
          <button onClick={onClose} className="btn btn-primary">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
