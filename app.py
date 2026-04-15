from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import re

app = Flask(__name__)
CORS(app)

HF_API_KEY = os.getenv("HF_TOKEN")

API_URL = "https://router.huggingface.co/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json"
}

chat_history = [
    {
        "role": "system",
        "content": "You are a helpful AI. Give clear, detailed answers without using markdown symbols like *, **, or bullet points."
    }
]

# 🧹 CLEAN TEXT FUNCTION
def clean_text(text):
    text = re.sub(r"\*\*", "", text)   # remove bold **
    text = re.sub(r"\*", "", text)     # remove *
    text = re.sub(r"#+", "", text)     # remove ###
    text = re.sub(r"`", "", text)      # remove `
    text = re.sub(r"- ", "", text)     # remove dash bullets
    return text.strip()

@app.route("/")
def index():
    return "Hello World by nova ai"

@app.route("/chat", methods=["POST"])
def chat():
    global chat_history

    data = request.json
    user_message = data.get("message")

    if not user_message:
        return jsonify({"reply": "No message provided"}), 400

    # ➕ Add user message to memory
    chat_history.append({
        "role": "user",
        "content": user_message
    })

    payload = {
        "model": "meta-llama/Meta-Llama-3-8B-Instruct",
        "messages": chat_history[-10:],   # 🔥 last 10 messages only
        "max_tokens": 800,                # 🔥 longer response
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

            # ➕ Save AI response to memory
            chat_history.append({
                "role": "assistant",
                "content": reply
            })

            # 🧹 Clean formatting
            cleaned_reply = clean_text(reply)

            return jsonify({"reply": cleaned_reply})

        # ❌ HF API ERROR
        elif "error" in result:
            return jsonify({
                "reply": f"HF ERROR: {result['error']['message']}"
            })

        # ❌ UNKNOWN ERROR
        else:
            return jsonify({
                "reply": "Unexpected response from AI"
            })

    except Exception as e:
        return jsonify({
            "reply": f"Server error: {str(e)}"
        }), 500


# 🔄 RESET CHAT (optional but useful)
@app.route("/reset", methods=["POST"])
def reset_chat():
    global chat_history

    chat_history = [
        {
            "role": "system",
            "content": "You are a helpful AI. Give clear, detailed answers without markdown symbols like *, **, or bullet points."
        }
    ]

    return jsonify({"message": "Chat reset successful"})


if __name__ == "__main__":
    app.run(debug=True)