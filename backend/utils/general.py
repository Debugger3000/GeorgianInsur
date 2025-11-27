from datetime import datetime, timezone
import pytz
import json
import asyncio
from utils.enums import Templates, Paths
import os
from pathlib import Path
from utils.enums import Paths


# DEPENDENCIES for general functions
#-------------------------------------------------------------
# json config helper functions
#-----
def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# dependency for write_to_json
async def write_json_async(path, data):
    # Run the blocking file write in a thread
    await asyncio.to_thread(write_json_sync, path, data)

# dependency for ^^^^^
# Blocking JSON write helper
def write_json_sync(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

#------------------------------------------------------------


def get_cur_time() -> str:
    # Current time in UTC
    now_utc = datetime.now(timezone.utc)


    # Convert to Eastern Time
    eastern = pytz.timezone("US/Eastern")
    now_eastern = now_utc.astimezone(eastern)

    # Format as month-day-year
    formatted_date = now_eastern.strftime("%m-%d-%Y-%H-%M-%S")
    print(formatted_date)
    return formatted_date


# get download path for specified type
async def get_download_path(t: str) -> tuple[str, str]:

    type = ""
    match t:
        case Templates.ESL.value:
            type = Templates.ESL.value
        case Templates.ILAC.value:
            type = Templates.ILAC.value
        case Templates.POST.value:
            type = Templates.POST.value
        case Templates.ACCOUNTING.value:
            type = Templates.ACCOUNTING.value
        case _:
            return "bad"

    settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)

    # Step 2: Grab baseline filename from config
    filename = settings[Templates.TEMPLATE_CONFIG_KEY.value][type]
    print(filename)
    path = Templates.POP_TEMPLATE_PATH.value+type+"/"

    # Step 3: Combine folder + filename
    full_file_path = os.path.join(path, filename)
    print(full_file_path)
    return full_file_path, filename


# delete files within directory
# For baseline, populated_templates, and templates
def delete_files(path: str):
    # Path to the directory
    dir_path = Path(path)

    # Iterate through all files in the directory and delete them
    for file_path in dir_path.iterdir():
        if file_path.is_file():
            file_path.unlink()  # deletes the file

    print("All files deleted in", dir_path)


async def write_to_json(value: str, object_key: str, key_value: str):
    settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)
    print("after we read config json settings full_process")
    print(Templates.TEMPLATE_CONFIG_KEY.value)
    # change json line to new name
    settings[object_key][key_value] = value
    # run coroutine task, to write to json for new baseline data
    asyncio.create_task(write_json_async(Paths.CONFIG_PATH.value, settings))

# write to json baseline all at once for name and row_count
async def write_to_json_once(name_value: str, object_key: str, row_value):
    settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)
    print("after we read config json settings full_process")
    print(Templates.TEMPLATE_CONFIG_KEY.value)
    # change json line to new name
    settings[object_key]["name"] = name_value
    settings[object_key]["row_count"] = row_value
    # run coroutine task, to write to json for new baseline data
    asyncio.create_task(write_json_async(Paths.CONFIG_PATH.value, settings))

async def read_from_json(object_key: str, key_value: str):
    # grab config.json
    settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)
    # read from object / then key-value
    value = settings[object_key][key_value]
    # return grabbed value
    return value



# get baseline file
async def get_baseline_path_async():
    settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)

    # Step 2: Grab baseline filename from config
    baseline_filename = settings[Paths.BASELINE_PROPS_KEY.value]["name"]

    # Step 3: Combine folder + filename
    baseline_file_path = os.path.join(Paths.BASELINE_PATH.value, baseline_filename)

    return baseline_file_path

# write excel file to directory
def write_file_sync(path, data):
    with open(path, "wb") as f:
        f.write(data)