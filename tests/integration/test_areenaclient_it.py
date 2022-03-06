from resources.lib import areenaclient


def test_search():
    res = areenaclient.search('Pasila')
    streams = [x for x in res if isinstance(x, areenaclient.StreamLink)]
    navigation = [x for x in res if isinstance(x, areenaclient.SearchNavigationLink)]

    assert len(streams) > 0
    assert all(x.homepage for x in streams)
    assert all(x.title not in [None, '', '???'] for x in streams)

    assert len(navigation) == 1
    assert navigation[0].keyword == 'Pasila'
    assert navigation[0].offset > 0


def test_search_pagination():
    res = areenaclient.search('Pasila', offset=30, page_size=10)
    navigation = [x for x in res if isinstance(x, areenaclient.SearchNavigationLink)]

    assert len(navigation) == 1
    assert navigation[0].keyword == 'Pasila'
    assert navigation[0].offset == 40


def test_playlist():
    playlist = areenaclient.playlist('1-50552121', page_size=10)
    streams = [x for x in playlist if isinstance(x, areenaclient.StreamLink)]
    navigation = [x for x in playlist if isinstance(x, areenaclient.SeriesNavigationLink)]

    assert len(streams) > 0
    assert all(x.homepage for x in streams)
    assert all(x.title not in [None, '', '???'] for x in streams)
    assert all(x.published is not None for x in streams)
    assert all(x.thumbnail for x in streams)
    assert all(x.is_folder is False for x in streams)

    assert len(navigation) == 1
    assert navigation[0].series_id == '1-50552121'
    assert navigation[0].offset > 0


def test_playlist_pagination():
    playlist = areenaclient.playlist('1-50552121', offset=20, page_size=5)
    navigation = [x for x in playlist if isinstance(x, areenaclient.SeriesNavigationLink)]

    assert len(navigation) == 1
    assert navigation[0].series_id == '1-50552121'
    assert navigation[0].offset == 25
