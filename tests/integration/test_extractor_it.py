from resources.lib import extractor


def test_extract_html5():
    manifest_url = extractor.extract_media_url('yleareena://items/1-787136')

    assert manifest_url is not None
    assert '.m3u8' in manifest_url.url
