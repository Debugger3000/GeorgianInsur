# from flask import Flask, request, jsonify
from quart import Quart, jsonify, render_template, send_from_directory
from quart_cors import cors
from hypercorn.middleware import ProxyFixMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix
import asyncio
import sys
import os
import json
from utils.general import write_json_async
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


app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# Routes
app.register_blueprint(processing_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(templates_bp)
app.register_blueprint(baseline_bp)

@app.route("/")
async def serve_index():
    return await send_from_directory("client", "index.html")

# ------
# Data Scaffold functions on server start up

def ensure_data_directories():
    base_dir="/tmp/data"
    categories = ["ACCOUNTING", "ESL", "ILAC", "POST"]

    # Top-level directories
    baseline_dir = os.path.join(base_dir, "baseline")
    populated_dir = os.path.join(base_dir, "populated_templates")
    templates_dir = os.path.join(base_dir, "templates")

    # Create base structure
    os.makedirs(baseline_dir, exist_ok=True)
    os.makedirs(populated_dir, exist_ok=True)
    os.makedirs(templates_dir, exist_ok=True)

    # Create category subdirectories
    for category in categories:
        os.makedirs(os.path.join(populated_dir, category), exist_ok=True)
        os.makedirs(os.path.join(templates_dir, category), exist_ok=True)

    print("Data Directories successfully created!")



async def ensure_config_json():
    base_dir="/tmp/data"
    filename="config.json"
    config_path = os.path.join(base_dir, filename)

    # Do not overwrite if it already exists
    # if os.path.exists(config_path):
    #     return config_path

    config_data = {
        "insurance_targets": {
            "fall": "",
            "winter": "",
            "summer": "",
            "fall_post": "",
            "winter_post": "",
            "summer_post": ""
        },
        "baseline_props": {
            "path": "",
            "name": "",
            "row_count": "",
            "created_at": "",
            "updated_at": ""
        },
        "template_props": {
            "ACCOUNTING": "",
            "ESL": "",
            "ILAC": "",
            "POST": ""
        },
        "process_filtering": {},
        "populated_templates": {
            "ACCOUNTING": "",
            "ESL": "",
            "ILAC": "",
            "POST": ""
        }
    }

    # Ensure parent directory exists (safe even if already created)
    os.makedirs(base_dir, exist_ok=True)

    await write_json_async(config_path, config_data)

    # with open(config_path, "w", encoding="utf-8") as f:
    #     json.dump(config_data, f, indent=4)


    print("Config file successfully created !")




@app.before_serving
async def create_data_directory():

    print("===== SERVER FILESYSTEM DEBUG =====", flush=True)

    print("CWD:", os.getcwd(), flush=True)
    print("UID:", os.getuid(), "GID:", os.getgid(), flush=True)

    print("Root dir:", os.listdir("/"), flush=True)

    if os.path.exists("/tmp"):
        print("/tmp exists", flush=True)
        print("/tmp contents:", os.listdir("/tmp"), flush=True)
    else:
        print("/tmp DOES NOT EXIST", flush=True)

    # Show permissions
    print("/tmp perms:", oct(os.stat("/tmp").st_mode), flush=True)

    print("===================================", flush=True)

    try:
        ensure_data_directories()
        print("/tmp contents:", os.listdir("/tmp/data"), flush=True)
        print("/tmp contents:", os.listdir("/tmp/data/templates"), flush=True)
    except Exception as error:
        print("Error in scaffolding data directories for excel files.")
        print(error)
        return jsonify({
            "status": False,
            "message": str(error)
        }), 500
    
    try:
        await ensure_config_json()

        # Print full contents safely
        if os.path.exists("/tmp/data/config.json"):
            with open("/tmp/data/config.json", "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    print("Config.json contents:", json.dumps(data, indent=4), flush=True)
                except json.JSONDecodeError as e:
                    print("Config.json exists but is invalid JSON!", flush=True)
                    raw = f.read()
                    print("Raw contents:", repr(raw), flush=True)
        else:
            print("Config.json file does not exist!", flush=True)

    except Exception as error:
        print("Error in scaffolding config.json file.")
        print(error)
        return jsonify({
            "status": False,
            "message": str(error)
        }), 500
    


# -------




app = ProxyFixMiddleware(app, mode="legacy", trusted_hops=1)

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
