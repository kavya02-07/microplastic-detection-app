"""
Phase 6E — PDF Analytical Report Generation Endpoint

Generates a formal scientific report from existing Analysis + Detection database records.
Does NOT rerun YOLO inference.
"""

import io
import math
import statistics
from datetime import datetime
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.db import models
from backend.db.models import User
from backend.dependencies import get_db
from backend.auth.dependencies import get_current_user
from backend.core import morphology_reference as morph_ref
from backend.core import model_evaluation

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image as RLImage, HRFlowable
)

# Matplotlib for charts
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from scipy.stats import gaussian_kde

router = APIRouter()

# ─── Color palette ───────────────────────────────────────────────────────────
BRAND_DARK = colors.HexColor('#0f172a')
BRAND_PRIMARY = colors.HexColor('#0ea5e9')
BRAND_ACCENT = colors.HexColor('#06b6d4')
BRAND_LIGHT_BG = colors.HexColor('#f0f9ff')
TEXT_DARK = colors.HexColor('#1e293b')
TEXT_MUTED = colors.HexColor('#64748b')
TABLE_HEADER_BG = colors.HexColor('#0f172a')
TABLE_ALT_ROW = colors.HexColor('#f8fafc')

# Chart colors for the 4 classes
CLASS_COLORS = {
    'Fibers':    '#0ea5e9',
    'Films':     '#06b6d4',
    'Fragments': '#8b5cf6',
    'Pellets':   '#f59e0b',
}
CHART_BG = '#fafbfc'


def _build_styles():
    """Create all paragraph styles used in the report."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'ReportTitle', parent=styles['Title'],
        fontSize=28, leading=34, textColor=BRAND_DARK,
        alignment=TA_CENTER, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        'ReportSubtitle', parent=styles['Normal'],
        fontSize=13, leading=18, textColor=TEXT_MUTED,
        alignment=TA_CENTER, spaceAfter=20,
    ))
    styles.add(ParagraphStyle(
        'SectionHeading', parent=styles['Heading1'],
        fontSize=16, leading=20, textColor=BRAND_DARK,
        spaceBefore=18, spaceAfter=10,
        borderColor=BRAND_PRIMARY, borderWidth=2,
        borderPadding=(0, 0, 4, 0),
    ))
    styles.add(ParagraphStyle(
        'SubHeading', parent=styles['Heading2'],
        fontSize=12, leading=16, textColor=BRAND_DARK,
        spaceBefore=10, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        'BodyText2', parent=styles['Normal'],
        fontSize=10, leading=14, textColor=TEXT_DARK,
        alignment=TA_JUSTIFY, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        'SmallText', parent=styles['Normal'],
        fontSize=8, leading=10, textColor=TEXT_MUTED,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        'CellText', parent=styles['Normal'],
        fontSize=8.5, leading=11, textColor=TEXT_DARK,
    ))
    styles.add(ParagraphStyle(
        'CellHeader', parent=styles['Normal'],
        fontSize=8.5, leading=11, textColor=colors.white,
        fontName='Helvetica-Bold',
    ))
    styles.add(ParagraphStyle(
        'FooterText', parent=styles['Normal'],
        fontSize=7, leading=9, textColor=TEXT_MUTED,
        alignment=TA_CENTER,
    ))
    return styles


def _make_chart_image(fig, dpi=150):
    """Convert a matplotlib figure to a ReportLab Image flowable."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight',
                facecolor=CHART_BG, edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return buf


def _safe_stat(values, func):
    """Safely compute a statistic, returning None on failure."""
    try:
        if not values:
            return None
        return func(values)
    except Exception:
        return None


def _fmt(val, decimals=2):
    """Format a number or return '—' if None."""
    if val is None:
        return '—'
    return f'{val:.{decimals}f}'


def _pct(val, decimals=1):
    """Format a percentage value."""
    if val is None:
        return '—'
    return f'{val:.{decimals}f}%'


# ─── Chart Builders ──────────────────────────────────────────────────────────

def _build_morphology_composition_chart(class_counts: dict, total: int) -> io.BytesIO:
    """Figure 1: Donut chart showing morphology composition with counts and percentages."""
    active_items = [(cls, cnt) for cls, cnt in class_counts.items() if cnt > 0]
    if not active_items:
        labels = list(class_counts.keys())
        counts = [0] * len(labels)
        chart_colors = [CLASS_COLORS.get(l, '#94a3b8') for l in labels]
    else:
        labels = [item[0] for item in active_items]
        counts = [item[1] for item in active_items]
        chart_colors = [CLASS_COLORS.get(l, '#94a3b8') for l in labels]

    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    fig.patch.set_facecolor(CHART_BG)
    ax.set_facecolor(CHART_BG)

    if sum(counts) > 0:
        wedges, texts, autotexts = ax.pie(
            counts,
            labels=None,
            colors=chart_colors,
            autopct='%1.1f%%',
            startangle=90,
            pctdistance=0.76,
            wedgeprops=dict(width=0.42, edgecolor='white', linewidth=1.5),
        )
        for at in autotexts:
            at.set_fontsize(8.5)
            at.set_fontweight('bold')
            at.set_color('#1e293b')

        # Center summary text
        ax.text(0, 0, f"Total\n{total}\nParticles", ha='center', va='center',
                fontsize=9.5, fontweight='bold', color='#0f172a', linespacing=1.3)

        # Clean legend with class names, counts and percentages
        legend_labels = [f"{l}: {c} ({c/total*100:.1f}%)" for l, c in zip(labels, counts)]
        ax.legend(wedges, legend_labels, title="Morphology Classes", loc="center left",
                  bbox_to_anchor=(0.95, 0.5), fontsize=8.5, title_fontsize=9,
                  frameon=True, facecolor='white', edgecolor='#e2e8f0')
    else:
        ax.text(0.5, 0.5, "No detections to display", ha='center', va='center',
                fontsize=10, color='#64748b', transform=ax.transAxes)
        ax.axis('off')

    ax.set_title("Morphology Composition Proportion", fontsize=11, fontweight='bold', color='#0f172a', pad=12)
    fig.tight_layout(pad=1.5)
    return _make_chart_image(fig)


