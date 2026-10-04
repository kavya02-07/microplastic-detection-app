import sys
import re
import zlib
import base64
from pathlib import Path

pdf_path = sys.argv[1] if len(sys.argv) > 1 else 'scratch/test_report_13.pdf'
if not Path(pdf_path).exists():
    pdf_path = 'scratch/upgraded_report_test.pdf'

print(f"Inspecting PDF: {pdf_path}")
with open(pdf_path, 'rb') as f:
    data = f.read()

streams = re.findall(rb'stream\r?\n(.*?)~>endstream', data, re.DOTALL)
decompressed_chunks = []

for s in streams:
    try:
        raw = base64.a85decode(s + b'~>', adobe=True)
        decomp = zlib.decompress(raw)
        decompressed_chunks.append(decomp.decode('latin1', errors='ignore'))
    except Exception:
        pass

all_text = ' '.join(decompressed_chunks)
print(f'Total decompressed text length: {len(all_text):,} characters from {len(decompressed_chunks)} streams')

figures = [
    ('Figure 1: Morphology Donut Chart', 'Figure 1: Morphology composition proportion'),
    ('Figure 2: Class Bar Chart', 'Figure 2: Absolute particle counts'),
    ('Figure 3: Confidence Histogram', 'Figure 3: Distribution of model confidence scores'),
    ('Figure 4: Area Histogram', 'Figure 4: Bounding-box area distribution'),
    ('Figure 5: Class-Wise Avg Area Bar', 'Figure 5: Comparison of average bounding-box area'),
    ('Figure 6: Spatial Density Heatmap', 'Figure 6: Spatial detection-density heatmap'),
    ('Figure 7: Confidence vs Area Scatter', 'Figure 7: Model confidence score as a function'),
]

print("\n--- Verifying All 7 Analytical Figures in PDF ---")
all_found = True
for label, needle in figures:
    found = needle in all_text
    status = "OK" if found else "FAIL"
    print(f'  [{status}] {label}: "{needle}"')
    if not found:
        all_found = False

sections = [
    ('Section 4: Morphology Reference', '4. Morphology Reference'),
    ('Section 11: Model Evaluation', '11. Model Evaluation'),
    ('Section 12: Interpretation & Limitations', '12. Interpretation'),
    ('Model evaluation Figure 8', 'Figure 8'),
    ('Morphology reference sources line', 'Sources: GESAMP'),  # parentheses are escaped in PDF streams
]

print("\n--- Verifying Morphology Reference, Model Evaluation & Interpretation Sections ---")
for label, needle in sections:
    found = needle in all_text
    status = "OK" if found else "FAIL"
    print(f'  [{status}] {label}: "{needle}"')
    if not found:
        all_found = False

pages = re.findall(rb'/Type\s*/Page\b', data)
print(f'\nTotal Pages in PDF: {len(pages)}')
img_matches = re.findall(b'/Subtype\s*/Image', data)
print(f'Embedded Image/Figure Elements: {len(img_matches)}')

assert all_found, "Missing figure in PDF!"
assert len(pages) > 0, "PDF has 0 pages!"
assert len(img_matches) >= 7, "Expected at least 7 embedded figures!"
print("\nALL 7 VISUAL ANALYTICS FIGURES SUCCESSFULLY VERIFIED IN PDF!")
