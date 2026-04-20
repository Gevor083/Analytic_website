"""
Export views: PDF report, CSV/JSON/XLSX download.
"""

import io
import json
import logging

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from ..models import ProcessedData, UploadedFile

logger = logging.getLogger(__name__)


def _check_ownership(request, file_obj):
    """Return True if the current user may access the file."""
    if request.user.is_staff or request.user.is_superuser:
        return True
    return file_obj.user == request.user


@login_required
def generate_pdf_report_view(request, file_id):
    """Generate and stream a PDF analytics report."""
    file_obj = get_object_or_404(UploadedFile, id=file_id)

    if not _check_ownership(request, file_obj):
        return HttpResponse("Permission denied.", status=403)

    if not file_obj.processed:
        return HttpResponse("File is still being processed.", status=202)
    if file_obj.error_message:
        return HttpResponse(f"Error processing file: {file_obj.error_message}", status=500)

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        )
        from reportlab.lib import colors
        from reportlab.lib.units import inch

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            leftMargin=0.5 * inch, rightMargin=0.5 * inch,
            topMargin=0.75 * inch, bottomMargin=0.75 * inch,
        )
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            'CustomTitle', parent=styles['Heading1'],
            fontSize=26, spaceAfter=20, alignment=1,
            textColor=colors.darkblue, fontName='Helvetica-Bold',
        )
        h2 = ParagraphStyle(
            'H2', parent=styles['Heading2'],
            fontSize=16, spaceAfter=12, textColor=colors.navy, fontName='Helvetica-Bold',
        )
        h3 = ParagraphStyle(
            'H3', parent=styles['Heading3'],
            fontSize=12, spaceAfter=8, textColor=colors.darkblue, fontName='Helvetica-Bold',
        )
        normal = ParagraphStyle('Normal2', parent=styles['Normal'], fontSize=10, spaceAfter=4)
        footer_style = ParagraphStyle(
            'Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=1,
        )

        story.append(Paragraph("Analytics App — Data Analysis Report", ParagraphStyle(
            'Header', parent=styles['Normal'], fontSize=12, textColor=colors.grey, alignment=1,
        )))
        story.append(Spacer(1, 8))
        file_name = file_obj.file.name.split('/')[-1]
        story.append(Paragraph(f"Analytics Report: {file_name}", title_style))
        story.append(Spacer(1, 16))

        story.append(Paragraph("File Information", h2))
        try:
            df = pd.read_csv(file_obj.file.path)
            num_columns = len(df.columns)
        except Exception:
            num_columns = "N/A"

        file_info = [
            ["File Name", file_name],
            ["Uploaded At", file_obj.uploaded_at.strftime('%Y-%m-%d %H:%M:%S UTC')],
            ["File Type", file_obj.file_type.upper()],
            ["Rows", str(file_obj.num_rows)],
            ["Columns", str(num_columns)],
            ["File Size", f"{file_obj.size / 1024:.1f} KB"],
        ]
        _table_style = [
            ('BACKGROUND', (0, 0), (0, -1), colors.navy),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (1, 0), (-1, -1), [colors.aliceblue, colors.lightcyan]),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]
        t = Table(file_info, colWidths=[2 * inch, 4.5 * inch])
        t.setStyle(TableStyle(_table_style))
        story.append(t)
        story.append(Spacer(1, 16))

        story.append(Paragraph("Column Analysis", h2))
        processed_data = ProcessedData.objects.filter(uploaded_file=file_obj)
        for pd_obj in processed_data:
            story.append(Paragraph(f"Column: {pd_obj.column_name} ({pd_obj.data_type})", h3))
            stats = pd_obj.stats
            if isinstance(stats, str):
                try:
                    stats = json.loads(stats)
                except Exception:
                    stats = {}
            rows = [["Statistic", "Value"]]
            for key, value in stats.items():
                if key in ('histogram', 'sample_values'):
                    continue
                if key == 'outliers' and isinstance(value, dict):
                    rows.append(['outlier_count', str(value.get('count', 0))])
                    continue
                if isinstance(value, list):
                    val_str = ', '.join(str(v) for v in value[:5])
                    if len(value) > 5:
                        val_str += '…'
                else:
                    val_str = str(value)
                    if isinstance(value, float):
                        val_str = f"{value:.4f}"
                rows.append([key, val_str[:60]])

            st = Table(rows, colWidths=[2 * inch, 4.5 * inch])
            st.setStyle(TableStyle(_table_style))
            story.append(st)
            story.append(Spacer(1, 10))

        story.append(Spacer(1, 12))
        story.append(Paragraph("Generated by Analytics App", footer_style))

        doc.build(story)
        buffer.seek(0)

        resp = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        resp['Content-Disposition'] = f'attachment; filename="analytics_report_{file_id}.pdf"'
        return resp

    except Exception as e:
        logger.error("Error generating PDF for file %d: %s", file_id, e, exc_info=True)
        return HttpResponse(f"Error generating PDF: {e}", status=500)


@login_required
def export_results_view(request, file_id):
    """Export the processed data as CSV, JSON, or XLSX."""
    file_obj = get_object_or_404(UploadedFile, id=file_id)

    if not _check_ownership(request, file_obj):
        return HttpResponse("Permission denied.", status=403)

    if not file_obj.processed:
        return HttpResponse("File is still being processed.", status=202)
    if file_obj.error_message:
        return HttpResponse(f"Error: {file_obj.error_message}", status=500)

    fmt = request.GET.get('format', 'csv')
    try:
        df = pd.read_csv(file_obj.file.path)
    except Exception as e:
        return HttpResponse(f"Error reading file: {e}", status=500)

    buf = io.BytesIO()
    fmt_map = {
        'csv':   ('text/csv', 'csv', lambda: df.to_csv(buf, index=False)),
        'json':  ('application/json', 'json', lambda: df.to_json(buf, orient='records')),
        'excel': (
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xlsx',
            lambda: df.to_excel(buf, index=False, engine='openpyxl'),
        ),
    }
    if fmt not in fmt_map:
        return HttpResponse("Invalid format specified.", status=400)

    content_type, ext, write_fn = fmt_map[fmt]
    write_fn()
    buf.seek(0)

    resp = HttpResponse(buf.getvalue(), content_type=content_type)
    resp['Content-Disposition'] = f'attachment; filename="exported_data_{file_id}.{ext}"'
    return resp