def _build_class_bar_chart(class_counts: dict, total: int) -> io.BytesIO:
    """Figure 2: Class distribution bar chart showing exact detection counts."""
    labels = list(class_counts.keys())
    counts = [class_counts[l] for l in labels]
    chart_colors = [CLASS_COLORS.get(l, '#94a3b8') for l in labels]

    fig, ax = plt.subplots(figsize=(6.2, 3.0))
    fig.patch.set_facecolor(CHART_BG)
    ax.set_facecolor(CHART_BG)

    bars = ax.bar(labels, counts, color=chart_colors, edgecolor='white', linewidth=1.0, width=0.52)
    ax.set_ylabel("Number of Detected Particles", fontsize=9, color='#1e293b', fontweight='500')
    ax.set_xlabel("Morphological Class", fontsize=9, color='#1e293b', fontweight='500')
    ax.set_title("Particle Counts by Morphological Class", fontsize=11, fontweight='bold', color='#0f172a', pad=12)
    ax.tick_params(axis='x', labelsize=9)
    ax.tick_params(axis='y', labelsize=8)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cbd5e1')
    ax.spines['bottom'].set_color('#cbd5e1')
    ax.grid(axis='y', linestyle='--', alpha=0.4, color='#cbd5e1')

    # Add count and percentage labels above each bar
    max_c = max(counts) if counts else 0
    for bar, count in zip(bars, counts):
        pct_str = f" ({count/total*100:.1f}%)" if total > 0 else ""
        y_pos = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, y_pos + (0.15 if max_c < 8 else max_c * 0.02),
                f"{count}{pct_str}" if count > 0 else "0",
                ha='center', va='bottom', fontsize=8, fontweight='bold', color='#1e293b')

    if max_c > 0:
        ax.set_ylim(0, max_c * 1.22 + 0.5)

    fig.tight_layout(pad=1.5)
    return _make_chart_image(fig)


