import os
import sys
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from invoice_generator import create_invoice_pdf
from send_email import send_invoice_email

# ==========================
# Настройка логов (работает на Render)
# ==========================
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

load_dotenv()
app = Flask(__name__)

# ==========================
# Helper: парсинг Webflow form-data
# ==========================
def parse_webflow_form():
    form = request.form.to_dict()
    parsed = {}

    # data[client], data[email] → client, email
    for key, value in form.items():
        if key.startswith("data[") and key.endswith("]"):
            clean = key[5:-1]
            parsed[clean] = value

    # fallback: обычные ключи
    for key, value in form.items():
        if key not in parsed and "[" not in key:
            parsed[key] = value

    return parsed


# ==========================
#      MAIN ENDPOINT
# ==========================
@app.route("/new_invoice", methods=["POST"])
def new_invoice():

    log.info("\n========== NEW REQUEST ==========")
    log.info("Headers: %s", dict(request.headers))
    raw = request.get_data().decode(errors="ignore")
    log.info("RAW BODY: %s", raw)
    log.info("Form: %s", request.form.to_dict())
    log.info("JSON: %s", request.get_json(silent=True))

    data = {}

    # ---------- 1. JSON ----------
    payload = request.get_json(silent=True)
    if payload:
        log.info("Detected JSON payload")
        data = payload.get("data", payload)

    # ---------- 2. FORM-DATA ----------
    elif request.form:
        log.info("Detected Webflow form-data")
        data = parse_webflow_form()

    # ---------- 3. RAW fallback ----------
    else:
        log.info("Fallback parse (RAW urlencoded)")
        pairs = raw.split("&")
        for pair in pairs:
            if "=" in pair:
                k, v = pair.split("=", 1)
                k = k.replace("data[", "").replace("]", "")
                data[k] = v.replace("+", " ")

    log.info("📥 Parsed DATA: %s", data)

    # ---------- 4. Extract ----------
    client = data.get("client")
    service = data.get("service")
    amount = data.get("amount")
    currency = data.get("currency")
    date = data.get("date")
    email = data.get("email")

    # ---------- 5. Validation ----------
    if not all([client, service, amount, currency, email]):
        log.error("❌ Missing fields: %s", data)
        return jsonify({"error": "missing fields", "got": data}), 400

    # ---------- 6. PDF ----------
    pdf_path = create_invoice_pdf(client, service, amount, currency, date)

    # ---------- 7. Email ----------
    send_invoice_email(email, client, pdf_path, amount, currency, service)

    return jsonify({
        "status": "ok",
        "client": client,
        "service": service,
        "email": email,
        "pdf": pdf_path
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
