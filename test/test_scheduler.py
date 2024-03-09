import pytest
from scheduler import hhmmToTime, timeToHhmm, Scheduler
import datetime as dt
from loguru import logger
from typing import List

class MockHardwareControlClient:
    def __init__(self, channel):
        NUM_RELAYS = 8
        NUM_LIGHTS = 3
        self.temperature_degC = 0
        self.pH = 7
        self.relays = [False] * NUM_RELAYS
        self.light_colors = ["off"] * NUM_LIGHTS
        self.phSensorSampleTime_ms = 1

    def getTemperature_degC(self) -> float:
        """
        Get the latest temperature reading in degrees C
        """
        return self.temperature_degC

    def getTemperature_degF(self) -> float:
        """
        Get the latest temperature reading in degrees F
        """
        return (self.temperature_degC * 9.0) / 5.0 + 32.0

    def getPH(self) -> float:
        """
        Get the latest pH reading.
        """
        return self.pH

    def echo(self, payload="Test123") -> None:
        """
        Send and receive a loopback test of given string.
        """
        pass

    def setRelayState(self, chn, isEngaged) -> None:
        """
        Set state on given channel to given state
        """
        self.relays[chn - 1] = isEngaged

    def getRelayStates(self) -> List[bool]:
        """
        Get all relay states as list.
        Unpack from GRPC object and return as native Python list.
        """
        return self.relays

    def setLightColor(self, lightId: int, color_name: str, scope: str = "") -> None:
        """Set given light to given color.

        Parameters
        ----------
        lightId : int
            Light to change
        color_name : str
            One of ['off', 'white', 'blue']
        scope : str, optional
            Command scope, by default ""
        """
        assert color_name in ["off", "white", "blue"]
        logger.debug(f"Set {lightId} to {color_name}")
        self.light_colors[lightId - 1] = color_name

    def getLightColors(self) -> List[str]:
        """Get all light colors and return as list of strings.
            Unpack from GRPC object and return as native Python list.

        Returns
        -------
        List[str]
            List of current light colors
        """
        return self.light_colors

    def moveStepper(self, numSteps: int, isReverse: bool = False) -> None:
        """
        Move stepper motor specified number of steps
        """
        pass

    def stopStepper(self) -> None:
        """Stop the stepper motor from doing any motion"""
        pass

    def getIsStepperActive(self) -> bool:
        """Get true/false if stepper is active right now"""
        return False

    def setScope(self, scope="") -> None:
        """Set the Light Control scope."""
        pass

    def setPhSensorSampleTime(self, time_msec: int) -> None:
        """time of 0 = return to default"""
        self.phSensorSampleTime_ms = time_msec

    def getPhSensorSampleTime_ms(self) -> int:
        return self.phSensorSampleTime_ms

    def sendPhSensorCommand(self, cmd: str) -> str:
        pass


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


@pytest.fixture
def jData():
    _jData = {
        "light_schedules": {
            "tank_lights": {
                "lights": {
                    "TankLight1": {"white_enabled": True, "blue_enabled": True},
                    "TankLight2": {"white_enabled": True, "blue_enabled": True},
                },
                "sunrise_hhmm": 830,
                "sunset_hhmm": 1730,
                "blue_lights_at_night": False,
                "eclipse_enabled": False,
                "eclipse_white_duration_min": 6,
                "eclipse_blue_duration_min": 4,
                "manual_eclipse_enabled": False,
                "manual_eclipse_duration_sec": 5,
            }
        },
        "outlet_schedules": {
            "outlet1": {
                "mode": "timer",
                "sunrise_hhmm": 830,
                "sunset_hhmm": 1730,
                "description": "Grow Lights",
            },
        },
    }

    yield _jData


