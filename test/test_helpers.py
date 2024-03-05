from helpers import PhCalibrationHelper, get_ph_warning_message, PhMessages, wrap_text
import datetime as dt
import os
import json


def test_get_ph_calibrations():
    pch = PhCalibrationHelper()
    pch.PH_CALIBRATION_PATH = os.path.join(os.path.dirname(__file__), "test_cal1.json")

    try:
        os.remove(pch.PH_CALIBRATION_PATH)
    except FileNotFoundError:  # may not exist yet
        pass
    assert pch.get_ph_calibrations() == []

    write_dict(pch.PH_CALIBRATION_PATH, {})
    assert pch.get_ph_calibrations() == []

    data1 = {"2023-01-05T12:00:00": {}}
    write_dict(pch.PH_CALIBRATION_PATH, data1)
    assert pch.get_ph_calibrations() == [
        dt.datetime(year=2023, month=1, day=5, hour=12, minute=0, second=0)
    ]

    pch.record_calibration(dt.datetime(year=2023, month=2, day=3), {"field": 1})
    cals = pch.get_ph_calibrations()
    assert len(cals) == 2
    assert cals[1] == dt.datetime(year=2023, month=2, day=3)

    os.remove(pch.PH_CALIBRATION_PATH)
    pch.record_calibration(dt.datetime(year=2023, month=2, day=3), {"field": 1})
    cals = pch.get_ph_calibrations()
    assert len(cals) == 1


def write_dict(fp: str, data: dict):
    with open(fp, "w") as fp:
        json.dump(data, fp)


def test_wrap():
    assert "" == wrap_text("", 20)
    assert "This is\na test" == wrap_text("This is a test", width=7)


