import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import stripe

load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")

stripe.api_key = STRIPE_API_KEY


def create_payment_link(amount, currency, description):
    # Stripe принимает сумму в центах: 25.00$ → 2500
    amount_cents = int(float(amount) * 100)

    payment_link = stripe.PaymentLink.create(
        line_items=[{
            "price_data": {
                "currency": currency.lower(),
                "product_data": {"name": description},
                "unit_amount": amount_cents
            },
            "quantity": 1
        }]
    )
    return payment_link.url


def send_invoice_email(recipient, client, pdf_path, amount, currency, service):
    # создаём платёжную ссылку
    link = create_payment_link(amount, currency, f"{service} — {client}")

    msg = EmailMessage()
    msg["Subject"] = f"Invoice for {client}"
    msg["From"] = EMAIL_SENDER
    msg["To"] = recipient

    msg.set_content(
        f"Hi {client},\n\n"
        f"Here is your invoice for *{service}*.\n\n"
        f"Amount due: {amount} {currency}\n\n"
        f"💳 Pay here: {link}\n\n"
        f"Thank you!"
    )

    # attach PDF
    with open(pdf_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(pdf_path)
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

    print(f"📤 Invoice sent to {recipient}")
    print(f"💳 Stripe link: {link}")
