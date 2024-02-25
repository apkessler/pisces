import pytest
from helpers import PhCalibrationHelper
import datetime as dt
import os
import json

def test_get_ph_calibrations():
    pch = PhCalibrationHelper()
    pch.PH_CALIBRATION_PATH = os.path.join(os.path.dirname(__file__), 'test_cal1.json')

    os.remove(pch.PH_CALIBRATION_PATH)
    assert pch.get_ph_calibrations() == []

    write_dict(pch.PH_CALIBRATION_PATH, {})
    assert pch.get_ph_calibrations() == []

    data1 = {
        "20230101-120000": {}
    }
    write_dict(pch.PH_CALIBRATION_PATH, data1)
    assert pch.get_ph_calibrations() == [dt.datetime(year=2023, month=1, day=1, hour=12, minute=0, second=0)]



def write_dict(fp:str, data:dict):
    with open(fp, 'w') as fp:
        json.dump(data, fp)
