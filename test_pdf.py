from fpdf import FPDF

try:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text="Body:\nTest body")
    pdf.output("test.pdf")
    print("PDF generated successfully with 'text'")
except Exception as e:
    print(f"Error with 'text': {e}")

try:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt="Body:\nTest body")
    pdf.output("test2.pdf")
    print("PDF generated successfully with 'txt'")
except Exception as e:
    print(f"Error with 'txt': {e}")
