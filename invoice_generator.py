from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

def create_invoice_pdf(client, service, amount, currency, date):
    filename = f"invoice_{client.replace(' ', '_')}.pdf"
    os.makedirs("invoices", exist_ok=True)
    path = os.path.join("invoices", filename)

    c = canvas.Canvas(path, pagesize=A4)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(200, 800, "INVOICE")

    c.setFont("Helvetica", 12)
    c.drawString(100, 750, f"Client: {client}")
    c.drawString(100, 730, f"Service: {service}")
    c.drawString(100, 710, f"Amount: {amount} {currency}")
    c.drawString(100, 690, f"Date: {date}")
    c.drawString(100, 650, "Thank you for your business!")
    c.save()

    return path
