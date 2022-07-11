from resources.lib.extractor import iso_duration_as_seconds


def test_iso_duration_as_seconds():
    assert iso_duration_as_seconds('PT1832S') == 1832
    assert iso_duration_as_seconds('PT1H28M14S') == 5294
    assert iso_duration_as_seconds('PT23M49.600S') == 1429


def test_iso_duration_invalid_input():
    assert iso_duration_as_seconds('') is None
    assert iso_duration_as_seconds('PT123') is None
    assert iso_duration_as_seconds('PTS') is None
    assert iso_duration_as_seconds('abc') is None