def test_event(jData):
    class test_event:
        count = 0

        def __init__(self):
            test_event.count += 1
            print(f"called test event! {test_event.count}")

    hwCntrl = MockHardwareControlClient(0)
    sch = Scheduler(hwCntrl)
    sch.build_light_timers(jData["light_schedules"])
    sch.build_outlet_timers(jData["outlet_schedules"])
    sch.add_event("dispense", 500, test_event)

    TEST_YEAR = 2024
    TEST_MONTH = 1
    TEST_DAY = 1
    now = dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY, 0, 0)

    while now < dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY, 5, 0):
        sch.update(now)
        assert test_event.count == 0
        now = now + dt.timedelta(seconds=30)

    while now <= dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY + 1, 0, 0):
        sch.update(now)
        assert test_event.count == 1
        now = now + dt.timedelta(seconds=30)


def test_scheduler_off_at_night(jData):
    hwCntrl = MockHardwareControlClient(0)
    sch = Scheduler(hwCntrl)
    sch.build_light_timers(jData["light_schedules"])
    sch.build_outlet_timers(jData["outlet_schedules"])

    TEST_YEAR = 2024
    TEST_MONTH = 1
    TEST_DAY = 1

    now = dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY, 0, 0)

    sch.update(now)
    assert hwCntrl.getLightColors() == ["off", "off", "off"]

    while now <= dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY, 8, 30):
        sch.update(now)
        assert hwCntrl.getLightColors() == ["off", "off", "off"]
        now = now + dt.timedelta(seconds=30)

    while now < dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY, 17, 30):
        sch.update(now)
        assert hwCntrl.getLightColors() == ["white", "white", "white"]
        now = now + dt.timedelta(seconds=30)

    while now <= dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY + 1):
        sch.update(now)
        assert hwCntrl.getLightColors() == ["off", "off", "off"]
        now = now + dt.timedelta(seconds=30)


def test_scheduler_blue_at_night(jData):
    hwCntrl = MockHardwareControlClient(0)
    jData["light_schedules"]["tank_lights"]["blue_lights_at_night"] = True
    sch = Scheduler(hwCntrl)
    sch.build_light_timers(jData["light_schedules"])
    sch.build_outlet_timers(jData["outlet_schedules"])

    TEST_YEAR = 2024
    TEST_MONTH = 1
    TEST_DAY = 1

    # Do a day with blue on at night
    now = dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY, 0, 0)
    while now <= dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY, 8, 30):
        sch.update(now)
        assert hwCntrl.getLightColors() == ["blue", "blue", "off"]
        now = now + dt.timedelta(seconds=30)

    while now < dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY, 17, 30):
        sch.update(now)
        assert hwCntrl.getLightColors() == ["white", "white", "white"]
        now = now + dt.timedelta(seconds=30)

    while now <= dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY + 1):
        sch.update(now)
        assert hwCntrl.getLightColors() == ["blue", "blue", "off"]
        now = now + dt.timedelta(seconds=30)


def test_scheduler_eclipse(jData):
    jData["light_schedules"]["tank_lights"]["eclipse_enabled"] = True

    hwCntrl = MockHardwareControlClient(0)
    sch = Scheduler(hwCntrl)
    sch.build_light_timers(jData["light_schedules"])
    sch.build_outlet_timers(jData["outlet_schedules"])

    TEST_YEAR = 2024
    TEST_MONTH = 1
    TEST_DAY = 1

    # Do a day with blue on at night
    now = dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY, 0, 0)
    while now <= dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY, 8, 30):
        sch.update(now)
        assert hwCntrl.getLightColors() == ["off", "off", "off"]
        now = now + dt.timedelta(seconds=30)

    # Now its past 8:30!

    sunset_time = dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY, 17, 30)
    while now < sunset_time:
        next_eclipse_start = now + dt.timedelta(minutes=6)
        while now < next_eclipse_start:
            sch.update(now)
            assert hwCntrl.getLightColors() == ["white", "white", "white"]
            now = now + dt.timedelta(seconds=30)

        next_eclipse_end = now + dt.timedelta(minutes=4)
        while now < min(next_eclipse_end, sunset_time):
            sch.update(now)
            assert hwCntrl.getLightColors() == ["blue", "blue", "white"]
            now = now + dt.timedelta(seconds=30)

    while now <= dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY + 1):
        sch.update(now)
        assert hwCntrl.getLightColors() == ["off", "off", "off"]
        now = now + dt.timedelta(seconds=30)


