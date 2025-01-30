from flask import Flask, request, jsonify, send_from_directory
import os
import subprocess
import sqlite3

app = Flask(__name__)

EXTRACTED_DIR = "extracted/"
WHATSAPP_DB_PATH = os.path.join(EXTRACTED_DIR, "msgstore.db")

# Allow frontend access
from flask_cors import CORS
CORS(app)

# ADB Connect
@app.route("/connect", methods=["POST"])
def connect_device():
    data = request.json
    ip = data.get("ip")
    
    if not ip:
        return jsonify({"error": "IP address required"}), 400
    
    try:
        subprocess.run(["adb", "connect", f"{ip}:5555"], check=True)
        return jsonify({"message": "Connected successfully"})
    except subprocess.CalledProcessError:
        return jsonify({"error": "Failed to connect to device"}), 500

# Extract WhatsApp Chats
@app.route("/extract/whatsapp", methods=["GET"])
def extract_whatsapp_chats():
    try:
        subprocess.run(["adb", "pull", "/data/data/com.whatsapp/databases/msgstore.db", EXTRACTED_DIR], check=True)
        return jsonify({"message": "WhatsApp chat database extracted successfully"})
    except subprocess.CalledProcessError:
        return jsonify({"error": "Failed to extract WhatsApp data"}), 500

# Read WhatsApp Chats
@app.route("/chats", methods=["GET"])
def get_chats():
    if not os.path.exists(WHATSAPP_DB_PATH):
        return jsonify({"error": "WhatsApp database not found"}), 404
    
    conn = sqlite3.connect(WHATSAPP_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_list.key_remote_jid, messages.data FROM messages JOIN chat_list ON messages.key_remote_jid = chat_list.key_remote_jid;")
    
    chats = cursor.fetchall()
    conn.close()
    
    return jsonify({"chats": chats})

# Search for a Keyword in Chats
@app.route("/search", methods=["POST"])
def search_keyword():
    data = request.json
    keyword = data.get("keyword")
    
    if not keyword:
        return jsonify({"error": "Keyword required"}), 400
    
    conn = sqlite3.connect(WHATSAPP_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_list.key_remote_jid, messages.data FROM messages JOIN chat_list ON messages.key_remote_jid = chat_list.key_remote_jid WHERE messages.data LIKE ?;", (f"%{keyword}%",))
    
    results = cursor.fetchall()
    conn.close()
    
    return jsonify({"matches": results})

# Extract Media
@app.route("/extract/media", methods=["GET"])
def extract_media():
    try:
        subprocess.run(["adb", "pull", "/sdcard/WhatsApp/Media", EXTRACTED_DIR], check=True)
        return jsonify({"message": "Media files extracted successfully"})
    except subprocess.CalledProcessError:
        return jsonify({"error": "Failed to extract media files"}), 500

# Display Media
@app.route("/media/<filename>")
def get_media(filename):
    return send_from_directory(os.path.join(EXTRACTED_DIR, "WhatsApp/Media"), filename)

if __name__ == "__main__":
    app.run(debug=True)
