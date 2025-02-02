###############################################################################
#
# Test on_demand with high memory usage xlsx.
#

import sys
import time
from gc import get_referents
from types import FunctionType, ModuleType

import pytest

import xlrd

from .base import from_this_dir

# ----------------------------- test memory without psutil --------------------------
# solution from : https://stackoverflow.com/a/30316760/3655984

# Custom objects know their class.
# Function objects seem to know way too much, including modules.
# Exclude modules as well.
BLACKLIST = type, ModuleType, FunctionType


def getsize(obj):
    """sum size of object & members."""
    if isinstance(obj, BLACKLIST):
        raise TypeError('getsize() does not take argument of type: ' + str(type(obj)))
    seen_ids = set()
    size = 0
    objects = [obj]
    while objects:
        need_referents = []
        for obj in objects:
            if not isinstance(obj, BLACKLIST) and id(obj) not in seen_ids:
                seen_ids.add(id(obj))
                size += sys.getsizeof(obj)
                need_referents.append(obj)
        objects = get_referents(*need_referents)
    return size


# ------------------------------------------------------------------------------------


def test_xlsx_on_demand():
    test_file = from_this_dir('test_high_mem.xlsx')

    # without on_demand, time and memory go high
    # t0 = time.perf_counter()
    # with xlrd.open_workbook(test_file) as workbook:
    #     # access the last sheet
    #     worksheet = workbook.sheet_by_name("Store days 100%")
    #     test_val = worksheet.cell(rowx=49, colx=24).value
    #     assertEqual(test_val, 59, "Read out data should equal written one")
    #
    #     # it took about 54 seconds and memory usage should go up around 300MB
    #     original_load_time = time.perf_counter() - t0

    # with on_demand, everything should be quick
    t0 = time.time()
    with xlrd.open_workbook(test_file, on_demand=True) as workbook:
        # access the last sheet
        worksheet = workbook.sheet_by_name("Store days 100%")
        assert 59.0 == worksheet.cell(rowx=49, colx=24).value

        # it took around 14 seconds and memory usage about 83MB for this sheet
        new_load_time = time.time() - t0

    # check if the load time is indeed faster
    assert new_load_time < 35


def test_xlsx_unload_sheet():
    test_file = from_this_dir('test_high_mem.xlsx')

    with xlrd.open_workbook(test_file, on_demand=True) as workbook:
        # access the last sheet, around 14 second to load
        wb_size_begin = getsize(workbook)

        worksheet = workbook.sheet_by_name("Store days 100%")
        # wb_size_now = getsize(workbook)

        assert 59.0 == worksheet.cell(rowx=49, colx=24).value

        workbook.unload_sheet("Store days 100%")
        wb_size_then = getsize(workbook)

    assert wb_size_begin == pytest.approx(wb_size_then, 1e-3)
