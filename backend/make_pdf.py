from fpdf import FPDF

def create_pdf(content, filename="Class_Notes.pdf"):
    pdf = FPDF()
    pdf.add_page()
    
    # Set a nice font
    pdf.set_font("Arial", size=12)
    
    # Add a Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Smart Classroom - AI Generated Notes", ln=True, align='C')
    pdf.ln(10) # Line break
    
    # Add the Content
    pdf.set_font("Arial", size=11)
    # multi_cell is great for long paragraphs
    pdf.multi_cell(0, 10, txt=content)
    
    # Save the file
    pdf.output(filename)
    print(f"✅ Success! Your PDF is ready: {filename}")

# --- TEST IT ---
# We will use the text you saved yesterday in 'class_summary.txt'
try:
    with open("class_summary.txt", "r") as f:
        saved_text = f.read()
    create_pdf(saved_text)
except FileNotFoundError:
    print("Run your read_board.py first to generate the text file!")
