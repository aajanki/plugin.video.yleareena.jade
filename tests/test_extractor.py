from datetime import datetime, timedelta, timezone
from resource.lib.extractor import get_text, parse_publication_event_date


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


def test_event_date_parser_empty():
    assert parse_publication_event_date({}) is None


def test_event_date_parser_earliest_date():
    metadata = {
        'publicationEvent': [
            {
                'temporalStatus': 'currently',
                'startTime': '2020-01-30T18:30:00+02:00',
            },
            {
                'temporalStatus': 'currently',
                'startTime': '2019-06-30T20:54:28+03:00',
            },
            {
                'temporalStatus': 'currently',
                'startTime': '2019-08-10T20:00:00+03:00',
            }
        ]
    }

    parsed = parse_publication_event_date(metadata)
    assert parsed == datetime(2019, 6, 30, 20, 54, 28, tzinfo=timezone(timedelta(hours=3)))
