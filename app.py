import os
import sys
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import stripe

from invoice_generator import create_invoice_pdf
from send_email import send_invoice_email

# ----------------------------------------------------
# Logging setup
# ----------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ----------------------------------------------------
# Load environment variables
# ----------------------------------------------------
load_dotenv()
app = Flask(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


# ----------------------------------------------------
# Parsing Webflow JSON → clean fields
# ----------------------------------------------------
def parse_webflow_json(payload):
    fields = {}
    wf_data = payload.get("payload", {}).get("data", {})

    for key, value in wf_data.items():
        if key.startswith("data[") and key.endswith("]"):
            clean = key[5:-1]
            fields[clean] = value

    return fields


# ----------------------------------------------------
# Main endpoint
# ----------------------------------------------------
@app.route("/new_invoice", methods=["POST"])
def new_invoice():

    log.info("\n========== NEW REQUEST ==========")
    log.info("Headers: %s", dict(request.headers))

    raw = request.get_data().decode(errors="ignore")
    log.info("RAW BODY: %s", raw)

    form = request.form.to_dict()
    log.info("Form: %s", form)

    json_payload = request.get_json(silent=True)
    log.info("JSON: %s", json_payload)

    data = {}

    # -------- Case 1: Webflow JSON ----------
    if json_payload and "payload" in json_payload:
        log.info("Detected Webflow JSON format")
        data = parse_webflow_json(json_payload)

    # -------- Case 2: Form data ----------
    elif form:
        log.info("Detected Webflow form-data format")
        for key, value in form.items():
            if key.startswith("data[") and key.endswith("]"):
                data[key[5:-1]] = value
            else:
                data[key] = value

    # -------- Case 3: Raw fallback ----------
    else:
        log.info("Fallback parse (rare case)")
        for pair in raw.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                k = k.replace("data[", "").replace("]", "")
                data[k] = v.replace("+", " ")

    log.info("📥 FINAL PARSED DATA: %s", data)

    # ----------------------------------------------------
    # Extract required fields
    # ----------------------------------------------------
    client = data.get("client")
    service = data.get("service")
    amount = data.get("amount")
    currency = data.get("currency")
    date = data.get("date")
    email = data.get("email")

    if not all([client, service, amount, currency, email]):
        log.error("❌ Missing fields!")
        return jsonify({"error": "missing fields", "received": data}), 400

    # ----------------------------------------------------
    # Create invoice PDF
    # ----------------------------------------------------
    pdf_path = create_invoice_pdf(client, service, amount, currency, date)
    log.info("📄 PDF created: %s", pdf_path)

    # ----------------------------------------------------
    # Create Stripe Payment Link
    # ----------------------------------------------------
    try:
        payment_link = stripe.PaymentLink.create(
            line_items=[{
                "price_data": {
                    "currency": currency.lower(),
                    "unit_amount": int(float(amount) * 100),
                    "product_data": {"name": service}
                },
                "quantity": 1
            }],
            after_completion={"type": "redirect", "redirect": {"url": "https://google.com"}}
        )

        stripe_url = payment_link["url"]
        log.info("💳 Stripe Payment Link: %s", stripe_url)

    except Exception as e:
        log.error("❌ Stripe error: %s", e)
        return jsonify({"error": "stripe_failed", "details": str(e)}), 500

    # ----------------------------------------------------
    # Send invoice email through Resend
    # ----------------------------------------------------
    email_ok = send_invoice_email(
        email,
        client,
        pdf_path,
        amount,
        currency,
        service,
        stripe_url
    )

    if not email_ok:
        log.error("❌ Email sending failed")
        return jsonify({"error": "email_failed"}), 500

    log.info("✅ Invoice processed successfully")

    return jsonify({
        "status": "ok",
        "stripe_url": stripe_url,
        "pdf": pdf_path,
        "data": data
    })


# ----------------------------------------------------
# Run server
# ----------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
