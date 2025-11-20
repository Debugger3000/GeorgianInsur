# from flask import Flask, request, jsonify
from quart import Quart, request, jsonify, send_file
from quart_cors import cors
import os
import json
import pandas as pd
from io import BytesIO
import asyncio
import sys
import asyncio

if sys.platform == "win32":
    # Avoid ProactorEventLoop socket bugs
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# run dev
# hypercorn main:app --reload
# runs on port 8000


app = Quart(__name__)
app = cors(app, allow_origin="*")  # replaces flask_cors


# path enums  i guess
CONFIG_PATH = "./data/config.json"  # ← path to your JSON config file
baseline_config_name = "baseline_props"
BASELINE_PATH = "./data/baseline/"

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

    # Ensure file exists
    if "baseline_file" not in request.files:
        return jsonify({"error": "No baseline file found..."}), 400

    file = request.files["baseline_file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Read file data (blocking but fine; werkzeug already loaded into memory)
    file_data = file.read()
    filename = file.filename

    # Ensure storage folder exists
    os.makedirs(BASELINE_PATH, exist_ok=True)
    dest_path = os.path.join(BASELINE_PATH, filename)
    # Write file asynchronously (safe)
    await asyncio.to_thread(write_file_sync, dest_path, file_data)

    # get dataframe for baseline excel file
    df = pd.read_excel(BytesIO(file_data))
    baseline_row_count = len(df)
    baseline_name = filename

    # Step 1: Read JSON in a thread
    settings = await asyncio.to_thread(read_json, CONFIG_PATH)
    print("after read json ret")
    # Step 2: Update the dictionary
    settings[baseline_config_name]["name"] = baseline_name
    settings[baseline_config_name]["row_count"] = baseline_row_count

    # run coroutine task, to write to json for new baseline data
    asyncio.create_task(write_json_async(CONFIG_PATH, settings))

    print("Before returning response upload baseline")

    # Return baseline properties...
    result = {
        "baseline_name" : baseline_name,
        "baseline_row_count" : baseline_row_count,
    }

    print(result)

    return jsonify(result)

@app.route("/get-baseline", methods=["GET"])
async def get_baseline():
    print("get baseline route hit")

    baseline_file_path = await get_baseline_path_async()
    print(baseline_file_path)

    # grab baseline file config object
    settings = await asyncio.to_thread(read_json, CONFIG_PATH)
    
    # get dataframe for baseline excel file
    df = pd.read_excel(baseline_file_path)

    baseline_row_count = len(df) # get baseline file row count
    baseline_name = settings[baseline_config_name]["name"] # get baseline file name

    
    # Return baseline properties...
    result = {
        "baseline_name" : baseline_name,
        "baseline_row_count" : baseline_row_count,
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
