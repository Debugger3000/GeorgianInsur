from quart import Blueprint, jsonify, request, send_file
from io import BytesIO
import os
import json
import pandas as pd
from utils.general import get_cur_time
from utils.enums import Templates, Paths
import asyncio
from utils.general import read_json, write_json_async, get_download_path, delete_files, read_from_json, get_baseline_path_async, write_file_sync, write_to_json
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from utils.processing_helpers import populate_ESL, populate_ILAC, populate_POST, populate_accounting
from utils.settings_helpers import edit_accounting_targets, get_account_targets



# route export
settings_bp = Blueprint("settings", __name__, url_prefix="/settings")




@settings_bp.post("/account-fee-target")
async def account_fees():

    try:
        print("Post a change to account fees")

        # receive object like
        # {
        #   "fall": 225,
        #   "winter": 225,
        #   "summer": 225
        # }

        data = await request.get_json()  # <-- automatically parses JSON
        print(data)
        if not data:
            return jsonify({"message": "No JSON body received in post new account-fee-targets"}), 400
        print(data)

        # give function object, change fields that have different value, keep others the same...
        result = await edit_accounting_targets(data)

        if not result:
            return jsonify({"status": "False", "message": "Server error when trying to change Assessment Fees"}), 400

        return jsonify({"status": "True", "message": "Assessment Fees change successful !"}), 200


    except Exception as e:
        print("Error in POST account fee target:", e)
        return jsonify({"status": "False", "message": str(e)}), 400



@settings_bp.get("/")
async def account_fees_targets():

    try:
        print("GET account fees")

        # receive object like
        # {
        #   "fall": 225,
        #   "winter": 225,
        #   "summer": 225
        # }

        fee_data = await get_account_targets()

        return jsonify({
            "status": "True",
            "data": fee_data
        }), 200


    except Exception as e:
        print("Error in GET account fee targets:", e)
        return jsonify({"status": "False"}), 400



