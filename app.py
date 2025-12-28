import json
import os
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
STATE_FILE = "state.json"

def get_saved_time():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f).get("last_time", "7:00")
    return "07:00"

def save_time(new_time):
    with open(STATE_FILE, "w") as f:
        json.dump({"last_time": new_time}, f)

@app.route("/")
def index():
    current_time = get_saved_time()
    return render_template("index.html", current_time=current_time)

@app.route("/set-alarm-time", methods=["POST"])
def set_alarm_time():
    data = request.get_json()
    alarm_time = data.get('time')

    save_time(alarm_time)
    try:
        return jsonify({"message": "Homebridge updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    