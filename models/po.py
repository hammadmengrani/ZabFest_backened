from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def add_name_only(name, title, phone, email, address, date, po_number, products, tax, shipping, payment_method, payment_date, notes):
    input_pdf = "D:/Zab Fest Projext/backened/PO.pdf"

    pdf_reader = PdfReader(input_pdf)
    pdf_writer = PdfWriter()
    page = pdf_reader.pages[0]

    # Calculate total dynamically
    products_total = 0
    for product in products[:7]:
        # sale_price * quantity
        try:
            sale_price = float(product.get("sale_price", 0))
            quantity = float(product.get("quantity", 0))
        except Exception:
            sale_price = 0
            quantity = 0
        products_total += sale_price * quantity

    try:
        tax_val = float(tax)
    except Exception:
        tax_val = 0

    try:
        shipping_val = float(shipping)
    except Exception:
        shipping_val = 0

    total = products_total + tax_val + shipping_val

    # Create overlay PDF in memory
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Add Name & Contact Info
    can.setFont("Helvetica", 14)
    can.drawString(80, 670, str(name))
    can.drawString(90, 645, str(title))
    can.drawString(85, 615, str(phone))
    can.drawString(80, 590, str(email))
    can.drawString(80, 562, str(address))

    # PO details
    can.setFont("Helvetica", 12)
    can.drawString(510, 712, str(date))
    can.drawString(365, 712, str(po_number))

    # Product details (first 7 only)
    y_positions = [395, 374, 352, 332, 310, 288, 265]
    for i, product in enumerate(products[:7]):
        y = y_positions[i]
        can.setFont("Helvetica", 12)
        can.drawString(120, y, str(product["name"]))
        can.drawString(312, y, str(product["quantity"]))
        can.drawString(348, y, str(product.get("price", "")))
        can.drawString(430, y, str(product.get("sale_price", "")))
        # Calculate total per product line
        try:
            line_total = float(product.get("sale_price", 0)) * float(product.get("quantity", 0))
        except Exception:
            line_total = 0
        can.drawString(510, y, str(round(line_total, 2)))

    # Tax, Shipping, Total
    can.setFont("Helvetica-Bold", 12)
    can.drawString(510, 243, str(tax))      # numeric tax as string
    can.drawString(510, 220, str(shipping)) # numeric shipping as string
    can.drawString(510, 198, str(round(total, 2)))

    # Payment info
    can.setFont("Helvetica", 12)
    can.drawString(180, 105, str(payment_method))
    can.drawString(180, 83, str(payment_date))

    # Notes
    can.drawString(350, 70, str(notes))

    can.save()
    packet.seek(0)

    # Merge overlay with original PDF page
    overlay_pdf = PdfReader(packet)
    overlay_page = overlay_pdf.pages[0]
    page.merge_page(overlay_page)
    pdf_writer.add_page(page)

    # Write final PDF to in-memory BytesIO
    output_stream = BytesIO()
    pdf_writer.write(output_stream)
    output_stream.seek(0)

    print("✅ PDF generated in memory with calculated total.")
    return output_stream
