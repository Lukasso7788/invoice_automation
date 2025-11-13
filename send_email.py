import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_invoice_email(recipient, client, pdf_path):
    msg = EmailMessage()
    msg["Subject"] = f"Invoice for {client}"
    msg["From"] = EMAIL_SENDER
    msg["To"] = recipient
    msg.set_content(f"Hi {client},\n\nHere is your invoice. Please see the attachment.\n\nBest regards,\nLukasso Design")

    with open(pdf_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=os.path.basename(pdf_path))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)
