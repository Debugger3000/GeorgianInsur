from utils.types import PopulatedTemplateData
from utils.general import read_json, get_download_path, format_date, get_template_type_key
from utils.enums import Paths, Templates
import asyncio
import pandas as pd





async def build_report_data(filenames) -> PopulatedTemplateData:
    result: PopulatedTemplateData = {}
    check = ["ESL", "ILAC", "POST"]

    for key, filename in filenames.items():

        file_path, filename = await get_download_path(key)
        df = pd.read_excel(file_path)

        if key in check:
            result[key] = {
                "date": format_date(filename),
                "row_count": len(df)-12
            }
        else:
            result[key] = {
                "date": format_date(filename),
                "row_count": len(df)
            }

    return result

async def get_template_data_helper() -> PopulatedTemplateData:
    # json data - INSURANCE
    settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)

    temp_object = settings[Templates.TEMPLATE_CONFIG_KEY.value]

    result = await build_report_data(temp_object)

    # pretty_dates = {key: extract_pretty_date(value) for key, value in temp_object.items()}

    return result

async def get_templates_helper():
    # json data - INSURANCE
    settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)
    
    return {
        "accounting": settings[Paths.TEMPLATES_KEY.value][Templates.ACCOUNTING.value],
        "esl": settings[Paths.TEMPLATES_KEY.value][Templates.ESL.value],
        "ilac": settings[Paths.TEMPLATES_KEY.value][Templates.ILAC.value],
        "post": settings[Paths.TEMPLATES_KEY.value][Templates.POST.value]
    }

async def check_for_duplicates(key_name: str, file_name: str) -> bool:
    settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)

    entries = settings[Paths.TEMPLATES_KEY.value].get(key_name, [])

    return file_name in entries


def get_template_path_from_type(t: str) -> tuple[str,str]:
    #  used for directory + template name in config.json
    key = get_template_type_key(t)

    return Paths.TEMPLATE_PATH.value + key + "/", key