@pytest.mark.parametrize("white1", [False, True])
@pytest.mark.parametrize("blue1", [False, True])
@pytest.mark.parametrize("white2", [False, True])
@pytest.mark.parametrize("blue2", [False, True])
@pytest.mark.parametrize("blue_at_night", [False, True])
def test_scheduler_eclipse_lights_disabled(
    jData, white1, blue1, white2, blue2, blue_at_night
):
    jTankLights = jData["light_schedules"]["tank_lights"]
    jTankLights["eclipse_enabled"] = True
    jTankLights["eclipse_blue_duration_min"] = 2
    jTankLights["eclipse_white_duration_min"] = 3
    jTankLights["blue_lights_at_night"] = blue_at_night

    jTankLights["lights"]["TankLight1"]["white_enabled"] = white1
    jTankLights["lights"]["TankLight1"]["blue_enabled"] = blue1

    jTankLights["lights"]["TankLight2"]["white_enabled"] = white2
    jTankLights["lights"]["TankLight2"]["blue_enabled"] = blue2

    hwCntrl = MockHardwareControlClient(0)
    sch = Scheduler(hwCntrl)
    sch.build_light_timers(jData["light_schedules"])
    sch.build_outlet_timers(jData["outlet_schedules"])

    TEST_YEAR = 2024
    TEST_MONTH = 10
    TEST_DAY = 1

    now = dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY, 0, 0)

    # Do a day with blue on at night
    for day_offset in range(2):
        while now <= dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY + day_offset, 8, 30):
            sch.update(now)
            assert hwCntrl.getLightColors() == [
                "blue" if (blue1 and blue_at_night) else "off",
                "blue" if (blue2 and blue_at_night) else "off",
                "off",
            ]
            now = now + dt.timedelta(seconds=30)

        # Now its past 8:30!

        sunset_time = dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY + day_offset, 17, 30)
        while now < sunset_time:
            next_eclipse_start = now + dt.timedelta(minutes=3)
            while now < next_eclipse_start:
                sch.update(now)
                assert hwCntrl.getLightColors() == [
                    "white" if white1 else "off",
                    "white" if white2 else "off",
                    "white",
                ]
                now = now + dt.timedelta(seconds=30)

            next_eclipse_end = now + dt.timedelta(minutes=2)
            while now < min(next_eclipse_end, sunset_time):
                sch.update(now)
                assert hwCntrl.getLightColors() == [
                    "blue" if blue1 else "off",
                    "blue" if blue2 else "off",
                    "white",
                ]
                now = now + dt.timedelta(seconds=30)

        while now <= dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY + day_offset + 1):
            sch.update(now)
            assert hwCntrl.getLightColors() == [
                "blue" if (blue1 and blue_at_night) else "off",
                "blue" if (blue2 and blue_at_night) else "off",
                "off",
            ]
            now = now + dt.timedelta(seconds=30)


