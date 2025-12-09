from quart import jsonify
from io import BytesIO
import os
import json

import pandas as pd
from utils.general import get_cur_time
from utils.enums import Templates
import asyncio
from utils.general import read_json, write_json_async, get_download_path, delete_files, write_to_json, read_from_json
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from utils.templates_helpers import get_template_path_from_type

from utils.enums import Paths

# for post, ilac and EAPC
column_map = {
        "Student ID": "Student #",
        "First Name": "First Name*",
        "Last Name": "Last Name*",
        "Birthdate": "Birthdate*",
        "Gender": "Gender*",
        "Country of Citizenship": "Country of Origin*", 
        "Legacy Email": "Insured's Primary Email*"
}

# for ININ accounting reports...
accounting_column_map = {
        "Selected Term Desc": "Selected Term Desc",
        "Student ID": "Student ID",
        "First Name": "First Name",
        "Last Name": "Last Name"
        # balance column -> +20 or -20
        # Fee Code column -> ININ
}



#------------------------------------------------------------




async def populate_ESL(esl_eapc: pd.DataFrame):

    # ESL EAPC - 'major' column has value of 'ESL EAPC'
    
        #----
        # Grab ESL EAPC -> template pointer
        # get DF
        #esl_eapc_template_df = pd.read_excel("./data/templates/insurance/ESL EAP GuardMe template.xlsx")

        # Create a NEW empty template-shaped dataframe
        #output_df = pd.DataFrame(columns=esl_eapc_template_df.columns)

    

    try:

        # template_name = await find_template_by_keyword(Templates.ESL.value, Paths.INSURANCE_TEMPLATES.value)
        # if template_name == None:
        #     return jsonify({"error": "Populate ESL keyword for template no match"}), 500
        
        template_path, key = get_template_path_from_type(Templates.ESL.value)
        template_name = await read_from_json(Paths.TEMPLATES_KEY.value, key)
        final_path = template_path + template_name

        wb = load_workbook(final_path)
        ws = wb.active

        # sanity checks
        if esl_eapc.empty:
            print("DEBUG: source dataframe (esl_eapc) is empty — nothing to write.")
        else:
            print(f"DEBUG: source dataframe has {len(esl_eapc)} rows")

        # eventually grabbed from json...
        HEADER_ROW = 13

        # Build a mapping of template header name -> column letter
        # {Student # : C}
        template_columns = {}
        for col_idx, cell in enumerate(ws[HEADER_ROW], start=1):  # header row is ws[1]
            if cell.value:  # skip empty or merged secondary cells
                template_columns[cell.value] = get_column_letter(col_idx)


        # Populate rows from source into template
        current_row = HEADER_ROW + 1  # 14
        #print(list(template_columns.items()))

        for _, df_row in esl_eapc.iterrows():
            for source_col, template_col_name in column_map.items():
                col_letter = template_columns.get(template_col_name)
                country_col_letter = template_columns.get("Country*")
                city_col_letter = template_columns.get("City*")
                #print(city_col_letter)
                if col_letter and source_col in df_row.index:
                    #print(f"writing '{df_row[source_col]}' to col {col_letter} row {current_row}")
                    ws[f"{col_letter}{current_row}"] = df_row[source_col]
                    # write into Country
                    ws[f"{country_col_letter}{current_row}"] = "Canada"
                    # write into City
                    ws[f"{city_col_letter}{current_row}"] = "Barrie"
            current_row += 1
        
        # auto-populate - City = Barrie
        # auto-populate - Country = Canada

        folder_path = Templates.POP_TEMPLATE_PATH.value + Templates.ESL.value + "/"

        # destroy other templates that exist in /ESL first
        delete_files(folder_path)

        # write new populated ESL EAPC .xlsx file to directory
        cur_time = get_cur_time()
        new_esl_report_name = cur_time + "_ESL_EAPC_insurance_report.xlsx"
        file_path = folder_path + new_esl_report_name
        
        #save new ouput
        wb.save(file_path)

        # write to config.json
        await write_to_json(new_esl_report_name, Templates.TEMPLATE_CONFIG_KEY.value, Templates.ESL.value)

        # Write new ESL populated template to config.json
        # settings = await asyncio.to_thread(read_json, Paths.CONFIG_PATH.value)
        # print("after we read config json settings full_process")
        # print(Templates.TEMPLATE_CONFIG_KEY.value)
        # # change json line to new name
        # settings[Templates.TEMPLATE_CONFIG_KEY.value][Templates.ESL.value] = new_esl_report_name
        # # run coroutine task, to write to json for new baseline data
        # asyncio.create_task(write_json_async(Paths.CONFIG_PATH.value, settings))
        
        print("ESL populated successfully")
        return True
    
    #return exception
    except Exception as error:
        print(error)
        return False
    

