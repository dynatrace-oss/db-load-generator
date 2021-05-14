import random

import pytest

from dbload import scenario, get_context


def test_register_function():
    @scenario
    def my_scenario_function(connection):
        pass

    # Scenario is registered
    ctx = get_context()
    assert "my_scenario_function" in ctx.scenarios

    # And infused with queries
    # assert hasattr(my_scenario_function, "insert_department")


def test_do_not_infuse():
    @scenario(infuse=False)
    def no_infuse(con):
        pass

    # Scenario is registered
    ctx = get_context()
    assert "no_infuse" in ctx.scenarios

    # And not infused
    assert not hasattr(no_infuse, "insert_department")


def test_register_under_different_name():
    @scenario(name="other_name")
    def explicit_name_scenario(con):
        pass

    ctx = get_context()
    assert "explicit_name_scenario" not in ctx.scenarios
    assert "other_name" in ctx.scenarios
