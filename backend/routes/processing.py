from quart import Blueprint, jsonify, request, send_file
from io import BytesIO
import os
import json
import pandas as pd
from utils.general import get_cur_time
from utils.enums import Templates, Paths
import asyncio
from utils.general import read_json, write_json_async, get_download_path, delete_files, read_from_json, get_baseline_path_async, write_file_sync, write_to_json, write_to_json_once
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from utils.processing_helpers import populate_ESL, populate_ILAC, populate_POST, populate_accounting, accounting_calculations



# route export
processing_bp = Blueprint("processing", __name__, url_prefix="/processing")

download_paths = {
    "ESL": "First Name",
    "ILAC": "PR email",
    "POST": "Enrollment Status"
}



#---------------------------------------------------
#
# Main functionality
# Full Process - compare file against existing baseline file
@processing_bp.post("/full")
async def full_process():

    # Insurance
        # Dyanmic pointer system - Then they can change logic if they decide too, and app doesn't become obsolete with minor changes
            # If column X, has value Y, we point that student to template Z
            # End filter; X students not adhering to previous filters, point to Z

    # grab query params - semester - year
    semester = request.args.get("semester")
    year = request.args.get("year")

    try:
        print("Full process route has ran")

        # get excel compare file from client input
        # file - compare_file
        compare_file_key = "compare_file" 
        files = await request.files

        if compare_file_key not in files:
            return jsonify({"message": "No compare file found in request..."}), 400

        file = files[compare_file_key]
        if file.filename == "":
            return jsonify({"message": "No COMPARE selected file"}), 400
        #---------

        # create DataFrame of incoming Compare file

        # Read file data (blocking but fine; werkzeug already loaded into memory)
        file_data = file.read()
        filename = file.filename

        # DATAFRAME - compare excel file
        compare_file_df = pd.read_excel(BytesIO(file_data)) # OLD + NEW compare


        # Get old baseline excel file, extract list of old student ids 
        baseline_path = await get_baseline_path_async() # get baseline path
        baseline_df = pd.read_excel(baseline_path) # OLD baseline - just OLD students

        # OLD baseline id list
            # compare to, to remove OLD students into a sole NEW_compare
        old_baseline_compare_list = baseline_df["Student ID"].tolist()
        old_ids = set(old_baseline_compare_list)

        # NEW compare - just new students to process
        new_compare_df = compare_file_df[~compare_file_df["Student ID"].isin(old_ids)]



        # extract out old students from baseline out of new compare
            # we hold old students in baseline

        # do processes on NEW_compare that has only NEW students

        # then after templates are populated... we append old baseline to new_compare to create new baseline



        #---------
        # ESL 
        # data for ESL template
        esl_eapc = new_compare_df[new_compare_df["Major"] == "ESL EAPC"]

        result = await populate_ESL(esl_eapc)
        if not result:
            return jsonify({"message": "Populate ESL gone wrong"}), 500
        

        # ILAC 
        # data for ILAC template
        ilac = new_compare_df[new_compare_df["Campus"] == "LT"]

        result = await populate_ILAC(ilac)
        if not result:
            return jsonify({"message": "Populate ILAC gone wrong"}), 500


        # POST SECONDARY  
        # Combine the indexes of the grabbed rows
        grabbed_indexes = esl_eapc.index.union(ilac.index)

        # POST data for POST template
        post_secondary = new_compare_df[~new_compare_df.index.isin(grabbed_indexes)]

        result = await populate_POST(post_secondary)
        if not result:
            return jsonify({"message": "Populate POST gone wrong"}), 500
        
        # ACCOUNTING
            # send EAPC
        post_ilac_combined_df = pd.concat([ilac, post_secondary], ignore_index=True)
        
        # Sort data into accounting template file
        accounting_df = await accounting_calculations(post_ilac_combined_df, esl_eapc, semester, year)

        result = await populate_accounting(accounting_df)
        if not result:
            return jsonify({"message": "Populate ACCCOUNTING gone wrong"}), 500
        
        #---------




        # Append Compare file data into Baseline file that lives on disk...
            # get Dataframe of Baseline
            # append Compare dataframe to Baseline dataframe
            # Save new aggregated baseline


        # Add back old students to new_compare

        # new compare_file already has old and new students
        # we can just write this file to the baseline directory / as the new baseline
        #new_rows = compare_file_df[~compare_file_df["Student ID"].isin(baseline_df["Student ID"])]
        # NEW BASELINE FILE
        new_baseline_df = pd.concat([baseline_df, new_compare_df], ignore_index=True) # merging OLD baseline + just NEW students df 

        # delete other baseline...
        delete_files(Paths.BASELINE_PATH.value)

        cur_time = get_cur_time()
        new_name = cur_time + "_BASELINE.xlsx"
        baseline_file_path = Paths.BASELINE_PATH.value + new_name

        # async write new baseline to directory...
        await asyncio.to_thread(new_baseline_df.to_excel, baseline_file_path, index=False)


        row_count = len(new_baseline_df)
        await write_to_json_once(new_name, Paths.BASELINE_PROPS_KEY.value, row_count)

        # write NEW BASELINE name to config.json
        # await write_to_json(new_name, Paths.BASELINE_PROPS_KEY.value, "name")
        # # write row count to config.json
        
        # await write_to_json(row_count, Paths.BASELINE_PROPS_KEY.value, "row_count")

        # write new baseline to directory
        #await asyncio.to_thread(write_file_sync, Paths.BASELINE_PATH.value, file_data)
        

        print("Full process complete")
        return jsonify({
            "status": "True",
            "message": "Process Successful ! New downloads available."
        }), 200

    except Exception as e:
        print("Error in full process:", e)
        return jsonify({"status": "False", "message": "Process Against Baseline encountered server errors..."}), 400




