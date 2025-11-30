from quart import Blueprint, jsonify, request, send_file
import os
import json
import pandas as pd
import asyncio

from utils.enums import Paths, Templates
from utils.templates_helpers import get_template_data_helper, check_for_duplicates, get_templates_helper, get_template_path_from_type
from utils.general import read_json, write_json_async, write_file_sync, delete_file, delete_files, write_to_json


# route export
templates_bp = Blueprint("templates", __name__, url_prefix="/templates")


# GET templates list to display for settings
# @app.route("/get-templates", methods=["GET"])
@templates_bp.get("/")
async def get_templates():
    try:
        templates = await get_templates_helper()

        print("templates returning.....")
        print(templates)

        # return excel file to browser client
        return jsonify({
            "status": True,
            "message": "Success",
            "templates": templates
        })

    except Exception as error:
        print(error)
        return jsonify({
            "status": False,
            "message": str(error),
        }), 500
    

# Get data for POPULATED templates
# date + row_count.. (row_count not accurate due to template variation...)
@templates_bp.get("/metadata")
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


# Upload insurance
# @app.route("/upload-insurance-template", methods=["POST"])
@templates_bp.post("")
async def upload_template():
    try:
        # type - template 
        type_ = request.args.get("type")

        # Ensure file exists
        # key : insurance_template_file 
        
        files = await request.files

        if "template_file" not in files:
            return jsonify({"message": "No insurance template found..."}), 400

        file = files["template_file"]

        if file.filename == "":
            return jsonify({"message": "No selected file"}), 400
        
        #------------------------------------------------------------------------------------------------   
        
        # send type, and get proper file path
        # returns tuple
        file_path, key = get_template_path_from_type(type_)

        # Read file data (blocking but fine; werkzeug already loaded into memory)
        file_data = file.read()
        filename = file.filename

        # overwrite directory with a new template...
        delete_files(file_path)

        dest_path = os.path.join(file_path, filename)
        # Write excel file to folder
        await asyncio.to_thread(write_file_sync, dest_path, file_data)

        # write new file to json.config
        await write_to_json(filename, Paths.TEMPLATES_KEY.value, key)

        # return success status
        return jsonify({
            "status": True,
            "message": "Template Upload successful !"
        })
    except Exception as error:
        print(error)
        return jsonify({
            "status": False,
            "message": str(error),
        }), 500


# @app.route("/upload-accounting-template", methods=["POST"])
# @templates_bp.post("/accounting")
# async def upload_accounting_template():
#     try:
#         # Ensure file exists
#         # key : insurance_template_file 
        
#         files = await request.files

#         if "accounting_template_file" not in files:
#             return jsonify({"message": "No accounting template found..."}), 400

#         file = files["accounting_template_file"]

#         if file.filename == "":
#             return jsonify({"message": "No selected file..."}), 400
        
#         # now add excel file to directory
#         # ACCOUNTING_TEMPLATE_PATH

#         # Read file data (blocking but fine; werkzeug already loaded into memory)
#         file_data = file.read()
#         filename = file.filename

#         # check make sure there is not a file with same name...
#         result = await check_for_duplicates(Paths.INSURANCE_TEMPLATES.value, filename)
#         # return 400, if template with same name already exists
#         if result:
#             return jsonify({
#                 "status": False,
#                 "message": "Template already exists...",
#             }), 400

#         # Ensure storage folder exists
#         os.makedirs(Paths.ACCOUNTING_TEMPLATES_PATH.value, exist_ok=True)
#         dest_path = os.path.join(Paths.ACCOUNTING_TEMPLATES_PATH.value, filename)
#         # Write file asynchronously (safe)
#         await asyncio.to_thread(write_file_sync, dest_path, file_data)

#         #---------------------
#         # add excel file name into config.json
#         settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)
#         print("after read json ret")
#         # Step 2: Update the dictionary
#         template_list: list[str] = settings[Paths.TEMPLATES_KEY.value][Paths.ACCOUNTING_TEMPLATES.value]
#         template_list.append(filename)
#         # run coroutine task, to write to json for new baseline data
#         asyncio.create_task(write_json_async(Paths.CONFIG_PATH.value, settings))
#         #------------------------

#         # return excel file to browser client
#         return jsonify({
#             "status": True,
#             "message": "Template upload successful !"
#         })
#     except Exception as error:
#         print(error)
#         return jsonify({
#             "status": False,
#             "message": str(error),
#         }), 500
    

# @app.route("/templates", methods=["DELETE"])
@templates_bp.delete("/")
async def delete_template():

    try:
        name = request.args.get("name")
        type_ = request.args.get("type")

        if not name or not type_:
            return jsonify({"success": False, "message": "Missing name or type"}), 400

        print("Deleting template:", name, "Type:", type_)

        template_path, template_key = get_template_path_from_type(type_)

        # discern type
        # template_key = ""
        # template_path = ""
        # if type_ == "accounting":
        #     template_key = Paths.ACCOUNTING_TEMPLATES.value # for json config
        #     template_path = Paths.ACCOUNTING_TEMPLATES_PATH.value # for excel
        # elif type_ == "esl":
        #     template_key = Paths.INSURANCE_TEMPLATES.value
        #     template_path = Paths.INSURANCE_TEMPLATES_PATH.value

        # delete excel file
        dest_path = os.path.join(template_path, name)
        result = delete_file(dest_path)

        if not result:
            return jsonify({
                "status": False,
                "message": "Delete template file failed",
            }), 400

        # write a empty string into json...
        await write_to_json("", Paths.TEMPLATES_KEY.value, template_key)

        return jsonify({"status": True, "message": "Template delete successful !"})
    except Exception as error:
        print(error)
        return jsonify({
            "status": False,
            "message": str(error),
        }), 500