def _build_confidence_histogram(confidences: list) -> io.BytesIO:
    """Figure 3: Histogram of model confidence scores with mean and median lines."""
    fig, ax = plt.subplots(figsize=(6.2, 3.0))
    fig.patch.set_facecolor(CHART_BG)
    ax.set_facecolor(CHART_BG)

    if len(confidences) >= 2:
        bins = min(15, max(5, len(confidences) // 2))
        ax.hist(confidences, bins=bins, color='#0ea5e9', edgecolor='white',
                linewidth=1.0, alpha=0.85)
        mean_c = statistics.mean(confidences)
        median_c = statistics.median(confidences)
        ax.axvline(mean_c, color='#ef4444', linewidth=1.5, linestyle='--',
                   label=f'Mean: {mean_c:.3f}')
        ax.axvline(median_c, color='#10b981', linewidth=1.5, linestyle=':',
                   label=f'Median: {median_c:.3f}')
        ax.legend(fontsize=8, loc='upper left', frameon=True, facecolor='white', edgecolor='#e2e8f0')
    elif len(confidences) == 1:
        ax.bar([confidences[0]], [1], width=0.04, color='#0ea5e9', edgecolor='white')
        ax.axvline(confidences[0], color='#ef4444', linewidth=1.5, linestyle='--',
                   label=f'Value: {confidences[0]:.3f}')
        ax.legend(fontsize=8, loc='upper left')
    else:
        ax.text(0.5, 0.5, "No confidence data available", ha='center', va='center',
                color='#64748b', transform=ax.transAxes)

    ax.set_xlabel("Model Confidence Score", fontsize=9, color='#1e293b', fontweight='500')
    ax.set_ylabel("Particle Count", fontsize=9, color='#1e293b', fontweight='500')
    ax.set_title("Model Confidence Score Distribution", fontsize=11, fontweight='bold', color='#0f172a', pad=12)
    ax.tick_params(axis='both', labelsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cbd5e1')
    ax.spines['bottom'].set_color('#cbd5e1')
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(axis='y', linestyle='--', alpha=0.4, color='#cbd5e1')

    fig.tight_layout(pad=1.5)
    return _make_chart_image(fig)


def _build_area_histogram(areas: list) -> io.BytesIO:
    """Figure 4: Particle bounding-box area distribution histogram in image px²."""
    fig, ax = plt.subplots(figsize=(6.2, 3.0))
    fig.patch.set_facecolor(CHART_BG)
    ax.set_facecolor(CHART_BG)

    if len(areas) >= 2:
        bins = min(15, max(5, len(areas) // 2))
        ax.hist(areas, bins=bins, color='#8b5cf6', edgecolor='white', linewidth=1.0, alpha=0.85)
        mean_a = statistics.mean(areas)
        median_a = statistics.median(areas)
        ax.axvline(mean_a, color='#ef4444', linewidth=1.5, linestyle='--',
                   label=f'Mean: {mean_a:.1f} px²')
        ax.axvline(median_a, color='#10b981', linewidth=1.5, linestyle=':',
                   label=f'Median: {median_a:.1f} px²')
        ax.legend(fontsize=8, loc='upper right', frameon=True, facecolor='white', edgecolor='#e2e8f0')
    elif len(areas) == 1:
        ax.bar([areas[0]], [1], width=max(areas[0]*0.1, 10), color='#8b5cf6', edgecolor='white')
        ax.axvline(areas[0], color='#ef4444', linewidth=1.5, linestyle='--',
                   label=f'Value: {areas[0]:.1f} px²')
        ax.legend(fontsize=8, loc='upper right')
    else:
        ax.text(0.5, 0.5, "No particle area data available", ha='center', va='center',
                color='#64748b', transform=ax.transAxes)

    ax.set_xlabel("Particle Bounding Box Area (px²)", fontsize=9, color='#1e293b', fontweight='500')
    ax.set_ylabel("Particle Count", fontsize=9, color='#1e293b', fontweight='500')
    ax.set_title("Particle Area Distribution (Image-Space px²)", fontsize=11, fontweight='bold', color='#0f172a', pad=12)
    ax.tick_params(axis='both', labelsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cbd5e1')
    ax.spines['bottom'].set_color('#cbd5e1')
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(axis='y', linestyle='--', alpha=0.4, color='#cbd5e1')

    fig.tight_layout(pad=1.5)
    return _make_chart_image(fig)


def _build_class_avg_area_chart(detections: list, all_classes: list) -> io.BytesIO:
    """Figure 5: Class-wise average particle area comparison bar chart."""
    labels = []
    avg_areas = []
    bar_colors = []

    for cls in all_classes:
        cls_areas = [d.area for d in detections if d.class_name == cls and d.area is not None]
        if cls_areas:
            labels.append(cls)
            avg_areas.append(statistics.mean(cls_areas))
            bar_colors.append(CLASS_COLORS.get(cls, '#94a3b8'))

    fig, ax = plt.subplots(figsize=(6.2, 3.0))
    fig.patch.set_facecolor(CHART_BG)
    ax.set_facecolor(CHART_BG)

    if labels:
        bars = ax.bar(labels, avg_areas, color=bar_colors, edgecolor='white', linewidth=1.0, width=0.5)
        ax.set_ylabel("Average Area (px²)", fontsize=9, color='#1e293b', fontweight='500')
        ax.set_xlabel("Morphological Class", fontsize=9, color='#1e293b', fontweight='500')
        ax.set_title("Class-Wise Average Particle Area", fontsize=11, fontweight='bold', color='#0f172a', pad=12)
        ax.tick_params(axis='x', labelsize=9)
        ax.tick_params(axis='y', labelsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cbd5e1')
        ax.spines['bottom'].set_color('#cbd5e1')
        ax.grid(axis='y', linestyle='--', alpha=0.4, color='#cbd5e1')

        max_val = max(avg_areas) if avg_areas else 1
        for bar, val in zip(bars, avg_areas):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max_val * 0.02,
                    f"{val:.1f} px²", ha='center', va='bottom', fontsize=8, fontweight='bold', color='#1e293b')
        ax.set_ylim(0, max_val * 1.2)
    else:
        ax.text(0.5, 0.5, "No area data available", ha='center', va='center',
                color='#64748b', transform=ax.transAxes)

    fig.tight_layout(pad=1.5)
    return _make_chart_image(fig)


def _build_spatial_heatmap(detections: list, original_filename: str = None) -> io.BytesIO:
    """
    Figure 6: 2D spatial detection-density heatmap from bounding box centers:
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    Preserves microscopic image coordinate convention (origin (0,0) at top-left).
    Clearly represents spatial distribution of detected particles, NOT a toxicity or health-risk map.
    """
    pts = []
    class_labels = []
    for d in detections:
        if d.x1 is not None and d.x2 is not None and d.y1 is not None and d.y2 is not None:
            cx = (d.x1 + d.x2) / 2.0
            cy = (d.y1 + d.y2) / 2.0
            pts.append((cx, cy))
            class_labels.append(d.class_name)

    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    fig.patch.set_facecolor(CHART_BG)
    ax.set_facecolor('#0f172a')  # Dark canvas for heatmap clarity

    if len(pts) >= 1:
        xs = np.array([p[0] for p in pts])
        ys = np.array([p[1] for p in pts])

        # Determine canvas bounds with margin
        max_x = max(float(np.max(xs)) * 1.08, 100.0)
        max_y = max(float(np.max(ys)) * 1.08, 100.0)
        min_x = max(0.0, float(np.min(xs)) * 0.92 - 10.0)
        min_y = max(0.0, float(np.min(ys)) * 0.92 - 10.0)

        # 2D Kernel Density Estimation if >= 3 non-collinear points
        kde_plotted = False
        if len(pts) >= 3:
            try:
                jitter_x = xs + np.random.normal(0, 1e-4, len(xs))
                jitter_y = ys + np.random.normal(0, 1e-4, len(ys))
                xy = np.vstack([jitter_x, jitter_y])
                kde = gaussian_kde(xy)

                grid_size = 120
                xi = np.linspace(min_x, max_x, grid_size)
                yi = np.linspace(min_y, max_y, grid_size)
                x_grid, y_grid = np.meshgrid(xi, yi)
                grid_coords = np.vstack([x_grid.ravel(), y_grid.ravel()])
                zi = kde(grid_coords).reshape(x_grid.shape)

                if zi.max() > zi.min():
                    zi = (zi - zi.min()) / (zi.max() - zi.min())

                im = ax.imshow(
                    zi, origin='upper', extent=[min_x, max_x, max_y, min_y],
                    cmap='plasma', aspect='auto', alpha=0.88, interpolation='bicubic'
                )
                cbar = fig.colorbar(im, ax=ax, pad=0.03, shrink=0.85)
                cbar.set_label("Relative Detection Density", fontsize=8, color='#1e293b')
                cbar.ax.tick_params(labelsize=7)
                kde_plotted = True
            except Exception:
                kde_plotted = False

        if not kde_plotted:
            counts, xedges, yedges = np.histogram2d(xs, ys, bins=15, range=[[min_x, max_x], [min_y, max_y]])
            im = ax.imshow(
                counts.T, origin='upper', extent=[min_x, max_x, max_y, min_y],
                cmap='plasma', aspect='auto', alpha=0.85, interpolation='gaussian'
            )
            cbar = fig.colorbar(im, ax=ax, pad=0.03, shrink=0.85)
            cbar.set_label("Detection Count Density", fontsize=8, color='#1e293b')
            cbar.ax.tick_params(labelsize=7)

        # Overlay individual detection centers
        for cx, cy, cname in zip(xs, ys, class_labels):
            pcolor = CLASS_COLORS.get(cname, '#ffffff')
            ax.scatter(cx, cy, color=pcolor, s=36, edgecolors='white', linewidth=0.7, zorder=5)

        ax.set_xlim(min_x, max_x)
        ax.set_ylim(max_y, min_y)  # Inverted Y: 0 at top, matching image coordinates
    else:
        ax.text(0.5, 0.5, "No spatial coordinates available", ha='center', va='center',
                color='white', transform=ax.transAxes)

    ax.set_xlabel("Image X Coordinate (px)", fontsize=9, color='#1e293b', fontweight='500')
    ax.set_ylabel("Image Y Coordinate (px — origin top-left)", fontsize=9, color='#1e293b', fontweight='500')
    ax.set_title("Detection Spatial Density (Image-Space Coordinates)", fontsize=11, fontweight='bold', color='#0f172a', pad=12)
    ax.tick_params(axis='both', labelsize=8, colors='#1e293b')
    ax.spines['top'].set_color('#cbd5e1')
    ax.spines['right'].set_color('#cbd5e1')
    ax.spines['left'].set_color('#cbd5e1')
    ax.spines['bottom'].set_color('#cbd5e1')

    fig.tight_layout(pad=1.5)
    return _make_chart_image(fig)


def _build_confidence_area_scatter(detections: list) -> io.BytesIO:
    """
    Figure 7: Confidence vs particle-area scatter plot.
    X = Detection.area (px²)
    Y = Detection.confidence
    Points distinguished by morphological class.
    """
    fig, ax = plt.subplots(figsize=(6.2, 3.0))
    fig.patch.set_facecolor(CHART_BG)
    ax.set_facecolor(CHART_BG)

    valid_dets = [d for d in detections if d.area is not None and d.confidence is not None]
    if len(valid_dets) >= 2:
        classes_present = sorted(set(d.class_name for d in valid_dets))
        for cls in classes_present:
            cls_dets = [d for d in valid_dets if d.class_name == cls]
            c_areas = [d.area for d in cls_dets]
            c_confs = [d.confidence for d in cls_dets]
            color = CLASS_COLORS.get(cls, '#94a3b8')
            ax.scatter(c_areas, c_confs, color=color, label=f"{cls} (n={len(cls_dets)})",
                       s=38, alpha=0.82, edgecolors='white', linewidth=0.6)

        ax.legend(fontsize=8, loc='best', frameon=True, facecolor='white', edgecolor='#e2e8f0')
    elif len(valid_dets) == 1:
        d = valid_dets[0]
        color = CLASS_COLORS.get(d.class_name, '#94a3b8')
        ax.scatter([d.area], [d.confidence], color=color, label=d.class_name, s=45, edgecolors='white')
        ax.legend(fontsize=8, loc='best')
    else:
        ax.text(0.5, 0.5, "Insufficient data for scatter plot", ha='center', va='center',
                color='#64748b', transform=ax.transAxes)

    ax.set_xlabel("Particle Area (px²)", fontsize=9, color='#1e293b', fontweight='500')
    ax.set_ylabel("Model Confidence Score", fontsize=9, color='#1e293b', fontweight='500')
    ax.set_title("Confidence Score vs. Particle Area", fontsize=11, fontweight='bold', color='#0f172a', pad=12)
    ax.tick_params(axis='both', labelsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cbd5e1')
    ax.spines['bottom'].set_color('#cbd5e1')
    ax.grid(True, linestyle='--', alpha=0.4, color='#cbd5e1')

    fig.tight_layout(pad=1.5)
    return _make_chart_image(fig)


# ─── Table Builder Helpers ────────────────────────────────────────────────────

def _styled_table(data, col_widths=None, header=True):
    """Create a consistently styled table."""
    tbl = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style_cmds = [
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]
    if header:
        style_cmds += [
            ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ]
    # Alternate row coloring
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), TABLE_ALT_ROW))

    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def _wrapped_table(data, col_widths, styles, highlight_rows=None, header=True):
    """
    Styled table whose cells wrap long text.

    String cells are converted to Paragraphs (CellHeader for the header row,
    CellText otherwise); existing flowables are passed through unchanged.
    Rows listed in `highlight_rows` receive a light brand-colored background.
    """
    highlight_rows = set(highlight_rows or [])
    wrapped = []
    for r, row in enumerate(data):
        cell_style = styles['CellHeader'] if (header and r == 0) else styles['CellText']
        wrapped.append([
            Paragraph(cell, cell_style) if isinstance(cell, str) else cell
            for cell in row
        ])

    tbl = Table(wrapped, colWidths=col_widths, repeatRows=1 if header else 0)
    style_cmds = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]
    if header:
        style_cmds.append(('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG))
    first_body = 1 if header else 0
    for i in range(first_body, len(data)):
        if i in highlight_rows:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), BRAND_LIGHT_BG))
            style_cmds.append(('LINEBEFORE', (0, i), (0, i), 3, BRAND_PRIMARY))
        elif i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), TABLE_ALT_ROW))

    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def _build_morphology_reference_section(styles, class_counts: dict, total: int, all_classes: list) -> list:
    """
    §4 Morphology Reference: a single compact table summarising published
    literature on each of the four morphological classes (characteristics +
    typical sources), with classes detected in this sample highlighted.
    Condensed by design — full scientific detail lives in
    backend.core.morphology_reference, not in the report body.
    """
    flow = []

    flow.append(Paragraph('4. Morphology Reference', styles['SectionHeading']))
    flow.append(Paragraph(
        'General literature background for each morphological class — not findings '
        'from this sample. Classes detected in this analysis are highlighted below; '
        'see Section 11 (Interpretation &amp; Limitations) for what this classification '
        'does and does not establish.',
        styles['BodyText2']
    ))
    flow.append(Spacer(1, 4))

    def _status(cls):
        cnt = class_counts.get(cls, 0)
        if cnt > 0:
            pct = cnt / total * 100 if total > 0 else 0.0
            return f'<b>Detected</b><br/>{cnt} ({pct:.1f}%)'
        return 'Not detected'

    overview = [['Class', 'This Sample', 'Characteristics', 'Typical Sources']]
    highlight = []
    cited_keys = []
    for row_idx, cls in enumerate(all_classes, start=1):
        profile = morph_ref.get_profile(cls)
        if profile is None:
            continue
        char_text, char_keys = profile['characteristics']
        src_text, src_keys = profile['sources']
        for k in char_keys + src_keys:
            if k not in cited_keys:
                cited_keys.append(k)
        overview.append([
            f'<b>{escape(cls)}</b>',
            _status(cls),
            escape(char_text),
            escape(src_text),
        ])
        if class_counts.get(cls, 0) > 0:
            highlight.append(row_idx)

    flow.append(_wrapped_table(overview, col_widths=[68, 62, 190, 160],
                               styles=styles, highlight_rows=highlight))
    flow.append(Spacer(1, 3))
    flow.append(Paragraph(
        f'<i>Highlighted rows indicate classes detected in this sample; detection does not '
        f'confirm plastic identity, polymer type or source. Sources: '
        f'{escape(morph_ref.short_sources(cited_keys))}.</i>',
        styles['SmallText']
    ))

    return flow


