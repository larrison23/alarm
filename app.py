import os
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from homebridge_api import HomebridgeClient

load_dotenv()

app = Flask(__name__)

hb_client = HomebridgeClient(
    base_url=os.getenv("HB_BASE_URL"),
    username=os.getenv("HB_USERNAME"),
    password=os.getenv("HB_PASSWORD")
)

@app.route("/")
def index():
    """Creates a HTML page with the current alarm time displayed"""
    current_time = hb_client.get_alarm_time()
    return render_template("index.html", current_time=current_time)

@app.route("/set-alarm-time", methods=["POST"])
def set_alarm_time():
    """Sets the alarm time"""
    data = request.get_json()
    if not data or 'time' not in data:
        return jsonify({"error": "No time provided"}), 400
    
    alarm_time = data.get('time')

    try:
        success = hb_client.update_morning_alarm(alarm_time)
        if success:
            return jsonify({"message": "Homebridge updated"}), 200
        else:
            return jsonify({"error": "Failed to update Homebridge config"}), 500
    except Exception as e:
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
    