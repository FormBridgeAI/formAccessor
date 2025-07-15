import json
from fpdf import FPDF
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "server"))
from sample import mock_schemas


schema = mock_schemas[1]

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

pdf.cell(0, 10, f"{schema['formTitle']}", ln=True, align='C')
pdf.cell(0, 10, f"Form ID: {schema['formId']}", ln=True, align='C')
pdf.ln(10)

for field in schema['fields']:
    label = field.get("label", "Unknown Field")
    field_type = field.get("type", "Unknown Type")
    required = "Required" if field.get("required") else "Optional"
    options = field.get("options")
    pdf.cell(0, 10, f"{label} ({field_type}) - {required}", ln=True)
    if options:
        pdf.cell(0, 10, f"Options: {', '.join(options)}", ln=True)
    hint = field.get("accessibility", {}).get("screenReaderHint")
    if hint:
        pdf.cell(0, 10, f"Hint: {hint}", ln=True)
    pdf.ln(2)

pdf.output("medical_intake_form.pdf")
print("PDF generated: medical_intake_form.pdf")