def _build_interpretation_box(styles, section_number: int = 11) -> list:
    """
    Interpretation & Limitations: one condensed, bordered call-out that
    replaces the former standalone Methodology / Model Information /
    Limitations / Conclusion / References sections. Keeps the essential
    scientific safeguards without literature-review-length prose.
    section_number is passed so numbering stays correct whether or not the
    optional Model Evaluation section precedes it.
    """
    safeguard_keys = ["gesamp2019", "kappler2016", "who2019", "who2022"]

    cell_flow = [
        Paragraph(f'{section_number}. Interpretation &amp; Limitations', styles['SectionHeading']),
        Paragraph(
            '• Fibers, Films, Fragments and Pellets are <b>morphological (shape) categories</b> '
            'derived from image features — they are not polymer-chemistry identification.',
            styles['BodyText2']
        ),
        Paragraph(
            '• This classification does <b>not</b> establish the source, toxicity, exposure dose, '
            'contamination severity, or human-health risk of any detected particle.',
            styles['BodyText2']
        ),
        Paragraph(
            '• Confirming polymer type (e.g. PE, PP, PET, PS, PVC) requires complementary analytical '
            'techniques such as <b>FTIR or Raman spectroscopy</b>; this model does not perform them.',
            styles['BodyText2']
        ),
        Paragraph(
            '• The human-health implications of microplastic exposure remain an '
            '<b>active area of scientific research</b>, with data currently insufficient to support '
            'risk conclusions from any single image-based analysis.',
            styles['BodyText2']
        ),
        Paragraph(
            '• All bounding-box measurements (width, height, area, aspect ratio) are in uncalibrated '
            'image-pixel units, not physical dimensions.',
            styles['BodyText2']
        ),
        Paragraph(
            f'<i>Background: {escape(morph_ref.short_sources(safeguard_keys))}.</i>',
            styles['SmallText']
        ),
    ]

    box = Table([[cell_flow]], colWidths=[471])
    box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BRAND_LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 1.2, BRAND_PRIMARY),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return [box]


