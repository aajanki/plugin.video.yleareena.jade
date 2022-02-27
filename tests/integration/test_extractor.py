from resource.lib import extractor


def test_extract_html5():
    stream = extractor.extract('yleareena://items/1-787136')

    assert '.m3u8' in stream.get('url', '')
