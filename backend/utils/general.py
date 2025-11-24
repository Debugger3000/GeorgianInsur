from datetime import datetime
import pytz
import json
import asyncio
from utils.enums import Templates
import os

CONFIG_PATH = "./data/config.json"

def get_cur_time() -> str:
    # Current time in UTC
    now_utc = datetime.utcnow()

    # Convert to Eastern Time
    eastern = pytz.timezone("US/Eastern")
    now_eastern = pytz.utc.localize(now_utc).astimezone(eastern)

    # Format as month-day-year
    formatted_date = now_eastern.strftime("%m-%d-%Y")
    print(formatted_date)
    return formatted_date

#-------------------
# json config helper functions
#-----
def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
async def write_json_async(path, data):
    # Run the blocking file write in a thread
    await asyncio.to_thread(write_json_sync, path, data)


# Blocking JSON write helper
def write_json_sync(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)



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
        

    settings = await asyncio.to_thread(read_json, CONFIG_PATH)

    # Step 2: Grab baseline filename from config
    filename = settings[Templates.TEMPLATE_CONFIG_KEY.value][type]
    path = Templates.POP_TEMPLATE_PATH.value+type+"/"

    # Step 3: Combine folder + filename
    full_file_path = os.path.join(path, filename)

    return full_file_path, filename