from quart import Blueprint, jsonify, request, send_file
import os
import json
import pandas as pd
import asyncio
from io import BytesIO
from utils.enums import Paths, Templates
from utils.templates_helpers import get_template_data_helper, check_for_duplicates, get_templates_helper
from utils.general import read_json, write_json_async, write_file_sync, delete_file, get_cur_time, delete_files, format_date


# route export
baseline_bp = Blueprint("baseline", __name__, url_prefix="/baseline")



# Baseline helper functions
# -------------
# get current baseline file path
async def get_baseline_path_async():
    settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)

    # Step 2: Grab baseline filename from config
    baseline_filename = settings[Paths.BASELINE_PROPS_KEY.value]["name"]

    # Step 3: Combine folder + filename
    baseline_file_path = os.path.join(Paths.BASELINE_PATH.value, baseline_filename)

    return baseline_file_path

#-----------------


@baseline_bp.get("/")
async def get_baseline():
    print("get baseline route hit")

    try:
        # to get excel file
        baseline_file_path = await get_baseline_path_async()
        print(baseline_file_path)

        # to get baseline name
        settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)
        
        # get dataframe for baseline excel file
        df = pd.read_excel(baseline_file_path)

        baseline_row_count = len(df) # get baseline file row count
        baseline_name = settings[Paths.BASELINE_PROPS_KEY.value]["name"] # get baseline file name

        date = format_date(baseline_name)
        
        # Return baseline properties...
        result = {
            "baseline_name" : baseline_name,
            "baseline_row_count" : baseline_row_count,
            "updated_at": date 
        }

        print(result)
        return jsonify(result)
    except Exception as error:
        print(error)
        return jsonify({
            "status": False,
            "message": str(error),
            #"row_count": -1,
            # "new_row": new_row
        }), 500
    


# @app.route("/upload-baseline", methods=["POST"])
@baseline_bp.post("/")
async def upload_baseline():
    print("upload baseline router.... flasker...")

    try:

        files = await request.files

        if "baseline_file" not in files:
            return jsonify({"message": "No baseline file found..."}), 400

        file = files["baseline_file"]

        if file.filename == "":
            return jsonify({"message": "No selected file"}), 400

        # Read file data (blocking but fine; werkzeug already loaded into memory)
        file_data = file.read()
        filename = file.filename

        cur_time = get_cur_time()
        new_name = cur_time + "_BASELINE.xlsx"
        baseline_file_path = Paths.BASELINE_PATH.value + new_name

        # delete other baseline...
        delete_files(Paths.BASELINE_PATH.value)

        # Ensure storage folder exists
        os.makedirs(Paths.BASELINE_PATH.value, exist_ok=True)
        #dest_path = os.path.join(BASELINE_PATH, new_name)
        # Write file asynchronously (safe)
        await asyncio.to_thread(write_file_sync, baseline_file_path, file_data)

        # get dataframe for baseline excel file
        df = pd.read_excel(BytesIO(file_data))
        baseline_row_count = len(df)
        #baseline_name = filename

        # Step 1: Read JSON in a thread
        settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)
        print("after read json ret")
        # Step 2: Update the dictionary
        settings[Paths.BASELINE_PROPS_KEY.value]["name"] = new_name
        settings[Paths.BASELINE_PROPS_KEY.value]["row_count"] = baseline_row_count

        # run coroutine task, to write to json for new baseline data
        asyncio.create_task(write_json_async(Paths.CONFIG_PATH.value, settings))

        print("Before returning response upload baseline")

        # Return baseline properties...
        result = {
            "status": True,
            "message": "Baseline upload successful !",
            "baseline_name" : new_name,
            "baseline_row_count" : baseline_row_count,
        }

        print(result)

        return jsonify(result)
    except Exception as error:
        print(error)
        return jsonify({
            "status": False,
            "message": str(error)
        }), 500
    




# rename baseline
@baseline_bp.post("/rename")
async def rename_baseline():
    print("Rename baseline route hit")

    try:
        # Grab JSON body from request
        data = await request.get_json()  # <-- automatically parses JSON
        if not data:
            return jsonify({"message": "No JSON body received in rename baseline"}), 400
        print(data)

        

        # {"new_baseline_name" : name}
        new_name_data = data["new_baseline_name"]
        name_timestamp = get_cur_time()
        final_new_name = name_timestamp+"_"+new_name_data+".xlsx"
        new_full_path = Paths.BASELINE_PATH.value+final_new_name

        # grab baseline file_path
        old_baseline_path = await get_baseline_path_async()

    
        # rename baseline excel file
        os.rename(old_baseline_path, new_full_path)
        # print(BASELINE_PATH+new_full_path)

        # rename config.json as well
        settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)
        print("after read json ret")
        
        # update baseline config.json name
        settings[Paths.BASELINE_PROPS_KEY.value]["name"] = final_new_name

        # run coroutine task, to write to json for new baseline data
        asyncio.create_task(write_json_async(Paths.CONFIG_PATH.value, settings))

        # return excel file to browser client
        return jsonify({
            "status": True,
            "new_baseline_name": new_name_data+".xlsx",
            "message": "Baseline renamed successfully !",
        })
    except Exception as error:
        print(error)
        return jsonify({
            "status": False,
            "message": str(error),
            "row_count": -1,
            # "new_row": new_row
        }), 500
    

# Add a student to baseline
@baseline_bp.post("/student")
async def add_student():
    try:
        print("add student route hit")

        # ***
        # we inject "id" into Notes field before request is sent to server...

        # Grab JSON body from request
        data = await request.get_json()  # <-- automatically parses JSON
        if not data:
            return jsonify({"message": "No JSON body received"}), 400
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
            "message": "Student added successfully !",
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
    

#  Download baseline file
@baseline_bp.get("/download")
async def download_baseline():
    # grab baseline file_path
    baseline_file_path = await get_baseline_path_async()

    # grab baseline file config object
    settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)
    baseline_name = settings[Paths.BASELINE_PROPS_KEY.value]["name"] # get baseline file name

    # return excel file to browser client
    response = await send_file(
        baseline_file_path,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        attachment_filename=baseline_name
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


