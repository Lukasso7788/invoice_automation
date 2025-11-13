from flask import Flask, request, jsonify
from invoice_generator import create_invoice_pdf
from send_email import send_invoice_email
import os
from dotenv import load_dotenv
import logging
import sys

# ---------- ЛОГИ ----------
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)
# --------------------------

load_dotenv()
app = Flask(__name__)

@app.route("/new_invoice", methods=["POST"])
def new_invoice():

    log.info("=========== NEW REQUEST ===========")

    log.info("Headers: %s", dict(request.headers))
    log.info("RAW BODY: %s", request.get_data().decode(errors="ignore"))
    log.info("Form: %s", request.form.to_dict())
    log.info("JSON: %s", request.get_json(silent=True))

    data = {}

    # ---------- 1. JSON ----------
    payload = request.get_json(silent=True)
    if payload:
        log.info("Detected JSON payload")
        data = payload.get("data", payload)

    # ---------- 2. Form ----------
    elif request.form:
        log.info("Detected FORM payload")
        form = request.form.to_dict()

        for key, value in form.items():
            if key.startswith("data[") and key.endswith("]"):
                data[key[5:-1]] = value

            # fallback
            elif "[" not in key:
                data[key] = value

    # ---------- 3. RAW URLENCODED ----------
    else:
        raw = request.get_data().decode(errors="ignore")
        if raw:
            log.info("Detected RAW urlencoded payload")
            pairs = raw.split("&")
            for pair in pairs:
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    k = k.replace("data[", "").replace("]", "")
                    data[k] = v.replace("+", " ")

    log.info("Parsed DATA: %s", data)

    # ---------- Extract ----------
    client = data.get("client")
    service = data.get("service")
    amount = data.get("amount")
    currency = data.get("currency")
    date = data.get("date")
    email = data.get("email")

    if not all([client, service, amount, currency, email]):
        log.error("❌ Missing fields: %s", data)
        return jsonify({"error": "missing fields"}), 400

    pdf_path = create_invoice_pdf(client, service, amount, currency, date)
    send_invoice_email(email, client, pdf_path, amount, currency, service)

    return jsonify({"status": "ok", "client": client})
