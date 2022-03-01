from resource.lib import areenaclient


def test_search():
    res = areenaclient.search('Pasila')

    assert len(res) > 0
    assert all(x.homepage for x in res)
    assert all(x.title not in [None, '', '???'] for x in res)
    assert all(x.thumbnail_url for x in res)
    assert all(x.is_folder is False for x in res)


def test_playlist():
    playlist = areenaclient.playlist('1-50552121')

    assert len(playlist) > 0
    assert all(x.homepage for x in playlist)
    assert all(x.title not in [None, '', '???'] for x in playlist)
    assert all(x.thumbnail_url for x in playlist)
    assert all(x.is_folder is False for x in playlist)