# ─── Model Evaluation (research addition; reads extracted JSON, NOT the checkpoint) ─

def _build_training_curve_chart(history: dict) -> io.BytesIO:
    """
    Compact training-performance chart from the checkpoint's recorded per-epoch
    history: precision, recall, mAP@50 and mAP@50-95 over epochs (all 0-1 scale).
    Uses only values present in the extracted JSON — nothing is computed or
    estimated. Distinct from the seven sample-analysis chart functions.
    """
    epochs = history.get('epoch', [])
    fig, ax = plt.subplots(figsize=(6.2, 2.8))
    fig.patch.set_facecolor(CHART_BG)
    ax.set_facecolor(CHART_BG)

    curves = [
        ('metrics/precision(B)', 'Precision', '#0ea5e9'),
        ('metrics/recall(B)', 'Recall', '#f43f5e'),
        ('metrics/mAP50(B)', 'mAP@50', '#10b981'),
        ('metrics/mAP50-95(B)', 'mAP@50-95', '#8b5cf6'),
    ]
    plotted = False
    for key, label, color in curves:
        series = history.get(key)
        if series and epochs and len(series) == len(epochs):
            ax.plot(epochs, series, color=color, linewidth=1.4, label=label)
            plotted = True

    if plotted:
        ax.set_ylim(0, 1.02)
        ax.set_xlabel('Epoch', fontsize=9, color='#1e293b', fontweight='500')
        ax.set_ylabel('Metric value', fontsize=9, color='#1e293b', fontweight='500')
        ax.legend(fontsize=7.5, loc='lower right', ncol=2, frameon=True,
                  facecolor='white', edgecolor='#e2e8f0')
        ax.tick_params(axis='both', labelsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cbd5e1')
        ax.spines['bottom'].set_color('#cbd5e1')
        ax.grid(axis='y', linestyle='--', alpha=0.4, color='#cbd5e1')
    else:
        ax.text(0.5, 0.5, 'No training history available', ha='center', va='center',
                color='#64748b', transform=ax.transAxes)
        ax.axis('off')

    ax.set_title('Training-Run Validation Metrics over Epochs', fontsize=11,
                 fontweight='bold', color='#0f172a', pad=10)
    fig.tight_layout(pad=1.2)
    return _make_chart_image(fig)


def _build_model_evaluation_section(styles, section_number: int) -> list:
    """
    Compact 'Model Evaluation' section built from the extracted metrics JSON
    (backend/core/model_metrics.json) — never from the 52 MB checkpoint.
    Returns [] if the metrics file is unavailable, so the report degrades
    gracefully. Reports only aggregate validation metrics + training config;
    no per-class metrics, confusion matrix, or independent-test claims.
    """
    try:
        data = model_evaluation.get_model_evaluation()
    except Exception:
        return []

    flow = []
    fv = data.get('final_validation_metrics', {})
    cfg = data.get('training_config', {})
    model_info = data.get('model', {})
    history = data.get('epoch_history', {})
    epoch_count = data.get('epoch_count', 0)

    def _pct4(v):
        return f'{v * 100:.2f}%' if isinstance(v, (int, float)) else '—'

    flow.append(PageBreak())
    flow.append(Paragraph(f'{section_number}. Model Evaluation (Training-Run Validation)',
                          styles['SectionHeading']))
    flow.append(Paragraph(
        'Research evidence for the deployed detection checkpoint, recorded during its '
        'original training run and embedded in the model file. These are aggregate '
        'validation-split metrics, <b>not</b> independent test-set results, and are '
        'independent of the specific sample analysed above.',
        styles['BodyText2']
    ))
    flow.append(Spacer(1, 8))

    # Validation metrics table
    metrics_data = [
        ['Validation Metric', 'Value', 'Checkpoint Key'],
        ['Precision', _pct4(fv.get('precision')), 'metrics/precision(B)'],
        ['Recall', _pct4(fv.get('recall')), 'metrics/recall(B)'],
        ['mAP@50', _pct4(fv.get('map50')), 'metrics/mAP50(B)'],
        ['mAP@50-95', _pct4(fv.get('map50_95')), 'metrics/mAP50-95(B)'],
    ]
    flow.append(_styled_table(metrics_data, col_widths=[150, 130, 200]))
    flow.append(Spacer(1, 10))

    # Training configuration table
    cfg_data = [
        ['Training Parameter', 'Value'],
        ['Architecture', model_info.get('architecture') or 'YOLOv8 Medium'],
        ['Deployed Checkpoint', model_info.get('deployed_checkpoint') or '—'],
        ['Checkpoint Date', str(model_info.get('checkpoint_date') or '—')],
        ['Epochs', str(cfg.get('epochs') if cfg.get('epochs') is not None else '—')],
        ['Image Size', f"{cfg.get('imgsz')} px" if cfg.get('imgsz') is not None else '—'],
        ['Batch Size', str(cfg.get('batch') if cfg.get('batch') is not None else '—')],
        ['Optimizer', str(cfg.get('optimizer') or '—')],
        ['Training Data Source', str(cfg.get('training_data_source') or '—')],
    ]
    flow.append(_styled_table(cfg_data, col_widths=[170, 310]))
    flow.append(Spacer(1, 4))
    flow.append(Paragraph(
        '<i>Recorded training data source; dataset not included in this repository.</i>',
        styles['SmallText']
    ))
    flow.append(Spacer(1, 10))

    # One compact training-performance chart from the real epoch history
    if history and epoch_count:
        chart_buf = _build_training_curve_chart(history)
        flow.append(RLImage(chart_buf, width=440, height=200))
        flow.append(Spacer(1, 4))
        flow.append(Paragraph(
            f'<i>Figure 8: Precision, recall, mAP@50 and mAP@50-95 across '
            f'{epoch_count} training epochs (recorded in the checkpoint).</i>',
            styles['SmallText']
        ))
        flow.append(Spacer(1, 8))

    # Evidence / limitations disclaimer specific to model evaluation
    flow.append(Paragraph(
        '<b>Evidence &amp; limitations:</b> The figures above are validation-split metrics '
        'from the original training run embedded in the deployed checkpoint. The training '
        'dataset is not included in this repository, so they cannot be independently '
        'reproduced here; no independent held-out test set is available. No per-class '
        'precision, recall, mAP, or sample-level accuracy is claimed, as corresponding '
        'ground-truth labels are unavailable.',
        styles['SmallText']
    ))

    return flow


# ─── Page Number / Footer ────────────────────────────────────────────────────

def _page_footer(canvas, doc):
    """Add page number and branding to each page."""
    canvas.saveState()
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(colors.HexColor('#94a3b8'))
    page_num = canvas.getPageNumber()
    canvas.drawCentredString(A4[0] / 2, 15 * mm,
                             f'Clarium — Microplastic Detection Report — Page {page_num}')
    canvas.restoreState()


# ─── Main Report Builder ─────────────────────────────────────────────────────

def generate_report_pdf(analysis: models.Analysis, detections: list) -> io.BytesIO:
    """
    Generate a comprehensive analytical PDF report from stored data.
    Returns a BytesIO buffer containing the PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=20 * mm, leftMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=25 * mm,
        title=f'Microplastic Analysis Report #{analysis.id}',
        author='Clarium',
    )

    styles = _build_styles()
    story = []

    # Pre-compute analytics
    confidences = [d.confidence for d in detections if d.confidence is not None]
    areas = [d.area for d in detections if d.area is not None]
    widths = [d.width for d in detections if d.width is not None]
    heights = [d.height for d in detections if d.height is not None]
    aspect_ratios = [d.aspect_ratio for d in detections if d.aspect_ratio is not None]
    class_names = [d.class_name for d in detections]

    all_classes = ['Fibers', 'Films', 'Fragments', 'Pellets']
    class_counts = {}
    for cls in all_classes:
        class_counts[cls] = sum(1 for d in detections if d.class_name == cls)

    total = len(detections)
    report_date = datetime.now().strftime('%B %d, %Y at %H:%M')
    analysis_date = 'N/A'
    if analysis.created_at:
        try:
            analysis_date = analysis.created_at.strftime('%B %d, %Y at %H:%M')
        except Exception:
            analysis_date = str(analysis.created_at)

    # ═══════════════════════════════════════════════════════════════════════
    # 1. TITLE PAGE
    # ═══════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 60))
    story.append(Paragraph('🔬', ParagraphStyle('emoji', parent=styles['Title'],
                                                 fontSize=48, alignment=TA_CENTER)))
    story.append(Spacer(1, 10))
    story.append(Paragraph('Clarium', styles['ReportTitle']))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width='60%', thickness=2, color=BRAND_PRIMARY,
                            spaceAfter=12, spaceBefore=4))
    story.append(Paragraph(
        'Microplastic Detection &amp; Quantitative Analysis Report',
        styles['ReportSubtitle']
    ))
    story.append(Spacer(1, 30))

    # Title page metadata table
    meta_data = [
        ['Analysis ID', f'#{analysis.id}'],
        ['Source File', analysis.original_filename or 'N/A'],
        ['Report Generated', report_date],
        ['Analysis Date', analysis_date],
        ['Total Detections', str(total)],
    ]
    meta_tbl = Table(meta_data, colWidths=[130, 280])
    meta_tbl.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), TEXT_MUTED),
        ('TEXTCOLOR', (1, 0), (1, -1), TEXT_DARK),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('LEFTPADDING', (1, 0), (1, -1), 12),
    ]))
    story.append(meta_tbl)

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # 2. EXECUTIVE SUMMARY
    # ═══════════════════════════════════════════════════════════════════════
    story.append(Paragraph('1. Executive Summary', styles['SectionHeading']))

    avg_conf_str = _fmt(analysis.average_confidence * 100 if analysis.average_confidence else None, 1)
    inf_time_str = _fmt(analysis.inference_time_ms, 1)

    # Build morphology breakdown text
    morph_parts = []
    for cls in all_classes:
        cnt = class_counts[cls]
        if cnt > 0:
            pct = (cnt / total * 100) if total > 0 else 0
            morph_parts.append(f'{cls} ({cnt}, {pct:.1f}%)')
    morph_text = ', '.join(morph_parts) if morph_parts else 'No detections'

    summary_text = (
        f'This report presents the quantitative results of microplastic analysis '
        f'<b>#{analysis.id}</b> performed on sample image '
        f'<b>{analysis.original_filename or "N/A"}</b>. '
        f'The YOLOv8 Medium detection model identified a total of '
        f'<b>{total}</b> particle(s) across four morphological classes: {morph_text}. '
        f'The average model confidence score was <b>{avg_conf_str}%</b> '
        f'and inference completed in <b>{inf_time_str} ms</b>.'
    )
    story.append(Paragraph(summary_text, styles['BodyText2']))
    story.append(Spacer(1, 8))

    # ═══════════════════════════════════════════════════════════════════════
    # 3. ANALYSIS INFORMATION
    # ═══════════════════════════════════════════════════════════════════════
    story.append(Paragraph('2. Detection Overview', styles['SectionHeading']))

    info_data = [
        ['Parameter', 'Value'],
        ['Analysis ID', f'#{analysis.id}'],
        ['Source Filename', analysis.original_filename or 'N/A'],
        ['Confidence Threshold', _fmt(analysis.confidence_threshold, 2)],
        ['Analysis Timestamp', analysis_date],
        ['Total Detections', str(total)],
        ['Average Confidence', f'{avg_conf_str}%'],
        ['Inference Time', f'{inf_time_str} ms'],
        ['Model Architecture', 'YOLOv8 Medium (Ultralytics), weights t29.pt'],
        ['Model Classes', 'Fibers, Films, Fragments, Pellets'],
    ]
    story.append(_styled_table(info_data, col_widths=[170, 310]))
    story.append(Spacer(1, 12))

    # ═══════════════════════════════════════════════════════════════════════
    # 4. MORPHOLOGY COMPOSITION & CLASS DISTRIBUTION
    # ═══════════════════════════════════════════════════════════════════════
    story.append(Paragraph('3. Morphology Composition &amp; Distribution', styles['SectionHeading']))

    morph_data = [['Class', 'Count', 'Percentage']]
    for cls in all_classes:
        cnt = class_counts[cls]
        pct = (cnt / total * 100) if total > 0 else 0.0
        morph_data.append([cls, str(cnt), f'{pct:.1f}%'])
    morph_data.append(['Total', str(total), '100.0%' if total > 0 else '0.0%'])

    story.append(_styled_table(morph_data, col_widths=[170, 120, 120]))
    story.append(Spacer(1, 10))

    if total > 0:
        c1_buf = _build_morphology_composition_chart(class_counts, total)
        c1_img = RLImage(c1_buf, width=440, height=210)
        story.append(c1_img)
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            '<i>Figure 1: Morphology composition proportion across detected microplastic classes.</i>',
            styles['SmallText']
        ))
        story.append(Spacer(1, 10))

        c2_buf = _build_class_bar_chart(class_counts, total)
        c2_img = RLImage(c2_buf, width=440, height=200)
        story.append(c2_img)
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            '<i>Figure 2: Absolute particle counts and sample shares by morphological class.</i>',
            styles['SmallText']
        ))
    story.append(Spacer(1, 12))

    # ═══════════════════════════════════════════════════════════════════════
    # 4. MORPHOLOGY REFERENCE (condensed literature context; all 4 classes)
    # ═══════════════════════════════════════════════════════════════════════
    story.extend(_build_morphology_reference_section(styles, class_counts, total, all_classes))
    story.append(Spacer(1, 12))

    # ═══════════════════════════════════════════════════════════════════════
    # 5. CONFIDENCE ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════
    story.append(Paragraph('5. Confidence Analysis', styles['SectionHeading']))

    if confidences:
        mean_c = _safe_stat(confidences, statistics.mean)
        median_c = _safe_stat(confidences, statistics.median)
        min_c = min(confidences)
        max_c = max(confidences)
        range_c = max_c - min_c
        stdev_c = _safe_stat(confidences, statistics.stdev) if len(confidences) >= 2 else None

        conf_data = [
            ['Statistic', 'Value'],
            ['Mean', _fmt(mean_c, 4)],
            ['Median', _fmt(median_c, 4)],
            ['Minimum', _fmt(min_c, 4)],
            ['Maximum', _fmt(max_c, 4)],
            ['Range', _fmt(range_c, 4)],
            ['Std. Deviation', _fmt(stdev_c, 4) if stdev_c is not None else 'N/A (< 2 samples)'],
        ]
        story.append(_styled_table(conf_data, col_widths=[170, 310]))
        story.append(Spacer(1, 10))

        c3_buf = _build_confidence_histogram(confidences)
        c3_img = RLImage(c3_buf, width=440, height=200)
        story.append(c3_img)
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            '<i>Figure 3: Distribution of model confidence scores with mean and median references.</i>',
            styles['SmallText']
        ))
    else:
        story.append(Paragraph(
            'No confidence data available for statistical analysis.',
            styles['BodyText2']
        ))
    story.append(Spacer(1, 12))

    # ═══════════════════════════════════════════════════════════════════════
    # 7. MORPHOMETRY ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph('6. Morphometry Analysis', styles['SectionHeading']))
    story.append(Paragraph(
        '<i>Note: All measurements are in image-space pixel units derived from bounding-box '
        'coordinates. They do not represent calibrated physical dimensions.</i>',
        styles['SmallText']
    ))
    story.append(Spacer(1, 6))

    if areas:
        morph_metrics = [
            ['Metric', 'Mean', 'Median', 'Min', 'Max'],
        ]
        for label, vals in [('Width (px)', widths), ('Height (px)', heights),
                            ('Area (px²)', areas), ('Aspect Ratio', aspect_ratios)]:
            if vals:
                morph_metrics.append([
                    label,
                    _fmt(_safe_stat(vals, statistics.mean)),
                    _fmt(_safe_stat(vals, statistics.median)),
                    _fmt(min(vals)),
                    _fmt(max(vals)),
                ])
        story.append(_styled_table(morph_metrics, col_widths=[100, 95, 95, 95, 95]))
        story.append(Spacer(1, 10))

        c4_buf = _build_area_histogram(areas)
        c4_img = RLImage(c4_buf, width=440, height=200)
        story.append(c4_img)
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            '<i>Figure 4: Bounding-box area distribution across all detected particles (image px²).</i>',
            styles['SmallText']
        ))
        story.append(Spacer(1, 10))

        c5_buf = _build_class_avg_area_chart(detections, all_classes)
        c5_img = RLImage(c5_buf, width=440, height=200)
        story.append(c5_img)
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            '<i>Figure 5: Comparison of average bounding-box area by morphological class.</i>',
            styles['SmallText']
        ))
    else:
        story.append(Paragraph(
            'No morphometric data available.', styles['BodyText2']
        ))
    story.append(Spacer(1, 12))

    # ═══════════════════════════════════════════════════════════════════════
    # 8. SPATIAL DETECTION ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph('7. Spatial Detection Analysis', styles['SectionHeading']))
    story.append(Paragraph(
        'The 2D spatial detection-density heatmap illustrates the distribution of detected particles '
        'across the sample field of view, calculated from bounding-box center coordinates '
        '(center_x = (x1 + x2)/2, center_y = (y1 + y2)/2). '
        '<b>Note:</b> This visualization represents the spatial distribution of detected bounding boxes '
        'within the analyzed image; it does not measure contamination severity, biological toxicity, or health risk.',
        styles['BodyText2']
    ))
    story.append(Spacer(1, 8))

    if detections:
        c6_buf = _build_spatial_heatmap(detections, analysis.original_filename)
        c6_img = RLImage(c6_buf, width=440, height=225)
        story.append(c6_img)
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            '<i>Figure 6: Spatial detection-density heatmap (plasma colormap) with overlaid particle center coordinates.</i>',
            styles['SmallText']
        ))
    else:
        story.append(Paragraph('No spatial coordinate data recorded.', styles['BodyText2']))
    story.append(Spacer(1, 12))

    # ═══════════════════════════════════════════════════════════════════════
    # 9. CONFIDENCE VS. PARTICLE AREA
    # ═══════════════════════════════════════════════════════════════════════
    story.append(Paragraph('8. Confidence vs. Particle Area Analysis', styles['SectionHeading']))
    story.append(Paragraph(
        'Evaluation of model confidence scores against bounding-box areas to identify potential size-dependent '
        'prediction characteristics across morphological classes.',
        styles['BodyText2']
    ))
    story.append(Spacer(1, 8))

    if detections:
        c7_buf = _build_confidence_area_scatter(detections)
        c7_img = RLImage(c7_buf, width=440, height=200)
        story.append(c7_img)
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            '<i>Figure 7: Model confidence score as a function of bounding-box particle area (px²).</i>',
            styles['SmallText']
        ))
    else:
        story.append(Paragraph('No detection data for correlation analysis.', styles['BodyText2']))
    story.append(Spacer(1, 12))

    # ═══════════════════════════════════════════════════════════════════════
    # 9. QUANTITATIVE SUMMARY TABLE
    # ═══════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph('9. Quantitative Summary', styles['SectionHeading']))

    qs_data = [
        ['Measurement', 'Value'],
        ['Total Particles Detected', str(total)],
        ['Number of Classes Present', str(sum(1 for c in class_counts.values() if c > 0))],
        ['Dominant Class', (sorted(class_counts.items(), key=lambda x: x[1], reverse=True)[0][0]
                           if total > 0 else 'N/A')],
        ['Average Confidence', f'{avg_conf_str}%'],
        ['Inference Time', f'{inf_time_str} ms'],
        ['Confidence Threshold', _fmt(analysis.confidence_threshold)],
        ['Mean Particle Area (px²)', _fmt(_safe_stat(areas, statistics.mean)) if areas else 'N/A'],
        ['Mean Aspect Ratio', _fmt(_safe_stat(aspect_ratios, statistics.mean)) if aspect_ratios else 'N/A'],
    ]
    story.append(_styled_table(qs_data, col_widths=[230, 250]))
    story.append(Spacer(1, 10))

    # ═══════════════════════════════════════════════════════════════════════
    # 10. FULL DETECTION APPENDIX
    # ═══════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph('10. Detection Appendix', styles['SectionHeading']))
    story.append(Paragraph(
        'Complete listing of all individual particle detections from this analysis.',
        styles['BodyText2']
    ))
    story.append(Spacer(1, 6))

    if detections:
        # Split into pages of detections to avoid oversized tables
        det_header = ['#', 'Class', 'Confidence', 'Width', 'Height', 'Area', 'Aspect Ratio']
        page_size = 35  # rows per table chunk

        for chunk_start in range(0, len(detections), page_size):
            chunk = detections[chunk_start:chunk_start + page_size]
            det_data = [det_header]
            for idx, d in enumerate(chunk, start=chunk_start + 1):
                det_data.append([
                    str(idx),
                    d.class_name or 'Unknown',
                    _fmt(d.confidence, 4),
                    _fmt(d.width, 1),
                    _fmt(d.height, 1),
                    _fmt(d.area, 1),
                    _fmt(d.aspect_ratio, 3),
                ])
            story.append(_styled_table(det_data, col_widths=[32, 72, 72, 68, 68, 78, 72]))
            story.append(Spacer(1, 8))
    else:
        story.append(Paragraph('No individual detections recorded.', styles['BodyText2']))

    story.append(Spacer(1, 10))

    # ═══════════════════════════════════════════════════════════════════════
    # 11. MODEL EVALUATION (optional research addition; from extracted JSON)
    # ═══════════════════════════════════════════════════════════════════════
    eval_flow = _build_model_evaluation_section(styles, section_number=11)
    story.extend(eval_flow)

    # ═══════════════════════════════════════════════════════════════════════
    # INTERPRETATION & LIMITATIONS (single condensed safeguard box)
    # Numbered 12 when the Model Evaluation section is present, else 11.
    # ═══════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    interp_number = 12 if eval_flow else 11
    story.extend(_build_interpretation_box(styles, section_number=interp_number))

    # Disclaimer
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width='100%', thickness=0.5, color=TEXT_MUTED,
                            spaceAfter=8, spaceBefore=8))
    story.append(Paragraph(
        f'<i>Generated by Clarium (YOLOv8 Medium, weights t29.pt) from stored analysis '
        f'data — YOLO inference was not re-run to produce this report. Detections below '
        f'{_fmt(analysis.confidence_threshold)} confidence were filtered out prior to storage. '
        f'For research purposes; results should be validated by domain experts before drawing '
        f'scientific conclusions.</i>',
        styles['SmallText']
    ))

    # Build PDF
    doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
    buffer.seek(0)
    return buffer


# ─── API Endpoint ─────────────────────────────────────────────────────────────

@router.get("/analyses/{analysis_id}/report")
def get_analysis_report(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate and return a PDF analytical report for a specific analysis.
    Uses stored detection data — does NOT rerun YOLO inference.
    """
    # Fetch analysis
    analysis = db.query(models.Analysis).filter(
        models.Analysis.id == analysis_id
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this analysis")

    # Fetch associated detections (already stored)
    detections = db.query(models.Detection).filter(
        models.Detection.analysis_id == analysis_id
    ).all()

    # Generate PDF
    pdf_buffer = generate_report_pdf(analysis, detections)

    filename = f'microplastic_report_{analysis_id}.pdf'

    return StreamingResponse(
        pdf_buffer,
        media_type='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
        },
    )
