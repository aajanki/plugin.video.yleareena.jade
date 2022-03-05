from resource.lib import areenaclient


def test_search():
    res = areenaclient.search('Pasila')
    streams = [x for x in res if isinstance(x, areenaclient.StreamLink)]
    navigation = [x for x in res if isinstance(x,areenaclient.SearchNavigationLink)]
    
    assert len(streams) > 0
    assert all(x.homepage for x in streams)
    assert all(x.title not in [None, '', '???'] for x in streams)
    assert all(x.thumbnail_url for x in streams)

    assert len(navigation) == 1
    assert navigation[0].keyword == 'Pasila'
    assert navigation[0].offset > 0


def test_search_pagination():
    res = areenaclient.search('Pasila', offset=30, page_size=10)
    navigation = [x for x in res if isinstance(x,areenaclient.SearchNavigationLink)]
    
    assert len(navigation) == 1
    assert navigation[0].keyword == 'Pasila'
    assert navigation[0].offset == 40


def test_playlist():
    playlist = areenaclient.playlist('1-50552121')

    assert len(playlist) > 0
    assert all(x.homepage for x in playlist)
    assert all(x.title not in [None, '', '???'] for x in playlist)
    assert all(x.thumbnail_url for x in playlist)
    assert all(x.is_folder is False for x in playlist)
