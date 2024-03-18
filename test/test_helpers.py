from helpers import PhCalibrationHelper, PhWarningHelper, PhMessages, wrap_text
import datetime as dt
import os
import json
import pytest


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
    PhWarningHelper.PHWARNINGS_CONFIG_FILE = os.path.join(
        os.path.dirname(__file__), "test_phwarn.json"
    )

    try:
        os.remove(PhWarningHelper.PHWARNINGS_CONFIG_FILE)
    except FileNotFoundError:  # may not exist yet
        pass

    # init the obj
    pwh = PhWarningHelper()
    assert os.path.exists(PhWarningHelper.PHWARNINGS_CONFIG_FILE)
    default_upper = pwh.get_upper_bound()
    default_lower = pwh.get_lower_bound()

    write_dict(PhWarningHelper.PHWARNINGS_CONFIG_FILE, {})

    with pytest.raises(KeyError):
        PhWarningHelper().get_ph_warning_message(
            ph_now=7.0,
            last_cal_date=dt.datetime(2024, 1, 1),
            time_now=dt.datetime(2024, 1, 1),
        )

    PhWarningHelper().save_new_settings(6.2, 8.3)
    pwh = PhWarningHelper()  # Reload
    assert pwh.get_lower_bound() == 6.2
    assert pwh.get_upper_bound() == 8.3

    with pytest.raises(ValueError):
        PhWarningHelper().save_new_settings(10, 7)

    pwh.save_new_settings(default_lower - 1, default_upper + 1)
    pwh.restore_defaults()
    assert pwh.get_lower_bound() == default_lower
    assert pwh.get_upper_bound() == default_upper

    # everything ok - cal same day
    PhWarningHelper().save_new_settings(6, 8)
    assert PhWarningHelper().get_ph_warning_message(
        ph_now=7.0,
        last_cal_date=dt.datetime(2024, 1, 1),
        time_now=dt.datetime(2024, 1, 1),
    ) == ("", "")

    pwh = PhWarningHelper()
    assert pwh.get_upper_bound() == 8
    assert pwh.get_lower_bound() == 6

    # everything ok - cal next month
    assert PhWarningHelper().get_ph_warning_message(
        ph_now=7.0,
        last_cal_date=dt.datetime(2024, 1, 1),
        time_now=dt.datetime(2024, 2, 1),
    ) == ("", "")

    # now before cal! - weird, but just let it slide
    assert PhWarningHelper().get_ph_warning_message(
        ph_now=7.0,
        last_cal_date=dt.datetime(2024, 2, 1),
        time_now=dt.datetime(2024, 1, 1),
    ) == ("", "")

    # cal ok - ph too high
    assert PhWarningHelper().get_ph_warning_message(
        ph_now=9.0,
        last_cal_date=dt.datetime(2024, 1, 1),
        time_now=dt.datetime(2024, 2, 1),
    ) == (PhMessages.MSG_RECALIBRATION_MAYBE_NEEDED, PhMessages.MSG_PH_OUTSIDE_OF_RANGE)

    # cal ok - ph too low
    assert PhWarningHelper().get_ph_warning_message(
        ph_now=4.0,
        last_cal_date=dt.datetime(2024, 1, 1),
        time_now=dt.datetime(2024, 2, 1),
    ) == (PhMessages.MSG_RECALIBRATION_MAYBE_NEEDED, PhMessages.MSG_PH_OUTSIDE_OF_RANGE)

    # reading ok - cal almost 6mo old
    assert PhWarningHelper().get_ph_warning_message(
        ph_now=7.0,
        last_cal_date=dt.datetime(2024, 1, 1),
        time_now=dt.datetime(2024, 6, 28),
    ) == ("", "")

    # reading ok - cal over 6mo old
    assert PhWarningHelper().get_ph_warning_message(
        ph_now=7.0,
        last_cal_date=dt.datetime(2024, 1, 1),
        time_now=dt.datetime(2024, 1, 1) + dt.timedelta(days=181),
    ) == (PhMessages.MSG_RECALIBRATION_MAYBE_NEEDED, PhMessages.MSG_PH_SIX_MONTHS_OLD)

    # reading low - cal over 6mo old
    assert PhWarningHelper().get_ph_warning_message(
        ph_now=4.0,
        last_cal_date=dt.datetime(2024, 1, 1),
        time_now=dt.datetime(2024, 1, 1) + dt.timedelta(days=181),
    ) == (PhMessages.MSG_RECALIBRATION_MAYBE_NEEDED, PhMessages.MSG_PH_SIX_MONTHS_OLD)

    # reading high - cal over 6mo old
    assert PhWarningHelper().get_ph_warning_message(
        ph_now=10.0,
        last_cal_date=dt.datetime(2024, 1, 1),
        time_now=dt.datetime(2024, 1, 1) + dt.timedelta(days=181),
    ) == (PhMessages.MSG_RECALIBRATION_MAYBE_NEEDED, PhMessages.MSG_PH_SIX_MONTHS_OLD)

    # reading ok - just under 1 year old
    assert PhWarningHelper().get_ph_warning_message(
        ph_now=7.0,
        last_cal_date=dt.datetime(2023, 1, 1),  # use 2023 to avoid a leap day...
        time_now=dt.datetime(2023, 12, 31),
    ) == (PhMessages.MSG_RECALIBRATION_MAYBE_NEEDED, PhMessages.MSG_PH_SIX_MONTHS_OLD)

    # reading ok - at  1 year old
    assert PhWarningHelper().get_ph_warning_message(
        ph_now=7.0,
        last_cal_date=dt.datetime(2023, 1, 1),  # use 2023 to avoid a leap day...
        time_now=dt.datetime(2024, 1, 1),
    ) == (PhMessages.MSG_RECALIBRATION_REQUIRED, PhMessages.MSG_PH_ONE_YEAR_OLD)

    # reading low,  - over  1 year old
    assert PhWarningHelper().get_ph_warning_message(
        ph_now=4.0,
        last_cal_date=dt.datetime(2023, 1, 1),  # use 2023 to avoid a leap day...
        time_now=dt.datetime(2024, 2, 1),
    ) == (PhMessages.MSG_RECALIBRATION_REQUIRED, PhMessages.MSG_PH_ONE_YEAR_OLD)

    # reading high,  - over  1 year old
    assert PhWarningHelper().get_ph_warning_message(
        ph_now=10.0,
        last_cal_date=dt.datetime(2023, 1, 1),  # use 2023 to avoid a leap day...
        time_now=dt.datetime(2024, 2, 1),
    ) == (PhMessages.MSG_RECALIBRATION_REQUIRED, PhMessages.MSG_PH_ONE_YEAR_OLD)

    # Check no calibrations
    assert PhWarningHelper().get_ph_warning_message(
        ph_now=7,
        last_cal_date=None,
        time_now=dt.datetime(2024, 2, 1),
    ) == (PhMessages.MSG_RECALIBRATION_REQUIRED, PhMessages.MSG_PH_CAL_NOT_FOUND)

    # Check no calibrations - low
    PhWarningHelper().save_new_settings(8, 9)
    assert PhWarningHelper().get_ph_warning_message(
        ph_now=7,
        last_cal_date=None,
        time_now=dt.datetime(2024, 2, 1),
    ) == (PhMessages.MSG_RECALIBRATION_REQUIRED, PhMessages.MSG_PH_CAL_NOT_FOUND)

    # Check no calibrations - high
    PhWarningHelper().save_new_settings(4.1, 5.2)
    assert PhWarningHelper().get_ph_warning_message(
        ph_now=7.3,
        last_cal_date=None,
        time_now=dt.datetime(2024, 2, 1),
    ) == (PhMessages.MSG_RECALIBRATION_REQUIRED, PhMessages.MSG_PH_CAL_NOT_FOUND)
