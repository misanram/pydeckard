#!/usr/bin/env python

import datetime

import pytest
from freezegun import freeze_time

from pydeckard import utils


def test_box():
    text = (
        "En un lugar de la mancha, de cuyo nombre no quiero"
        " acordarme, no ha mucho que vivia un hidalgo de los"
        " de lanza en astillero, adarga antigua, rocín flaco"
        " y galgo corredor."
        )
    expected = """
┌──────────────────────────────────────────────────────────┤ Quijote ├─┐
│ En un lugar de la mancha, de cuyo nombre no quiero acordarme, no ha  │
│ mucho que vivia un hidalgo de los de lanza en astillero, adarga      │
│ antigua, rocín flaco y galgo corredor.                               │
└──────────────────────────────────────────────────────────────────────┘
""".strip()
    assert utils.box("Quijote", text, 72) == expected


@freeze_time("2019-05-16 13:35:16")
def test_since_second():
    ref = datetime.datetime(2019, 5, 16, 13, 35, 15)
    assert utils.since(ref) == "1 second"


@freeze_time("2019-05-16 13:35:21")
def test_since_seconds():
    ref = datetime.datetime(2019, 5, 16, 13, 35, 15)
    assert utils.since(ref) == "6 seconds"


@freeze_time("2019-05-16 13:36:21")
def test_since_minute_and_seconds():
    ref = datetime.datetime(2019, 5, 16, 13, 35, 15)
    assert utils.since(ref) == "1 minute 6 seconds"


@freeze_time("2019-05-16 13:37:21")
def test_since_minutes_and_seconds():
    ref = datetime.datetime(2019, 5, 16, 13, 35, 15)
    assert utils.since(ref) == "2 minutes 6 seconds"


@freeze_time("2019-05-16 14:37:21")
def test_since_hour_and_minutes_and_seconds():
    ref = datetime.datetime(2019, 5, 16, 13, 35, 15)
    assert utils.since(ref) == "1 hour 2 minutes 6 seconds"


@freeze_time("2019-05-16 15:37:21")
def test_since_hours_and_minutes_and_seconds():
    ref = datetime.datetime(2019, 5, 16, 13, 35, 15)
    assert utils.since(ref) == "2 hours 2 minutes 6 seconds"


@freeze_time("2019-05-17 15:37:21")
def test_since_day_hours_and_minutes_and_seconds():
    ref = datetime.datetime(2019, 5, 16, 13, 35, 15)
    assert utils.since(ref) == "1 day 2 hours 2 minutes 6 seconds"


@freeze_time("2019-05-19 15:37:21")
def test_since_days_hours_and_minutes_and_seconds():
    ref = datetime.datetime(2019, 5, 16, 13, 35, 15)
    assert utils.since(ref) == "3 days 2 hours 2 minutes 6 seconds"


def test_tipo_int_parameter():
    int_param = utils.IntParameter('edad', 'Edad legal', start_value=18)
    assert int_param.get_value('23') == 23


def test_tipo_int_parameter_outbounds():
    int_param = utils.IntParameter('edad', 'Edad legal', start_value=18)
    with pytest.raises(ValueError):
        int_param.get_value('13')


def test_tipo_str_parameter_with_acceptables():
    values = ['ALFA', 'BETA', 'GAMMA', 'DELTA']
    greek_param = utils.StrParameter(
        'letter',
        'Legra griega',
        acceptable=values,
        )
    assert greek_param.get_value('BETA') == 'BETA'


def test_tipo_str_parameter_with_acceptables_failure():
    values = ['ALFA', 'BETA', 'GAMMA', 'DELTA']
    greek_param = utils.StrParameter(
        'letter',
        'Legra griega',
        acceptable=values,
        )
    with pytest.raises(ValueError):
        greek_param.get_value('omega')


if __name__ == "__main__":
    pytest.main()
