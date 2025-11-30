# from flask import Flask, request, jsonify
from quart import Quart, jsonify
from quart_cors import cors
import asyncio
import sys
# route imports
from routes.processing import processing_bp
from routes.settings import settings_bp
from routes.templates import templates_bp
from routes.baseline import baseline_bp

if sys.platform == "win32":
    # Avoid ProactorEventLoop socket bugs
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Notes
# ------
# run dev
    # hypercorn main:app --reload
# runs on port 8000
# ------

# main app 
app = Quart(__name__)
app = cors(app, allow_origin="*")  # replaces flask_cors

# Routes
app.register_blueprint(processing_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(templates_bp)
app.register_blueprint(baseline_bp)

@app.route("/", methods=["GET"])
async def home():
    return jsonify({"message": "Flask server is running!"})

if __name__ == "__main__":
    app.run(port=5000, debug=True, threaded=True)
