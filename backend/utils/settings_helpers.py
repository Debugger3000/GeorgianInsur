from utils.types import AccountingTargets
from utils.general import read_from_json, read_json, write_to_json, write_json_async
from utils.enums import Paths
import asyncio




async def get_account_targets() -> AccountingTargets:


    # grab config.json
    settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)
    # read from object / then key-value
    data = settings[Paths.SETTINGS_FEES_KEY.value]

    return {
        "fall": data["fall"],
        "winter": data["winter"],
        "summer": data["summer"],
        "fall_post": data["fall_post"],
        "winter_post": data["winter_post"],
        "summer_post": data["summer_post"]
    }

async def write_to_json_fee_targets(value: AccountingTargets):

    try:
        settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)
        # replace whole insurance target object...
        settings[Paths.SETTINGS_FEES_KEY.value] = value
        # run coroutine task, to write to json for new baseline data
        asyncio.create_task(write_json_async(Paths.CONFIG_PATH.value, settings))

        return True

    except Exception as e:
        print("Error in write json for fee targets:", e)
        return False


async def edit_accounting_targets(target_object: AccountingTargets) -> bool:

    # receive object like
        # {
        #   "fall": 225,
        #   "winter": 225,
        #   "summer": 225
        # }
    try:
        # If a post is submitted just rewrite anyways, since client handles changed values...
        #cur_targets = await get_account_targets()

        result = await write_to_json_fee_targets(target_object)
        if not result:
            return False

        return True
    
    except Exception as e:
        print("Error in POST account fee target:", e)
        return False
    