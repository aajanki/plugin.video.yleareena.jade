from resource.lib import extractor


def test_extract_html5():
    media_url = extractor.extract_media_url('yleareena://items/1-787136')

    assert '.m3u8' in media_url
