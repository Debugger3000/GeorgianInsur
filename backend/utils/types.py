from typing import TypedDict

class AccountingTargets(TypedDict):
    fall: int
    winter: int
    summer: int
    fall_post: int
    winter_post: int
    summer_post: int

class PopulatedTemplateData(TypedDict):
    date: str
    row_count: int
