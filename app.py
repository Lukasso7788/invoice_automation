import os
import sys
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from invoice_generator import create_invoice_pdf
from send_email import send_invoice_email

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

load_dotenv()
app = Flask(__name__)


def parse_webflow_json(payload):
    """Парсинг Webflow JSON → data[...] поля"""
    real = {}

    wf_data = payload.get("payload", {}).get("data", {})

    for key, value in wf_data.items():
        if key.startswith("data[") and key.endswith("]"):
            clean = key[5:-1]
            real[clean] = value

    return real


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

    # -------- CASE 1: JSON от Webflow ----------
    if json_payload and "payload" in json_payload:
        log.info("Detected Webflow JSON format")
        data = parse_webflow_json(json_payload)

    # -------- CASE 2: обычная форма ----------
    elif form:
        log.info("Detected Webflow form-data format")
        for key, value in form.items():
            if key.startswith("data[") and key.endswith("]"):
                data[key[5:-1]] = value
            else:
                data[key] = value

    # -------- CASE 3: fallback ----------
    else:
        log.info("Fallback parse")
        for pair in raw.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                k = k.replace("data[", "").replace("]", "")
                data[k] = v.replace("+", " ")

    log.info("📥 FINAL PARSED DATA: %s", data)

    # -------- Extract fields ----------
    client = data.get("client")
    service = data.get("service")
    amount = data.get("amount")
    currency = data.get("currency")
    date = data.get("date")
    email = data.get("email")

    if not all([client, service, amount, currency, email]):
        log.error("❌ Missing fields!")
        return jsonify({"error": "missing fields", "received": data}), 400

    pdf_path = create_invoice_pdf(client, service, amount, currency, date)
    send_invoice_email(email, client, pdf_path, amount, currency, service, stripe_url)

    return jsonify({"status": "ok", "data": data, "pdf": pdf_path})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
