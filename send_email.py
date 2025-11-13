import os
import base64
import requests

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = os.getenv("SENDER_NAME", "Invoice Automation Bot")


def send_invoice_email(to_email, client, pdf_path, amount, currency, service, stripe_url):
    """
    Отправляет email через Resend API с PDF-вложением.
    """

    url = "https://api.resend.com/emails"

    # HTML письмо
    html = f"""
    <div style="font-family: Arial; padding: 20px;">
        <h2>Hello, {client} 👋</h2>
        <p>Here is your invoice for: <b>{service}</b></p>
        <p><b>Amount:</b> {amount} {currency}</p>

        <p>You can complete payment securely using Stripe:</p>

        <a href="{stripe_url}"
           style="background:#635BFF;color:white;padding:12px 20px;
                  border-radius:6px;text-decoration:none;font-size:16px;">
            Pay Invoice
        </a>

        <p style="margin-top:25px;">PDF invoice is attached.</p>
    </div>
    """

    # PDF → base64
    with open(pdf_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode()

    attachments = [
        {
            "filename": os.path.basename(pdf_path),
            "content": pdf_data,
            "type": "application/pdf"
        }
    ]

    payload = {
        "from": f"{SENDER_NAME} <{SENDER_EMAIL}>",
        "to": [to_email],
        "subject": "Your Invoice",
        "html": html,
        "attachments": attachments
    }

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post(url, json=payload, headers=headers)

    print("📧 Resend response:", r.status_code, r.text)

    return r.status_code == 200
