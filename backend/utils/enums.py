

from enum import Enum

class Status(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"

class Paths(Enum):
    CONFIG_PATH = "./data/config.json"
    BASELINE_PROPS_KEY = "baseline_props"
    BASELINE_PATH = "./data/baseline/"
    TEMPLATES_KEY = "template_props"
    INSURANCE_TEMPLATES = "insurance_templates"
    INSURANCE_TEMPLATES_PATH = "./data/templates/insurance/"
    ACCOUNTING_TEMPLATES = "accounting_templates"
    ACCOUNTING_TEMPLATES_PATH = "./data/templates/accounting/"
    SETTINGS_FEES_KEY = "insurance_targets"
    TEMPLATE_PATH = "./data/templates/"

class Templates(Enum):
    ESL = "ESL"
    ILAC = "ILAC"
    POST = "POST"
    ACCOUNTING = "ACCOUNTING"
    TEMPLATE_CONFIG_KEY = "populated_templates"
    POP_TEMPLATE_PATH = "./data/populated_templates/"
    ACCOUNT_TEMPLATE_PATH  = "./data/populated_templates/"
# from utils.enums import Status
# Status.RUNNING

class Accounting(Enum):
    INSURANCE_KEY = "insurance_targets"
    FALL = "fall"
    WINTER = "winter"
    SUMMER = "summer"
    FALL_POST = "fall_post"
    WINTER_POST = "winter_post"
    SUMMER_POST = "summer_post"