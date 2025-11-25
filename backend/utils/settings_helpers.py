from utils.types import AccountingTargets
from utils.general import read_from_json, read_json, write_to_json
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
        "summer": data["summer"]
    }


async def edit_accounting_targets(target_object: AccountingTargets) -> bool:

    # receive object like
        # {
        #   "fall": 225,
        #   "winter": 225,
        #   "summer": 225
        # }

    #  implement function to change account settings ... we cant race condition for three awaits...

    try:
        print("tehe")

        cur_targets = await get_account_targets()

        fall = target_object["fall"]
        winter = target_object["winter"]
        summer = target_object["summer"]

        print(cur_targets)

        print(cur_targets["fall"])
        print(fall)
        # update fall with new value
        if cur_targets["fall"] != fall:
            await write_to_json(fall, Paths.SETTINGS_FEES_KEY.value, "fall")

        # update winter with new value
        if cur_targets["winter"] != winter:
            await write_to_json(winter, Paths.SETTINGS_FEES_KEY.value, "winter")

        # update summer with new value
        if cur_targets["summer"] != summer:
            await write_to_json(summer, Paths.SETTINGS_FEES_KEY.value, "summer")

        return True
    
    except Exception as e:
        print("Error in POST account fee target:", e)
        return False
    