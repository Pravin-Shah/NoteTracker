"""
Export data to PDF, CSV, JSON formats.
"""

import json
import csv
from typing import List, Dict
from io import BytesIO, StringIO
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def export_to_csv(data: List[Dict], filename: str = None) -> bytes:
    """
    Export data to CSV.

    Args:
        data: List of dictionaries
        filename: Output filename (for reference only)

    Returns:
        CSV bytes
    """
    if not data:
        logger.warning("No data to export to CSV")
        return b""

    try:
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

        csv_bytes = output.getvalue().encode('utf-8')
        logger.info(f"Data exported to CSV: {len(data)} rows")
        return csv_bytes
    except Exception as e:
        logger.error(f"Failed to export to CSV: {e}")
        raise


def export_to_json(data: List[Dict], filename: str = None, pretty: bool = True) -> bytes:
    """
    Export data to JSON.

    Args:
        data: List of dictionaries
        filename: Output filename (for reference only)
        pretty: Pretty-print JSON

    Returns:
        JSON bytes
    """
    if not data:
        logger.warning("No data to export to JSON")
        return b"[]"

    try:
        if pretty:
            json_str = json.dumps(data, indent=2, default=str)
        else:
            json_str = json.dumps(data, default=str)

        json_bytes = json_str.encode('utf-8')
        logger.info(f"Data exported to JSON: {len(data)} records")
        return json_bytes
    except Exception as e:
        logger.error(f"Failed to export to JSON: {e}")
        raise


def export_to_pdf(data: List[Dict], title: str = "Report", filename: str = None) -> bytes:
    """
    Export data to PDF. Requires reportlab.

    Args:
        data: List of dictionaries
        title: Report title
        filename: Output filename (for reference only)

    Returns:
        PDF bytes
    """
    if not data:
        logger.warning("No data to export to PDF")
        return b""

    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []

        # Title
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=12
        )
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 0.2*inch))

        # Data Table
        if data:
            headers = list(data[0].keys())
            table_data = [headers]

            for row in data:
                row_data = []
                for header in headers:
                    value = row.get(header, '')
                    # Truncate long values
                    if isinstance(value, str) and len(str(value)) > 50:
                        value = str(value)[:47] + "..."
                    row_data.append(str(value))
                table_data.append(row_data)

            # Create table
            table = Table(table_data, repeatRows=1)

            # Style table
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))

            elements.append(table)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        logger.info(f"Data exported to PDF: {len(data)} records in '{title}'")
        return pdf_bytes

    except ImportError:
        logger.error("reportlab not installed - PDF export not available")
        raise Exception("reportlab library is required for PDF export. Install with: pip install reportlab")
    except Exception as e:
        logger.error(f"Failed to export to PDF: {e}")
        raise


def export_to_file(
    data: List[Dict],
    filepath: str,
    format: str = 'json'
) -> None:
    """
    Export data to file.

    Args:
        data: List of dictionaries
        filepath: Output file path
        format: 'json', 'csv', or 'pdf'

    Raises:
        ValueError: If format is invalid
    """
    if format not in ['json', 'csv', 'pdf']:
        raise ValueError(f"Unsupported format: {format}")

    try:
        if format == 'json':
            content = export_to_json(data)
        elif format == 'csv':
            content = export_to_csv(data)
        else:  # pdf
            content = export_to_pdf(data, title="Export")

        # Write to file
        Path(filepath).write_bytes(content)
        logger.info(f"Data exported to {filepath}")
    except Exception as e:
        logger.error(f"Failed to export to file: {e}")
        raise


def import_from_json(filepath: str) -> List[Dict]:
    """
    Import data from JSON file.

    Args:
        filepath: JSON file path

    Returns:
        List of dictionaries
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        logger.info(f"Data imported from JSON: {len(data)} records")
        return data if isinstance(data, list) else [data]
    except Exception as e:
        logger.error(f"Failed to import from JSON: {e}")
        raise


def import_from_csv(filepath: str) -> List[Dict]:
    """
    Import data from CSV file.

    Args:
        filepath: CSV file path

    Returns:
        List of dictionaries
    """
    try:
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(dict(row))
        logger.info(f"Data imported from CSV: {len(data)} records")
        return data
    except Exception as e:
        logger.error(f"Failed to import from CSV: {e}")
        raise


def batch_export(
    datasets: Dict[str, List[Dict]],
    output_dir: str,
    format: str = 'json'
) -> None:
    """
    Export multiple datasets at once.

    Args:
        datasets: Dict of {name: data_list}
        output_dir: Output directory
        format: Export format ('json', 'csv', 'pdf')
    """
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        for name, data in datasets.items():
            filename = f"{name}.{format}"
            filepath = Path(output_dir) / filename
            export_to_file(data, str(filepath), format)

        logger.info(f"Batch export completed: {len(datasets)} files in {output_dir}")
    except Exception as e:
        logger.error(f"Batch export failed: {e}")
        raise
