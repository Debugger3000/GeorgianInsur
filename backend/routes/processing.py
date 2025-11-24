from quart import Blueprint, jsonify, request, send_file
from io import BytesIO
import os
import json
import pandas as pd
from utils.general import get_cur_time
from utils.enums import Templates
import asyncio
from utils.general import read_json, write_json_async, get_download_path
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter



# route export
processing_bp = Blueprint("processing", __name__, url_prefix="/processing")

download_paths = {
    "ESL": "First Name",
    "ILAC": "PR email",
    "POST": "Enrollment Status"
}

# ENUMS
CONFIG_PATH = "./data/config.json"


#---------------------------------------------------
#
# Main functionality
# Full Process - compare file against existing baseline file
@processing_bp.post("/full")
async def full_process():

    try:
        print("Full process route has ran")

        # get excel compare file from client input
        # file - compare_file
        compare_file_key = "compare_file" 
        files = await request.files

        if compare_file_key not in files:
            return jsonify({"error": "No compare file found in request..."}), 400

        file = files[compare_file_key]
        if file.filename == "":
            return jsonify({"error": "No COMPARE selected file"}), 400
        #---------

        # create DataFrame of incoming Compare file

        # Read file data (blocking but fine; werkzeug already loaded into memory)
        file_data = file.read()
        filename = file.filename

        # Ensure storage folder exists
        #os.makedirs(BASELINE_PATH, exist_ok=True)
        #dest_path = os.path.join(BASELINE_PATH, filename)
        # Write file asynchronously (safe)
        #await asyncio.to_thread(write_file_sync, dest_path, file_data)



        # DATAFRAME - compare excel file
        compare_file_df = pd.read_excel(BytesIO(file_data))

        esl_eapc = compare_file_df[compare_file_df["Major"] == "ESL EAPC"]
        ilac = compare_file_df[compare_file_df["Campus"] == "LT"]

        # Everything not in A or B
        #post_secondary = compare_file_df[~(compare_file_df["Major"].isin(["ESL EAPC", "value2"]))]

        # Combine the indexes of the grabbed rows
        grabbed_indexes = esl_eapc.index.union(ilac.index)

        # Everything NOT in those indexes = post secondary
        post_secondary = compare_file_df[~compare_file_df.index.isin(grabbed_indexes)]

        column_map = {
            "Student ID": "Student #",
            "First Name": "First Name*",
            "Last Name": "Last Name*",
            "Birthdate": "Birthdate*",
            "Gender": "Gender*",
            "Country of Citizenship": "Country of Origin*", 
            "PR Email": "Insured's Primary Email*"
        }


        # Insurance
        # Dyanmic pointer system - Then they can change logic if they decide too, and app doesn't become obsolete with minor changes
            # If column X, has value Y, we point that student to template Z
            # End filter; X students not adhering to previous filters, point to Z



        # ESL EAPC - 'major' column has value of 'ESL EAPC'
        

        #----
        # Grab ESL EAPC -> template pointer
        # get DF
        #esl_eapc_template_df = pd.read_excel("./data/templates/insurance/ESL EAP GuardMe template.xlsx")

        # Create a NEW empty template-shaped dataframe
        #output_df = pd.DataFrame(columns=esl_eapc_template_df.columns)

        wb = load_workbook("./data/templates/insurance/ESL EAP GuardMe template.xlsx")
        ws = wb.active


        # Build a mapping of template header name -> column letter
        template_columns = {}
        for col_idx, cell in enumerate(ws[1], start=1):  # header row is ws[1]
            if cell.value:  # skip empty or merged secondary cells
                template_columns[cell.value] = get_column_letter(col_idx)

        # Populate rows from source into template
        for _, row in esl_eapc.iterrows():
            ws_row = ws.max_row + 1  # next empty row
            for source_col, template_col_name in column_map.items():
                col_letter = template_columns.get(template_col_name)
                if col_letter and source_col in row:
                    ws[f"{col_letter}{ws_row}"] = row[source_col]





        # Pick only the columns that exist in first_df
        #mapped_df = esl_eapc[list(column_map.keys())].rename(columns=column_map)

        #combined_df = pd.concat([esl_eapc_template_df, mapped_df], ignore_index=True)

        # add rows from compare file

        # auto-populate - City = Barrie
        # auto-populate - Country = Canada
        #combined_df["City*"] = combined_df["City"].fillna("Barrie")
        #combined_df["Country*"] = combined_df["Country"].fillna("Canada")





        # write new populated ESL EAPC .xlsx file to directory
        cur_time = get_cur_time()
        new_esl_report_name = cur_time + "_ESL_EAPC_insurance_report.xlsx"
        file_path = "./data/populated_templates/ESL/" + new_esl_report_name
        
        #save new ouput
        wb.save(file_path)

        # Write the DataFrame
        ##output_df.to_excel(file_path, index=False)


        # Write new ESL populated template to config.json
        settings = await asyncio.to_thread(read_json, CONFIG_PATH)
        print("after we read config json settings full_process")
        print(Templates.TEMPLATE_CONFIG_KEY.value)
        # change json line to new name
        settings[Templates.TEMPLATE_CONFIG_KEY.value][Templates.ESL.value] = new_esl_report_name

        # run coroutine task, to write to json for new baseline data
        asyncio.create_task(write_json_async(CONFIG_PATH, settings))
                



        # ILAC - 'Campus' column has value of 'LT'
        # auto-populate - City = Toronto
        # auto-populate - Country = Canada
        # ILAC GuardMe template.xlsx





        # POST SECONDARY - All students left after previous processing filters are applied
        # auto-populate - City = Barrie
        # auto-populate - Country = Canada
        # POST SECONDARY GuardMe template.xlsx


        # run processing logic on excel file...

        # Sort data into insurance template files

        # Sort data into accounting template file

        # Append Compare file data into Baseline file that lives on disk...
            # get Dataframe of Baseline
            # append Compare dataframe to Baseline dataframe
            # Save new aggregated baseline

        # Serve or store produced Template Files (insurance + accounting)

    
        return jsonify({
            "status": "True"
        }), 200

    except Exception as e:
        print("Error in full process:", e)
        return jsonify({"status": "False"}), 400



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

        # return excel file to browser client
        return await send_file(
            file_path,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print("Error in full process:", e)
        return jsonify({"status": "False"}), 400



















@processing_bp.get("/test")
async def tester():
    return jsonify({"status": "running TESTER GOOD"})