# ILAC populate
async def populate_ILAC(df: pd.DataFrame):

    # ILAC - 'Campus' column has value of 'LT'
        # auto-populate - City = Toronto
        # auto-populate - Country = Canada
        # ILAC GuardMe template.xlsx
    
    try:
        print("running populate ILAC")

        template_path, key = get_template_path_from_type(Templates.ILAC.value)
        template_name = await read_from_json(Paths.TEMPLATES_KEY.value, key)
        final_path = template_path + template_name

        wb = load_workbook(final_path)
        ws = wb.active

        # sanity checks
        if df.empty:
            print("DEBUG: source dataframe (ilac) is empty — nothing to write.")
        else:
            print(f"DEBUG: source dataframe has {len(df)} rows")

        # eventually grabbed from json...
        HEADER_ROW = 13

        # Build a mapping of template header name -> column letter
        # {Student # : C}
        template_columns = {}
        for col_idx, cell in enumerate(ws[HEADER_ROW], start=1):  # header row is ws[1]
            if cell.value:  # skip empty or merged secondary cells
                template_columns[cell.value] = get_column_letter(col_idx)

        # Populate rows from source into template
        current_row = HEADER_ROW + 1  # 14
        #print(list(template_columns.items()))

        for _, df_row in df.iterrows():
            for source_col, template_col_name in column_map.items():
                col_letter = template_columns.get(template_col_name)
                country_col_letter = template_columns.get("Country*")
                city_col_letter = template_columns.get("City*")
                #print(city_col_letter)
                if col_letter and source_col in df_row.index:
                    #print(f"writing '{df_row[source_col]}' to col {col_letter} row {current_row}")
                    ws[f"{col_letter}{current_row}"] = df_row[source_col]
                    # write into Country
                    ws[f"{country_col_letter}{current_row}"] = "Canada"
                    # write into City
                    ws[f"{city_col_letter}{current_row}"] = "Toronto"
            current_row += 1

        folder_path = Templates.POP_TEMPLATE_PATH.value + Templates.ILAC.value + "/"

        # destroy other templates that exist in /ESL first
        delete_files(folder_path)

        # write new populated ESL EAPC .xlsx file to directory
        cur_time = get_cur_time()
        new_ilac_report_name = cur_time + "_ILAC_GuardMe_template.xlsx"
        file_path = folder_path + new_ilac_report_name
        
        #save new ouput
        wb.save(file_path)

        # write to config.json
        await write_to_json(new_ilac_report_name, Templates.TEMPLATE_CONFIG_KEY.value, Templates.ILAC.value)

        print("ILAC populated successfully")
        return True
    
    #return exception
    except Exception as error:
        print(error)
        return False


# POST populate
async def populate_POST(df: pd.DataFrame):

    # POST SECONDARY - All students left after previous processing filters are applied
        # auto-populate - City = Barrie
        # auto-populate - Country = Canada
        # POST SECONDARY GuardMe template.xlsx
    
    try:
        print("running populate POST")

        template_path, key = get_template_path_from_type(Templates.POST.value)
        template_name = await read_from_json(Paths.TEMPLATES_KEY.value, key)
        final_path = template_path + template_name

        wb = load_workbook(final_path)
        ws = wb.active

        # sanity checks
        if df.empty:
            print("DEBUG: source dataframe (post) is empty — nothing to write.")
        else:
            print(f"DEBUG: source dataframe has {len(df)} rows")

        # eventually grabbed from json...
        HEADER_ROW = 13

        # Build a mapping of template header name -> column letter
        # {Student # : C}
        template_columns = {}
        for col_idx, cell in enumerate(ws[HEADER_ROW], start=1):  # header row is ws[1]
            if cell.value:  # skip empty or merged secondary cells
                template_columns[cell.value] = get_column_letter(col_idx)

        # Populate rows from source into template
        current_row = HEADER_ROW + 1  # 14
        #print(list(template_columns.items()))

        for _, df_row in df.iterrows():
            for source_col, template_col_name in column_map.items():
                col_letter = template_columns.get(template_col_name)
                country_col_letter = template_columns.get("Country*")
                city_col_letter = template_columns.get("City*")
                #print(city_col_letter)
                if col_letter and source_col in df_row.index:
                    #print(f"writing '{df_row[source_col]}' to col {col_letter} row {current_row}")
                    ws[f"{col_letter}{current_row}"] = df_row[source_col]
                    # write into Country
                    ws[f"{country_col_letter}{current_row}"] = "Canada"
                    # write into City
                    ws[f"{city_col_letter}{current_row}"] = "Barrie"
            current_row += 1

        folder_path = Templates.POP_TEMPLATE_PATH.value + Templates.POST.value + "/"

        # destroy other templates that exist in /ESL first
        delete_files(folder_path)

        # write new populated ESL EAPC .xlsx file to directory
        cur_time = get_cur_time()
        new_post_report_name = cur_time + "_POST_GuardMe_template.xlsx"
        file_path = folder_path + new_post_report_name
        
        #save new ouput
        wb.save(file_path)

        # write to config.json
        await write_to_json(new_post_report_name, Templates.TEMPLATE_CONFIG_KEY.value, Templates.POST.value)

        print("POST populated successfully")
        return True
    
    #return exception
    except Exception as error:
        print(error)
        return False



