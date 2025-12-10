import pytest
from utils.general import get_insurance_total


@pytest.mark.asyncio
async def test_fall():
    # FALL = 237.60
    total = await get_insurance_total("normal", "fall")
    assert total == 237.60

@pytest.mark.asyncio
async def test_winter():
    # FALL + WINTER = 237.60 + 226.80 = 464.40
    total = await get_insurance_total("normal", "winter")
    assert total == 464.40

@pytest.mark.asyncio
async def test_summer():
    # FALL + WINTER + SUMMER = 237.60 + 226.80 + 219.60 = 684.00
    total = await get_insurance_total("normal", "summer")
    assert total == 684.00

# ---------------------------------------------------------
#  POST TYPE TESTS  (uses fall_post / winter_post / summer_post)
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_post_fall():
    # FALL_POST = 657.00
    total = await get_insurance_total("post", "fall")
    assert total == 657.00


@pytest.mark.asyncio
async def test_post_winter():
    # FALL_POST + WINTER_POST = 657.00 + 437.40 = 1094.40
    total = await get_insurance_total("post", "winter")
    assert total == 1094.40


@pytest.mark.asyncio
async def test_post_summer():
    # FALL_POST + WINTER_POST + SUMMER_POST
    # 657.00 + 437.40 + 219.60 = 1314.00
    total = await get_insurance_total("post", "summer")
    assert total == 1314.00