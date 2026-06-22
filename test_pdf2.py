from fpdf import FPDF
from datetime import datetime

try:
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(0, 10, text="PhishGuard AI - Email Analysis Report", new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(10)
    
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 10, text=f"Date & Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, text="Analysis Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 10, text=f"Prediction Result: PHISHING", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
            
    # Email Content
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, text="Original Email Content", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=12)
    
    print("X before multi 1:", pdf.get_x())
    pdf.multi_cell(0, 10, text=f"Subject: Test Subject", new_x="LMARGIN", new_y="NEXT")
    print("X before multi 2:", pdf.get_x())
    pdf.multi_cell(0, 10, text=f"Body:\nTest body text here", new_x="LMARGIN", new_y="NEXT")
    
    pdf.output("test3.pdf")
    print("PDF generated successfully")
except Exception as e:
    import traceback
    traceback.print_exc()