# Accounting populate somewhere

async def populate_accounting(df: pd.DataFrame):

    try:
        print("running populate ACCOUNTING")

        # - fee targets
            # - POST / ILAC
            # - EAPC / ESLG

        template_path, key = get_template_path_from_type(Templates.ACCOUNTING.value)
        template_name = await read_from_json(Paths.TEMPLATES_KEY.value, key)
        final_path = template_path + template_name

        wb = load_workbook(final_path)
        ws = wb.active

        # sanity checks
        if df.empty:
            print("DEBUG: source dataframe (ACCOUNTING) is empty — nothing to write.")
        else:
            print(f"DEBUG: source dataframe has {len(df)} rows")

        # eventually grabbed from json...
        HEADER_ROW = 1

        template_columns = {}
        for col_idx, cell in enumerate(ws[HEADER_ROW], start=1):  # header row is ws[1]
            if cell.value:  # skip empty or merged secondary cells
                template_columns[cell.value] = get_column_letter(col_idx)
        
        current_row = HEADER_ROW + 1  # 2
        print(list(template_columns.items()))

        for _, df_row in df.iterrows():
            for source_col, template_col_name in accounting_column_map.items():
                col_letter = template_columns.get(template_col_name)
                notes_letter = template_columns.get("Notes")
                #print(city_col_letter)
                if col_letter and source_col in df_row.index:
                    #print(f"writing '{df_row[source_col]}' to col {col_letter} row {current_row}")
                    ws[f"{col_letter}{current_row}"] = df_row[source_col]
            current_row += 1

        # ws[f"{city_col_letter}{current_row}"] = "Barrie"

        folder_path = Templates.POP_TEMPLATE_PATH.value + Templates.ACCOUNTING.value + "/"

        # destroy other templates that exist in /ESL first
        delete_files(folder_path)

        # write new populated ESL EAPC .xlsx file to directory
        cur_time = get_cur_time()
        new_accounting_report_name = cur_time + "_ACCOUNTING_template.xlsx"
        file_path = folder_path + new_accounting_report_name
        
        #save new ouput
        wb.save(file_path)

        # write to config.json
        await write_to_json(new_accounting_report_name, Templates.TEMPLATE_CONFIG_KEY.value, Templates.ACCOUNTING.value)

        print("ACCOUNTING populated successfully")

        return True

    #return exception
    except Exception as error:
        print(error)
        return False






# accounting fee calculations
# Take a df ; either baseline or compare report
# Parameters:
    # df
    # semester
    # year
# RETURNS - accounting df
async def accounting_calculations(esl_df: pd.DataFrame, semester, year) -> pd.DataFrame:

    # logic such as which semester column to grab from;
        # Fall 2025, or winter 2026, 2025 total fees paid
    
    # function to get DF for post / ilac
    # get_post_df_post(semester, year, df)
        # return DF with same columns as COGNOS report, with just owed / owing rows




    # function to get DF for EAPC
    # get_post_df_eapc(semester, year, df)
        # return DF

    # merge 
    


    # post - with post values
    # ilac - with post values
    
    # esl - with EAPC values

    # merge all three dataframes together and thats all students who are +/- on insurance fees

    

    

    accounting_df = df[pd.to_numeric(df["Fall 2025 Fees Paid"], errors="coerce") != 555]

    # error handling... you try to grab a column, but it does not exist... we return error message to client


    return accounting_df

