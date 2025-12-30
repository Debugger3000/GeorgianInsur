# from flask import Flask, request, jsonify
from quart import Quart, jsonify, render_template, send_from_directory
from quart_cors import cors
from hypercorn.middleware import ProxyFixMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix
import asyncio
import sys
import os
# route imports
from routes.processing import processing_bp
from routes.settings import settings_bp
from routes.templates import templates_bp
from routes.baseline import baseline_bp

if sys.platform == "win32":
    # Avoid ProactorEventLoop socket bugs
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

port = int(os.environ.get("PORT", 8080))

# Notes
# ------
# run dev
    # hypercorn main:app --reload
# runs on port 8000
# ------

# main app 
app = Quart(__name__, static_folder="client", static_url_path="")

app = cors(app, allow_origin="*")  # replaces flask_cors



# fixed_app = ProxyFixMiddleware(app, mode="legacy", trusted_hops=1)

# redirected_app = HTTPToHTTPSRedirectMiddleware(app, host="example.com")

# app.asgi_app = ProxyFix(
#     app.asgi_app,
#     x_proto=1,
#     x_host=1,
# )

app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# Routes
app.register_blueprint(processing_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(templates_bp)
app.register_blueprint(baseline_bp)

# @app.route("/", methods=["GET"])
# async def home():
#     return jsonify({"message": "Flask server is running!"})

@app.route("/")
async def serve_index():
    return await send_from_directory("client", "index.html")


app.asgi_app = ProxyFixMiddleware(app.asgi_app, mode="legacy", trusted_hops=1)

# @app.route("/")
# async def index():
#     return await render_template("index.html")

# # Serve static JS/CSS files
# @app.route("/static/<path:filename>")
# async def static_files(filename):
#     return await send_from_directory("static", filename)

# For Development. As .run() forces dev features
# if __name__ == "__main__":
#     app.run(host="0.0.0.0",port=port, debug=False)
