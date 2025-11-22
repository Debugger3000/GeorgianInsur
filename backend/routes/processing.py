from quart import Blueprint, jsonify, request, send_file
from io import BytesIO
import os
import json
import pandas as pd



# route export
processing_bp = Blueprint("processing", __name__, url_prefix="/processing")



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
        df = pd.read_excel(BytesIO(file_data))


        # Insurance
        # Dyanmic pointer system - Then they can change logic if they decide too, and app doesn't become obsolete with minor changes
            # If column X, has value Y, we point that student to template Z
            # End filter; X students not adhering to previous filters, point to Z

        # ESL EAPC - 'major' column has value of 'ESL EAPC'

        # ILAC - 'Campus' column has value of 'LT'

        # POST SECONDARY - All students left after previous processing filters are applied



        # run processing logic on excel file...

        # Sort data into insurance template files

        # Sort data into accounting template file

        # Append Compare file data into Baseline file that lives on disk...
            # get Dataframe of Baseline
            # append Compare dataframe to Baseline dataframe
            # Save new aggregated baseline

        # Serve or store produced Template Files (insurance + accounting)

    
    except Exception as e:
        print("Error in full process:", e)
        return jsonify({"status": "False"})


    return jsonify({
        "status": "True"
    })



















@processing_bp.get("/test")
async def tester():
    return jsonify({"status": "running TESTER GOOD"})


