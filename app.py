from flask import Flask, request, jsonify
from invoice_generator import create_invoice_pdf
from send_email import send_invoice_email
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

@app.route("/new_invoice", methods=["POST"])
def new_invoice():
    data = request.form or request.get_json() or {}
    print("📥 Получены данные:", data)

    client = data.get("client")
    service = data.get("service")
    amount = data.get("amount")
    currency = data.get("currency")
    date = data.get("date")
    email = data.get("email")

    if not all([client, service, amount, currency, email]):
        return jsonify({"error": "missing fields"}), 400

    pdf_path = create_invoice_pdf(client, service, amount, currency, date)
    send_invoice_email(email, client, pdf_path, amount, currency, service)

    return jsonify({"status": "ok", "client": client, "pdf": pdf_path})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
