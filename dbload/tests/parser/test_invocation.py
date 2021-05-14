from dbload.query_parser import QueryParser


def test_parser(sources):
    parsed = QueryParser.parse(sources)
    assert len(parsed) == 20
