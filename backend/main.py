# from flask import Flask, request, jsonify
from quart import Quart, request, jsonify, send_file, Blueprint
from quart_cors import cors
import os
import json
import pandas as pd
from io import BytesIO
import asyncio
import sys
from pathlib import Path
from routes.processing import processing_bp
from routes.settings import settings_bp
from utils.enums import Paths, Templates
from utils.general import get_download_path, delete_files, get_cur_time
from datetime import datetime

if sys.platform == "win32":
    # Avoid ProactorEventLoop socket bugs
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# run dev
# hypercorn main:app --reload
# runs on port 8000


app = Quart(__name__)
app = cors(app, allow_origin="*")  # replaces flask_cors

# Routes
app.register_blueprint(processing_bp)
app.register_blueprint(settings_bp)


# path enums  i guess
CONFIG_PATH = "./data/config.json"  # ← path to your JSON config file
baseline_config_name = "baseline_props"
BASELINE_PATH = "./data/baseline/"

# Setting enums
INSURANCE_TEMPLATE_OBJECT_NAME = "insurance_templates"
ACCOUNTING_TEMPLATE_OBJECT_NAME = "accounting_templates"
INSURANCE_TEMPLATE_PATH = "./data/templates/insurance/"
ACCOUNTING_TEMPLATE_PATH = "./data/templates/accounting/"
TEMPLATE_OBJECT_KEY = "template_props"



# write excel file to baseline folder for baselines UPLOAD
def write_file_sync(path, data):
    with open(path, "wb") as f:
        f.write(data)


    




# def write_json(path, data):
#     with open(path, "w", encoding="utf-8") as f:
#         print("before json dump")
#         json.dump(data, f, indent=4)
#         print("after json dump")


# JSON read / write functions
#-----------------------
# Your async-safe write function
async def write_json_async(path, data):
    # Run the blocking file write in a thread
    await asyncio.to_thread(write_json_sync, path, data)