def test_get_ph_warning_message():
    # everything ok - cal same day
    assert get_ph_warning_message(
        ph_now=7.0,
        last_cal_date=dt.datetime(2024, 1, 1),
        time_now=dt.datetime(2024, 1, 1),
        lower_ph=6,
        upper_ph=8,
    ) == ("", "")

    # everything ok - cal next month
    assert get_ph_warning_message(
        ph_now=7.0,
        last_cal_date=dt.datetime(2024, 1, 1),
        time_now=dt.datetime(2024, 2, 1),
        lower_ph=6,
        upper_ph=8,
    ) == ("", "")

    # now before cal! - weird, but just let it slide
    assert get_ph_warning_message(
        ph_now=7.0,
        last_cal_date=dt.datetime(2024, 2, 1),
        time_now=dt.datetime(2024, 1, 1),
        lower_ph=6,
        upper_ph=8,
    ) == ("", "")

    # cal ok - ph too high
    assert get_ph_warning_message(
        ph_now=9.0,
        last_cal_date=dt.datetime(2024, 1, 1),
        time_now=dt.datetime(2024, 2, 1),
        lower_ph=6,
        upper_ph=8,
    ) == (PhMessages.MSG_RECALIBRATION_MAYBE_NEEDED, PhMessages.MSG_PH_OUTSIDE_OF_RANGE)

    # cal ok - ph too low
    assert get_ph_warning_message(
        ph_now=4.0,
        last_cal_date=dt.datetime(2024, 1, 1),
        time_now=dt.datetime(2024, 2, 1),
        lower_ph=6,
        upper_ph=8,
    ) == (PhMessages.MSG_RECALIBRATION_MAYBE_NEEDED, PhMessages.MSG_PH_OUTSIDE_OF_RANGE)

    # reading ok - cal almost 6mo old
    assert get_ph_warning_message(
        ph_now=7.0,
        last_cal_date=dt.datetime(2024, 1, 1),
        time_now=dt.datetime(2024, 6, 28),
        lower_ph=6,
        upper_ph=8,
    ) == ("", "")

    # reading ok - cal over 6mo old
    assert get_ph_warning_message(
        ph_now=7.0,
        last_cal_date=dt.datetime(2024, 1, 1),
        time_now=dt.datetime(2024, 1, 1) + dt.timedelta(days=181),
        lower_ph=6,
        upper_ph=8,
    ) == (PhMessages.MSG_RECALIBRATION_MAYBE_NEEDED, PhMessages.MSG_PH_SIX_MONTHS_OLD)

    # reading low - cal over 6mo old
    assert get_ph_warning_message(
        ph_now=4.0,
        last_cal_date=dt.datetime(2024, 1, 1),
        time_now=dt.datetime(2024, 1, 1) + dt.timedelta(days=181),
        lower_ph=6,
        upper_ph=8,
    ) == (PhMessages.MSG_RECALIBRATION_MAYBE_NEEDED, PhMessages.MSG_PH_SIX_MONTHS_OLD)

    # reading high - cal over 6mo old
    assert get_ph_warning_message(
        ph_now=10.0,
        last_cal_date=dt.datetime(2024, 1, 1),
        time_now=dt.datetime(2024, 1, 1) + dt.timedelta(days=181),
        lower_ph=6,
        upper_ph=8,
    ) == (PhMessages.MSG_RECALIBRATION_MAYBE_NEEDED, PhMessages.MSG_PH_SIX_MONTHS_OLD)

    # reading ok - just under 1 year old
    assert get_ph_warning_message(
        ph_now=7.0,
        last_cal_date=dt.datetime(2023, 1, 1),  # use 2023 to avoid a leap day...
        time_now=dt.datetime(2023, 12, 31),
        lower_ph=6,
        upper_ph=8,
    ) == (PhMessages.MSG_RECALIBRATION_MAYBE_NEEDED, PhMessages.MSG_PH_SIX_MONTHS_OLD)

    # reading ok - at  1 year old
    assert get_ph_warning_message(
        ph_now=7.0,
        last_cal_date=dt.datetime(2023, 1, 1),  # use 2023 to avoid a leap day...
        time_now=dt.datetime(2024, 1, 1),
        lower_ph=6,
        upper_ph=8,
    ) == (PhMessages.MSG_RECALIBRATION_REQUIRED, PhMessages.MSG_PH_ONE_YEAR_OLD)

    # reading low,  - over  1 year old
    assert get_ph_warning_message(
        ph_now=4.0,
        last_cal_date=dt.datetime(2023, 1, 1),  # use 2023 to avoid a leap day...
        time_now=dt.datetime(2024, 2, 1),
        lower_ph=6,
        upper_ph=8,
    ) == (PhMessages.MSG_RECALIBRATION_REQUIRED, PhMessages.MSG_PH_ONE_YEAR_OLD)

    # reading high,  - over  1 year old
    assert get_ph_warning_message(
        ph_now=10.0,
        last_cal_date=dt.datetime(2023, 1, 1),  # use 2023 to avoid a leap day...
        time_now=dt.datetime(2024, 2, 1),
        lower_ph=6,
        upper_ph=8,
    ) == (PhMessages.MSG_RECALIBRATION_REQUIRED, PhMessages.MSG_PH_ONE_YEAR_OLD)

    # Check no calibrations
    assert get_ph_warning_message(
        ph_now=7,
        last_cal_date=None,
        time_now=dt.datetime(2024, 2, 1),
        lower_ph=6,
        upper_ph=8,
    ) == (PhMessages.MSG_RECALIBRATION_REQUIRED, PhMessages.MSG_PH_CAL_NOT_FOUND)

    # Check no calibrations - low
    assert get_ph_warning_message(
        ph_now=7,
        last_cal_date=None,
        time_now=dt.datetime(2024, 2, 1),
        lower_ph=8,
        upper_ph=9,
    ) == (PhMessages.MSG_RECALIBRATION_REQUIRED, PhMessages.MSG_PH_CAL_NOT_FOUND)

    # Check no calibrations - high
    assert get_ph_warning_message(
        ph_now=7,
        last_cal_date=None,
        time_now=dt.datetime(2024, 2, 1),
        lower_ph=4,
        upper_ph=5,
    ) == (PhMessages.MSG_RECALIBRATION_REQUIRED, PhMessages.MSG_PH_CAL_NOT_FOUND)