@pytest.mark.parametrize("white1", [False, True])
@pytest.mark.parametrize("blue1", [False, True])
@pytest.mark.parametrize("white2", [False, True])
@pytest.mark.parametrize("blue2", [False, True])
@pytest.mark.parametrize("blue_at_night", [False, True])
def test_scheduler_eclipse_pause_resume(
    jData, white1, blue1, white2, blue2, blue_at_night
):
    jTankLights = jData["light_schedules"]["tank_lights"]
    jTankLights["eclipse_enabled"] = True
    jTankLights["eclipse_blue_duration_min"] = 4
    jTankLights["eclipse_white_duration_min"] = 6
    jTankLights["blue_lights_at_night"] = blue_at_night

    jTankLights["lights"]["TankLight1"]["white_enabled"] = white1
    jTankLights["lights"]["TankLight1"]["blue_enabled"] = blue1

    jTankLights["lights"]["TankLight2"]["white_enabled"] = white2
    jTankLights["lights"]["TankLight2"]["blue_enabled"] = blue2

    hwCntrl = MockHardwareControlClient(0)
    sch = Scheduler(hwCntrl)
    sch.build_light_timers(jData["light_schedules"])
    sch.build_outlet_timers(jData["outlet_schedules"])

    TEST_YEAR = 2024
    TEST_MONTH = 1
    TEST_DAY = 1

    now = dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY, 0, 0)
    while now <= dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY, 6, 30):
        sch.update(now)
        assert hwCntrl.getLightColors() == [
            "blue" if (blue1 and blue_at_night) else "off",
            "blue" if (blue2 and blue_at_night) else "off",
            "off",
        ]
        now = now + dt.timedelta(seconds=30)

    sch.disable_timers(["tank_lights", "outlet1"])

    # Lights should still be  off
    next_checkpoint = now + dt.timedelta(minutes=80)
    while now < next_checkpoint:
        sch.update(now)
        assert hwCntrl.getLightColors() == [
            "blue" if (blue1 and blue_at_night) else "off",
            "blue" if (blue2 and blue_at_night) else "off",
            "off",
        ]
        now = now + dt.timedelta(seconds=30)
    logger.debug(f"At checkpoint: {next_checkpoint}")

    sch.resume_timers(["tank_lights", "outlet1"], now)

    while now <= dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY, 8, 30):
        sch.update(now)
        assert hwCntrl.getLightColors() == [
            "blue" if (blue1 and blue_at_night) else "off",
            "blue" if (blue2 and blue_at_night) else "off",
            "off",
        ]
        now = now + dt.timedelta(seconds=30)

    # Now its past 8:30!
    sch.update(now)
    assert hwCntrl.getLightColors() == [
        "white" if white1 else "off",
        "white" if white2 else "off",
        "white",
    ]

    sch.disable_timers(["tank_lights", "outlet1"])

    # Lights should still be on, through the eclipse
    next_checkpoint = now + dt.timedelta(minutes=80)
    while now < next_checkpoint:
        sch.update(now)
        assert hwCntrl.getLightColors() == [
            "white" if white1 else "off",
            "white" if white2 else "off",
            "white",
        ]
        now = now + dt.timedelta(seconds=30)

    sch.resume_timers(["tank_lights", "outlet1"], now)

    sunset_time = dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY, 17, 30)
    while now < sunset_time:
        next_eclipse_start = now + dt.timedelta(minutes=6)
        while now < next_eclipse_start:
            sch.update(now)
            assert hwCntrl.getLightColors() == [
                "white" if white1 else "off",
                "white" if white2 else "off",
                "white",
            ]
            now = now + dt.timedelta(seconds=30)

        next_eclipse_end = now + dt.timedelta(minutes=4)
        while now < min(next_eclipse_end, sunset_time):
            sch.update(now)
            assert hwCntrl.getLightColors() == [
                "blue" if blue1 else "off",
                "blue" if blue2 else "off",
                "white",
            ]
            now = now + dt.timedelta(seconds=30)

    ## SUNSET
    next_checkpoint = now + dt.timedelta(minutes=120)
    while now <= next_checkpoint:
        sch.update(now)
        assert hwCntrl.getLightColors() == [
            "blue" if (blue1 and blue_at_night) else "off",
            "blue" if (blue2 and blue_at_night) else "off",
            "off",
        ]
        now = now + dt.timedelta(seconds=30)

    sch.disable_timers(["tank_lights", "outlet1"])
    next_checkpoint = now + dt.timedelta(minutes=120)
    while now <= next_checkpoint:
        sch.update(now)
        assert hwCntrl.getLightColors() == [
            "blue" if (blue1 and blue_at_night) else "off",
            "blue" if (blue2 and blue_at_night) else "off",
            "off",
        ]
        now = now + dt.timedelta(seconds=30)

    sch.resume_timers(["tank_lights", "outlet1"], now)

    while now <= dt.datetime(TEST_YEAR, TEST_MONTH, TEST_DAY + 1):
        sch.update(now)
        assert hwCntrl.getLightColors() == [
            "blue" if (blue1 and blue_at_night) else "off",
            "blue" if (blue2 and blue_at_night) else "off",
            "off",
        ]
        now = now + dt.timedelta(seconds=30)