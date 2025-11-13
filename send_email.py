import os
import base64
import requests
import logging

log = logging.getLogger(__name__)

# ---- Load ENV ----
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = os.getenv("SENDER_NAME", "Invoice Automation Bot")

# ---- Safety Checks ----
if not RESEND_API_KEY:
    log.error("❌ ERROR: RESEND_API_KEY отсутствует в Render Environment Variables!")
if not SENDER_EMAIL:
    log.error("❌ ERROR: SENDER_EMAIL отсутствует в переменных окружения!")


def send_invoice_email(to_email, client, pdf_path, amount, currency, service, stripe_url):
    """
    Отправляет email через Resend API, прикладывая PDF-инвойс + Stripe payment link.
    """

    if not RESEND_API_KEY:
        log.error("❌ НЕТ API КЛЮЧА RESEND → email отправить невозможно.")
        return False

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
    try:
        with open(pdf_path, "rb") as f:
            pdf_data = base64.b64encode(f.read()).decode()
    except Exception as e:
        log.error(f"❌ Ошибка чтения PDF: {e}")
        return False

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

    try:
        response = requests.post("https://api.resend.com/emails", json=payload, headers=headers)
    except Exception as e:
        log.error(f"❌ Ошибка HTTP запроса к Resend: {e}")
        return False

    log.info(f"📧 Resend response: {response.status_code} {response.text}")

    if response.status_code in (200, 202):
        log.info("✅ Email sent successfully")
        return True
    else:
        log.error(f"❌ Email sending failed: {response.text}")
        return False
