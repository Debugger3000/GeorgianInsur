from datetime import datetime, timezone
import pytz
import json
import asyncio
from utils.enums import Templates, Paths
import os
from pathlib import Path
from utils.enums import Paths, Accounting


# DEPENDENCIES for general functions
#-------------------------------------------------------------
# json config helper functions
#-----
def read_json(path):
    print("Path for read_json operationL: ")
    print(path)
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


def get_template_type_key(t: str):
    upper = t.upper()
    type = ""
    match upper:
        case Templates.ESL.value:
            type = Templates.ESL.value
        case Templates.ILAC.value:
            type = Templates.ILAC.value
        case Templates.POST.value:
            type = Templates.POST.value
        case Templates.ACCOUNTING.value:
            type = Templates.ACCOUNTING.value
        case _:
            type = "bad"
    return type


# get download path for specified type
async def get_download_path(t: str) -> tuple[str, str]:

    type = get_template_type_key(t)

    settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)

    # Step 2: Grab baseline filename from config
    filename = settings[Templates.TEMPLATE_CONFIG_KEY.value][type]
    # print(filename)
    path = Templates.POP_TEMPLATE_PATH.value+type+"/"

    # Step 3: Combine folder + filename
    full_file_path = os.path.join(path, filename)
    # print(full_file_path)
    return full_file_path, filename

# Delete helpers
#-----------
# delete files within directory
# For baseline, populated_templates, and templates
def delete_files(path: str):
    # Path to the directory
    dir_path = Path(path)

    print("deleting files within path: ")
    print(path)

    # Iterate through all files in the directory and delete them
    for file_path in dir_path.iterdir():
        if file_path.is_file():
            file_path.unlink()  # deletes the file

    print("All files deleted in", dir_path)

# delete a single file given a path
def delete_file(path):
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

#----------------------


async def write_to_json(value: str, object_key: str, key_value: str):
    settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)
    # print("after we read config json settings full_process")
    # print(Templates.TEMPLATE_CONFIG_KEY.value)
    # change json line to new name
    settings[object_key][key_value] = value
    # run coroutine task, to write to json for new baseline data
    await write_json_async(Paths.CONFIG_PATH.value, settings)

# write to json baseline all at once for name and row_count
async def write_to_json_once(name_value: str, object_key: str, row_value):
    settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)
    print("after we read config json settings full_process")
    print(Templates.TEMPLATE_CONFIG_KEY.value)
    # change json line to new name
    settings[object_key]["name"] = name_value
    settings[object_key]["row_count"] = row_value
    # run coroutine task, to write to json for new baseline data
    await write_json_async(Paths.CONFIG_PATH.value, settings)

async def read_from_json(object_key: str, key_value: str):
    # grab config.json
    settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)
    # read from object / then key-value
    value = settings[object_key][key_value]
    # return grabbed value
    return value

# get accounting insurance total for given semester
async def get_insurance_total(type: str, semester: str) -> float:
    # grab config.json
    settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)
    # vars
    vals = ["fall","winter","summer"]
    count = 0
    enum_appendage = ""
    # append _post if type matches
    if type == "post":
        enum_appendage = "_post"

    # put semester to lowercase first
    lowered_semester = semester.lower()
    index = vals.index(lowered_semester)
    for i in range(0,index+1):
        cur_val = vals[i]+enum_appendage
        value = settings[Accounting.INSURANCE_KEY.value][cur_val]
        count += float(value)
    
    return count



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


# ---
# Date Helpers

def get_cur_time() -> str:
    # Current time in UTC
    now_utc = datetime.now(timezone.utc)

    # Convert to Eastern Time
    eastern = pytz.timezone("US/Eastern")
    now_eastern = now_utc.astimezone(eastern)

    # Format as month-day-year
    formatted_date = now_eastern.strftime("%m-%d-%Y-%H-%M-%S")
    # print(formatted_date)
    return formatted_date

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
