from flask import Flask, request, jsonify
from invoice_generator import create_invoice_pdf
from send_email import send_invoice_email
import os

app = Flask(__name__)

@app.route("/new_invoice", methods=["POST"])
def new_invoice():
    data = request.get_json().get("data", {})
    print("📥 Получены данные:", data)

    client = data.get("client")
    service = data.get("service")
    amount = data.get("amount")
    currency = data.get("currency")
    date = data.get("date")
    email = data.get("email")

    if not all([client, service, amount, currency, email]):
        return jsonify({"error": "missing fields"}), 400

    # создаём PDF
    pdf_path = create_invoice_pdf(client, service, amount, currency, date)
    print("✅ PDF создан:", pdf_path)

    # отправляем email
    send_invoice_email(email, client, pdf_path)
    print("📤 Email отправлен:", email)

    return jsonify({"status": "ok", "client": client, "pdf": pdf_path})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
