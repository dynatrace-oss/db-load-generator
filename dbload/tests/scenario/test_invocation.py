import pytest

from dbload import get_context


# def test_playing_implicit_scenario(connection):
#     ctx = get_context()
#     setup = ctx.scenarios.setup.scenario

#     # Run scenario
#     setup(connection)

#     # Verify proper amount of queries was called
#     assert connection._cur._num_execute_called == 6