# Helper functions
def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Blocking JSON write helper
def write_json_sync(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# write to baseline config json
# async def write_config(new_name_data):
#     # rename config.json as well
#     settings = await asyncio.to_thread(read_json, CONFIG_PATH)
#     print("after read json ret")
#     # update baseline config.json name
#     settings[baseline_config_name]["name"] = new_name_data+".xlsx"
#     # run coroutine task, to write to json for new baseline data
#     asyncio.create_task(write_json_async(CONFIG_PATH, settings))

#----------------------------


# get current baseline file path
async def get_baseline_path_async():
    settings = await asyncio.to_thread(read_json, CONFIG_PATH)

    # Step 2: Grab baseline filename from config
    baseline_filename = settings[baseline_config_name]["name"]

    # Step 3: Combine folder + filename
    baseline_file_path = os.path.join(BASELINE_PATH, baseline_filename)

    return baseline_file_path
#----------------------------

#----------------
# rename excel function



#-----------
# Baseline routes 
@app.route("/upload-baseline", methods=["POST"])
async def upload_baseline():
    print("upload baseline router.... flasker...")

    files = await request.files

    if "baseline_file" not in files:
        return jsonify({"error": "No baseline file found..."}), 400

    file = files["baseline_file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Read file data (blocking but fine; werkzeug already loaded into memory)
    file_data = file.read()
    filename = file.filename

    cur_time = get_cur_time()
    new_name = cur_time + "_BASELINE.xlsx"
    baseline_file_path = Paths.BASELINE_PATH.value + new_name

    # delete other baseline...
    delete_files(Paths.BASELINE_PATH.value)

    # Ensure storage folder exists
    os.makedirs(BASELINE_PATH, exist_ok=True)
    #dest_path = os.path.join(BASELINE_PATH, new_name)
    # Write file asynchronously (safe)
    await asyncio.to_thread(write_file_sync, baseline_file_path, file_data)

    # get dataframe for baseline excel file
    df = pd.read_excel(BytesIO(file_data))
    baseline_row_count = len(df)
    #baseline_name = filename

    # Step 1: Read JSON in a thread
    settings = await asyncio.to_thread(read_json, CONFIG_PATH)
    print("after read json ret")
    # Step 2: Update the dictionary
    settings[baseline_config_name]["name"] = new_name
    settings[baseline_config_name]["row_count"] = baseline_row_count

    # run coroutine task, to write to json for new baseline data
    asyncio.create_task(write_json_async(CONFIG_PATH, settings))

    print("Before returning response upload baseline")

    # Return baseline properties...
    result = {
        "status": True,
        "baseline_name" : new_name,
        "baseline_row_count" : baseline_row_count,
    }

    print(result)

    return jsonify(result)

@app.route("/get-baseline", methods=["GET"])
async def get_baseline():
    print("get baseline route hit")

    # to get excel file
    baseline_file_path = await get_baseline_path_async()
    print(baseline_file_path)

    # to get baseline name
    settings = await asyncio.to_thread(read_json, CONFIG_PATH)
    
    # get dataframe for baseline excel file
    df = pd.read_excel(baseline_file_path)

    baseline_row_count = len(df) # get baseline file row count
    baseline_name = settings[baseline_config_name]["name"] # get baseline file name

    date = format_date(baseline_name)
    
    # Return baseline properties...
    result = {
        "baseline_name" : baseline_name,
        "baseline_row_count" : baseline_row_count,
        "updated_at": date 
    }

    print(result)

    return jsonify(result)


@app.route("/download-baseline")
async def download_baseline():
    # grab baseline file_path
    baseline_file_path = await get_baseline_path_async()

    # grab baseline file config object
    settings = await asyncio.to_thread(read_json, CONFIG_PATH)
    baseline_name = settings[baseline_config_name]["name"] # get baseline file name

    # return excel file to browser client
    return await send_file(
        baseline_file_path,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        attachment_filename=baseline_name
    )

@app.route("/rename-baseline", methods=["POST"])
async def rename_baseline():
    print("Rename baseline route hit")

    try:
        # Grab JSON body from request
        data = await request.get_json()  # <-- automatically parses JSON
        if not data:
            return jsonify({"error": "No JSON body received in rename baseline"}), 400
        print(data)

        # {"new_baseline_name" : name}
        new_name_data = data["new_baseline_name"]
        new_full_path = BASELINE_PATH+new_name_data+".xlsx"

        # grab baseline file_path
        old_baseline_path = await get_baseline_path_async()

        # grab baseline file config object
        # settings = await asyncio.to_thread(read_json, CONFIG_PATH)
        # baseline_name = settings[baseline_config_name]["name"] # get baseline file name

        # rename baseline excel file
        os.rename(old_baseline_path, new_full_path)
        print(BASELINE_PATH+new_full_path)

        # rename config.json as well
        settings = await asyncio.to_thread(read_json, CONFIG_PATH)
        print("after read json ret")
        # update baseline config.json name
        settings[baseline_config_name]["name"] = new_name_data+".xlsx"

        # run coroutine task, to write to json for new baseline data
        asyncio.create_task(write_json_async(CONFIG_PATH, settings))


        # check to make sure both the excel in /baseline and config.json["name"] are the same value..
            # if not, we revert...

        


        # return excel file to browser client
        return jsonify({
            "status": True,
            "new_baseline_name": new_name_data+".xlsx",
            "message": "Baseline renamed successfully",
        })
    except Exception as error:
        print(error)
        return jsonify({
            "status": False,
            "message": str(error),
            "row_count": -1,
            # "new_row": new_row
        }), 500

#------------------------


# Settings
# -----



# templates

# helper to grab list of template names...
async def get_templates_helper():
    # json data - INSURANCE
    settings = await asyncio.to_thread(read_json, CONFIG_PATH)
    
    return {
        "accounting_templates": settings[TEMPLATE_OBJECT_KEY][ACCOUNTING_TEMPLATE_OBJECT_NAME],
        "insurance_templates": settings[TEMPLATE_OBJECT_KEY][INSURANCE_TEMPLATE_OBJECT_NAME]
    }

async def check_for_duplicates(key_name: str, file_name: str) -> bool:
    settings = await asyncio.to_thread(read_json, CONFIG_PATH)

    entries = settings[TEMPLATE_OBJECT_KEY].get(key_name, [])

    return file_name in entries
    
 
@app.route("/get-templates", methods=["GET"])
async def get_templates():
    try:
        # now add excel file to directory
        # INSURANCE_TEMPLATE_PATH

        templates = await get_templates_helper()

        insurance = templates[INSURANCE_TEMPLATE_OBJECT_NAME]
        accounting = templates[ACCOUNTING_TEMPLATE_OBJECT_NAME]

        # return excel file to browser client
        return jsonify({
            "status": True,
            "message": "Success",
            "accounting_templates": accounting,
            "insurance_templates": insurance
        })

    except Exception as error:
        print(error)
        return jsonify({
            "status": False,
            "message": str(error),
        }), 500
    

def ordinal(n):
    # 1st, 2nd, 3rd, 4th...
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def format_date(filename):
    # Example: "11-24-2025-21-38-33_POST_GuardMe_template.xlsx"
    month, day, year, hour, minute, second = filename.split("_")[0].split("-")

    dt = datetime(
        int(year), int(month), int(day),
        int(hour), int(minute), int(second)
    )

    # Format components
    formatted_time = dt.strftime("%I:%M%p").lower()   # "08:31am"
    formatted_date = dt.strftime("%B {DAY}, %Y")

    # Insert ordinal day
    formatted_date = formatted_date.replace("{DAY}", ordinal(dt.day))

    return f"{formatted_time} - {formatted_date}"

async def build_report_data(filenames):
    result = {}

    for key, filename in filenames.items():

        file_path, filename = await get_download_path(key)
        df = pd.read_excel(file_path)

        result[key] = {
            "date": format_date(filename),
            "row_count": len(df)
        }

    return result

async def get_template_data_helper():
    # json data - INSURANCE
    settings = await asyncio.to_thread(read_json, CONFIG_PATH)

    temp_object = settings[Templates.TEMPLATE_CONFIG_KEY.value]

    result = await build_report_data(temp_object)

    # pretty_dates = {key: extract_pretty_date(value) for key, value in temp_object.items()}

    return result

@app.route("/get-template-data", methods=["GET"])
async def get_templates_data():
    try:
        templates = await get_template_data_helper()

        # return excel file to browser client
        return jsonify({
            "status": True,
            "data": templates
        })

    except Exception as error:
        print(error)
        return jsonify({
            "status": False,
            "message": str(error),
        }), 500
    

@app.route("/upload-insurance-template", methods=["POST"])
async def upload_insurance_template():
    
    # Ensure file exists
    # key : insurance_template_file 
    
    files = await request.files

    if "insurance_template_file" not in files:
        return jsonify({"error": "No insurance template found..."}), 400

    file = files["insurance_template_file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    # now add excel file to directory
    # INSURANCE_TEMPLATE_PATH

    # Read file data (blocking but fine; werkzeug already loaded into memory)
    file_data = file.read()
    filename = file.filename

    # check make sure there is not a file with same name...
    result = await check_for_duplicates(INSURANCE_TEMPLATE_OBJECT_NAME, filename)
    # return 400, if template with same name already exists
    if result:
        return jsonify({
            "status": False,
            "message": "Template already exists",
        }), 400


    # Ensure storage folder exists
    os.makedirs(INSURANCE_TEMPLATE_PATH, exist_ok=True)
    dest_path = os.path.join(INSURANCE_TEMPLATE_PATH, filename)
    # Write file asynchronously (safe)
    await asyncio.to_thread(write_file_sync, dest_path, file_data)


    #---------------------
    # add excel file name into config.json
    settings = await asyncio.to_thread(read_json, CONFIG_PATH)
    print("after read json ret")
    # Step 2: Update the dictionary
    template_list: list[str] = settings[TEMPLATE_OBJECT_KEY][INSURANCE_TEMPLATE_OBJECT_NAME]
    template_list.append(filename)
    # run coroutine task, to write to json for new baseline data
    asyncio.create_task(write_json_async(CONFIG_PATH, settings))
    #------------------------

    # return excel file to browser client
    return jsonify({
        "status": True,
        "message": "Success"
    })


@app.route("/upload-accounting-template", methods=["POST"])
async def upload_accounting_template():
    
    # Ensure file exists
    # key : insurance_template_file 
    
    files = await request.files

    if "accounting_template_file" not in files:
        return jsonify({"error": "No accounting template found..."}), 400

    file = files["accounting_template_file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    # now add excel file to directory
    # ACCOUNTING_TEMPLATE_PATH

    # Read file data (blocking but fine; werkzeug already loaded into memory)
    file_data = file.read()
    filename = file.filename

    # check make sure there is not a file with same name...
    result = await check_for_duplicates(ACCOUNTING_TEMPLATE_OBJECT_NAME, filename)
    # return 400, if template with same name already exists
    if result:
        return jsonify({
            "status": False,
            "message": "Template already exists",
        }), 400

    # Ensure storage folder exists
    os.makedirs(ACCOUNTING_TEMPLATE_PATH, exist_ok=True)
    dest_path = os.path.join(ACCOUNTING_TEMPLATE_PATH, filename)
    # Write file asynchronously (safe)
    await asyncio.to_thread(write_file_sync, dest_path, file_data)

    #---------------------
    # add excel file name into config.json
    settings = await asyncio.to_thread(read_json, CONFIG_PATH)
    print("after read json ret")
    # Step 2: Update the dictionary
    template_list: list[str] = settings[TEMPLATE_OBJECT_KEY][ACCOUNTING_TEMPLATE_OBJECT_NAME]
    template_list.append(filename)
    # run coroutine task, to write to json for new baseline data
    asyncio.create_task(write_json_async(CONFIG_PATH, settings))
    #------------------------

    # return excel file to browser client
    return jsonify({
        "status": True,
        "message": "Success"
    })


def delete_excel_file(path):
    p = Path(path)
    try:
        p.unlink()
        return True
    except FileNotFoundError:
        print("File not found:", path)
        return False
    except Exception as e:
        print("Error deleting file:", e)
        return False


@app.route("/templates", methods=["DELETE"])
async def delete_template():
    name = request.args.get("name")
    type_ = request.args.get("type")

    if not name or not type_:
        return jsonify({"success": False, "error": "Missing name or type"}), 400

    print("Deleting template:", name, "Type:", type_)

    # discern type
    template_key = ""
    template_path = ""
    if type_ == "accounting":
        template_key = ACCOUNTING_TEMPLATE_OBJECT_NAME # for json config
        template_path = ACCOUNTING_TEMPLATE_PATH # for excel
    else:
        template_key = INSURANCE_TEMPLATE_OBJECT_NAME
        template_path = INSURANCE_TEMPLATE_PATH

    # delete excel file
    dest_path = os.path.join(template_path, name)
    result = delete_excel_file(dest_path)

    if not result:
        return jsonify({
            "status": False,
            "message": "Delete template file failed",
        }), 400


    # delete json file name in list 
    #---------------------
    # add excel file name into config.json
    settings = await asyncio.to_thread(read_json, CONFIG_PATH)
    print("after read json ret")
    # Step 2: Update the dictionary
    template_list: list[str] = settings[TEMPLATE_OBJECT_KEY][template_key]
    template_list.remove(name)
    # run coroutine task, to write to json for new baseline data
    asyncio.create_task(write_json_async(CONFIG_PATH, settings))
    #------------------------

    # TODO: remove from DB / file system / wherever

    return jsonify({"status": True})




# @app.route("/upload", methods=["POST"])
# async def upload_excel():
#     if "excel_file1" not in request.files:
#         return jsonify({"error": "No file part"}), 400

#     # name of excel file 1
#     # 'excel_file1'

#     file = request.files["excel_file1"]

#     if file.filename == "":
#         return jsonify({"error": "No selected file"}), 400

#     try:
#         # Read Excel file directly using pandas
#         df = pd.read_excel(file)

#         # Example response
#         result = {
#             "rows": len(df),
#             "columns": list(df.columns),
#             "preview": df.head(5).to_dict(orient="records")
#         }

#         return jsonify(result)

#     except Exception as error:
#         return jsonify({"error": str(error)}), 500
    

@app.route("/add-student", methods=["POST"])
async def add_student():
    try:
        print("add student route hit")

        # Grab JSON body from request
        data = await request.get_json()  # <-- automatically parses JSON
        if not data:
            return jsonify({"error": "No JSON body received"}), 400
        print(data)

        # Get current baseline file path
        baseline_file_path = await get_baseline_path_async()
        print("Baseline path:", baseline_file_path)

        # Read Excel into DataFrame
        df = pd.read_excel(baseline_file_path)


        # Only keep the columns we want to add from the request
        new_row = {}
        for col in data.keys():
            # if col not in df.columns:
            #     # add missing column to dataframe
            #     df[col] = None
            new_row[col] = data[col]

        # Append the new row
        df.loc[len(df)] = new_row

        # Save back to Excel BASELINE asynchronously
        await asyncio.to_thread(df.to_excel, baseline_file_path, index=False)

        # this code here might be redudnant
        baseline_file_path = await get_baseline_path_async()
        print(baseline_file_path)
        # get dataframe for baseline excel file
        df = pd.read_excel(baseline_file_path)
        # ---------------

        print("hehe")
        

        return jsonify({
            "status": True,
            "message": "Student added successfully",
            "row_count": len(df),
            # "new_row": new_row
        })

    except Exception as error:
        print(error)
        return jsonify({
            "status": False,
            "message": str(error),
            "row_count": -1,
            # "new_row": new_row
        }), 500






@app.route("/", methods=["GET"])
async def home():
    return jsonify({"message": "Flask server is running!"})


if __name__ == "__main__":
    app.run(port=5000, debug=True, threaded=True)
