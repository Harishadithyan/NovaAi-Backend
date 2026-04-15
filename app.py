from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import re

app = Flask(__name__)

# ✅ Proper CORS setup
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# 🔐 HuggingFace API Key
HF_API_KEY = os.getenv("HF_TOKEN")

API_URL = "https://router.huggingface.co/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json"
}

# 🧠 Chat Memory
chat_history = [
    {
        "role": "system",
        "content": "You are a helpful AI. Give clear, detailed answers without using markdown symbols like *, **, or bullet points."
    }
]

# 🧹 CLEAN TEXT FUNCTION
def clean_text(text):
    text = re.sub(r"\*\*", "", text)
    text = re.sub(r"\*", "", text)
    text = re.sub(r"#+", "", text)
    text = re.sub(r"`", "", text)
    text = re.sub(r"- ", "", text)
    return text.strip()

# ✅ FORCE CORS HEADERS (IMPORTANT FOR RENDER)
@app.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

# 🚀 CHAT ENDPOINT
@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    global chat_history

    # ✅ Handle preflight request
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.json
    user_message = data.get("message")

    if not user_message:
        return jsonify({"reply": "No message provided"}), 400

    # ➕ Add user message
    chat_history.append({
        "role": "user",
        "content": user_message
    })

    payload = {
        "model": "meta-llama/Meta-Llama-3-8B-Instruct",
        "messages": chat_history[-10:],  # last 10 messages
        "max_tokens": 800,
        "temperature": 0.7
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)

        print("STATUS:", response.status_code)
        print("RAW RESPONSE:", response.text)

        result = response.json()

        # ✅ SUCCESS
        if "choices" in result:
            reply = result["choices"][0]["message"]["content"]

            chat_history.append({
                "role": "assistant",
                "content": reply
            })

            cleaned_reply = clean_text(reply)

            return jsonify({"reply": cleaned_reply})

        # ❌ HF ERROR
        elif "error" in result:
            return jsonify({
                "reply": f"HF ERROR: {result['error']['message']}"
            })

        # ❌ UNKNOWN
        else:
            return jsonify({
                "reply": "Unexpected response from AI"
            })

    except Exception as e:
        return jsonify({
            "reply": f"Server error: {str(e)}"
        }), 500


# 🔄 RESET CHAT
@app.route("/reset", methods=["POST", "OPTIONS"])
def reset_chat():
    global chat_history

    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    chat_history = [
        {
            "role": "system",
            "content": "You are a helpful AI. Give clear, detailed answers without using markdown symbols like *, **, or bullet points."
        }
    ]

    return jsonify({"message": "Chat reset successful"})


# 🌍 ROOT CHECK (optional but useful)
@app.route("/", methods=["GET"])
def home():
    return "API is running"


# 🚀 RUN (Render uses gunicorn, so this is fallback)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)