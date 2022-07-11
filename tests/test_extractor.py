from resources.lib.extractor import get_text, iso_duration_as_seconds


def test_get_text_default_is_fi():
    msg = get_text({
        'fi': 'Teksti suomeksi',
        'sv': 'Samma på Svenska'
    })

    assert msg == 'Teksti suomeksi'


def test_get_text_prefer_language():
    msg = get_text({
        'fi': 'Teskti suomeksi',
        'sv': 'Samma på Svenska'
    }, prefer_language='sv')

    assert msg == 'Samma på Svenska'


def test_get_text_fi_not_available():
    text_object = {
        'sv': 'Svenska',
        'en': 'English',
    }
    msg = get_text(text_object)

    assert msg in text_object.values()


def test_iso_duration_as_seconds():
    assert iso_duration_as_seconds('PT1832S') == 1832
    assert iso_duration_as_seconds('PT1H28M14S') == 5294
    assert iso_duration_as_seconds('PT23M49.600S') == 1429


def test_iso_duration_invalid_input():
    assert iso_duration_as_seconds('') is None
    assert iso_duration_as_seconds('PT123') is None
    assert iso_duration_as_seconds('PTS') is None
    assert iso_duration_as_seconds('abc') is None
