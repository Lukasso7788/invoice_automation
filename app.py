from flask import Flask, request, jsonify
from invoice_generator import create_invoice_pdf
from send_email import send_invoice_email
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

@app.route("/new_invoice", methods=["POST"])
def new_invoice():

    # ---------- RAW DEBUG LOGS ----------
    print("\n========== RAW LOGS ==========")
    print("Headers:", dict(request.headers))
    print("Form:", request.form.to_dict())
    print("JSON:", request.get_json(silent=True))
    print("================================\n")
    # ------------------------------------

    # ---------- 1. Пытаемся получить JSON ----------
    payload = request.get_json(silent=True)

    if payload:
        # либо payload["data"], либо сам JSON
        data = payload.get("data", payload)
    else:
        # ---------- 2. Если JSON нет — значит пришла форма ----------
        form = request.form.to_dict()

        data = {}

        # вариант A: Webflow format: data[client], data[email], ...
        for key, value in form.items():
            if key.startswith("data[") and key.endswith("]"):
                clean = key[5:-1]   # вырезает data[ и ]
                data[clean] = value

        # вариант B: вдруг поля пришли как обычные: client, email, etc.
        # (подстраховка)
        for key, value in form.items():
            if key not in data and "[" not in key:
                data[key] = value

    print("📥 Получены данные (после парсинга):", data)

    # ---------- 3. Достаём поля ----------
    client = data.get("client")
    service = data.get("service")
    amount = data.get("amount")
    currency = data.get("currency")
    date = data.get("date")
    email = data.get("email")

    # ---------- 4. Проверяем ----------
    if not all([client, service, amount, currency, email]):
        print("❌ Ошибка: нет нужных полей!")
        return jsonify({"error": "missing fields"}), 400

    # ---------- 5. Генерация PDF ----------
    pdf_path = create_invoice_pdf(client, service, amount, currency, date)

    # ---------- 6. Отправка email ----------
    send_invoice_email(email, client, pdf_path, amount, currency, service)

    return jsonify({"status": "ok", "client": client, "pdf": pdf_path})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
