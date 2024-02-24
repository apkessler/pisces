import pytest
from scheduler import hhmmToTime, timeToHhmm
import datetime as dt


def test_hhmmToTime():
    assert hhmmToTime(1200) == dt.time(hour=12, minute=0)
    assert hhmmToTime(0) == dt.time(hour=0, minute=0)
    assert hhmmToTime(30) == dt.time(hour=0, minute=30)
    assert hhmmToTime(259) == dt.time(hour=2, minute=59)
    assert hhmmToTime(1159) == dt.time(hour=11, minute=59)
    assert hhmmToTime(1450) == dt.time(hour=14, minute=50)
    assert hhmmToTime(2359) == dt.time(hour=23, minute=59)

    with pytest.raises(ValueError):
        hhmmToTime(2500)
    with pytest.raises(ValueError):
        hhmmToTime(-100)
    with pytest.raises(ValueError):
        hhmmToTime(1267)


def test_timeToHhmm():
    assert timeToHhmm(dt.time(hour=12, minute=0)) == 1200
    assert timeToHhmm(dt.time(hour=0, minute=0)) == 0
    assert timeToHhmm(dt.time(hour=0, minute=30)) == 30
    assert timeToHhmm(dt.time(hour=2, minute=59)) == 259
    assert timeToHhmm(dt.time(hour=11, minute=59)) == 1159
    assert timeToHhmm(dt.time(hour=14, minute=50)) == 1450
    assert timeToHhmm(dt.time(hour=23, minute=59)) == 2359