# Baseline Solo Process
@processing_bp.post("/solo")
async def solo_process():

    try:
        print("Solo process route hit...")

        # grab query params - semester - year
        semester = request.args.get("semester")
        year = request.args.get("year")

        print(semester)
        print(year)

        

        print("Solo process route has ran")

        # get baseline path
        baseline_path = await get_baseline_path_async()
        # get baseline df
        solo_baseline_df = pd.read_excel(baseline_path)

        


        #---------
        # ESL 
        # data for ESL template
        esl_eapc = solo_baseline_df[solo_baseline_df["Major"] == "ESL EAPC"]


        result = await populate_ESL(esl_eapc)
        if not result:
            return jsonify({"message": "Populate ESL gone wrong"}), 500
        
        # ILAC 
        # data for ILAC template
        ilac = solo_baseline_df[solo_baseline_df["Campus"] == "LT"]

        result = await populate_ILAC(ilac)
        if not result:
            return jsonify({"message": "Populate ILAC gone wrong"}), 500

        # POST SECONDARY  
        # Combine the indexes of the grabbed rows
        grabbed_indexes = esl_eapc.index.union(ilac.index)

        # POST data for POST template
        post_secondary = solo_baseline_df[~solo_baseline_df.index.isin(grabbed_indexes)]

        result = await populate_POST(post_secondary)
        if not result:
            return jsonify({"message": "Populate POST gone wrong"}), 500
        

        # ACCOUNTING
            # send EAPC
        post_ilac_combined_df = pd.concat([ilac, post_secondary], ignore_index=True)
        
        # Sort data into accounting template file
        accounting_df = await accounting_calculations(post_ilac_combined_df, esl_eapc, semester, year)
        print("accounting df was returned fine...")
        result = await populate_accounting(accounting_df)
        if not result:
            return jsonify({"message": "Populate ACCCOUNTING gone wrong"}), 500
        
        #---------

        # delete other baseline...
        delete_files(Paths.BASELINE_PATH.value)

        cur_time = get_cur_time()
        new_name = cur_time + "_BASELINE.xlsx"
        baseline_file_path = Paths.BASELINE_PATH.value + new_name

       

        # async write new baseline to directory...
        await asyncio.to_thread(solo_baseline_df.to_excel, baseline_file_path, index=False)

        row_count = len(solo_baseline_df)
        await write_to_json_once(new_name, Paths.BASELINE_PROPS_KEY.value, row_count)

        # # write NEW BASELINE name to config.json
        # await write_to_json(new_name, Paths.BASELINE_PROPS_KEY.value, "name")
        # write row count to config.json



        #row_count = len(solo_baseline_df)
        #await write_to_json(row_count, Paths.BASELINE_PROPS_KEY.value, "row_count")

        print("Solo process complete")
        return jsonify({
            "status": "True",
            "message": "Process Successful ! New downloads available."
        }), 200

    except Exception as e:
        print("Error in solo process:", e)
        return jsonify({"status": "False", "message": "Process Baseline encountered server errors..."}), 400






@processing_bp.get("/download")
async def download_file():

    try:
        print("Download something")

        # ESL
        # ILAC
        # POST
        # ACC
        type_ = request.args.get("type")

        # grab file_path and filename
        file_path, filename = await get_download_path(type_)

        print(file_path)
        print(filename)

        response = await send_file(
            file_path,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            conditional=False
        )

        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return response


    except Exception as e:
        print("Error in full process:", e)
        return jsonify({"status": "False", "message": "File download failed..."}), 400



















@processing_bp.get("/test")
async def tester():
    return jsonify({"status": "running TESTER GOOD"})


