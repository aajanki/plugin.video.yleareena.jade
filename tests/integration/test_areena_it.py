from resources.lib import areena


def test_search():
    res = areena.search('Pasila')
    streams = [x for x in res if isinstance(x, areena.StreamLink)]
    navigation = [x for x in res if isinstance(x, areena.SearchNavigationLink)]

    assert len(streams) > 0
    assert all(x.homepage for x in streams)
    assert all(x.title not in [None, '', '???'] for x in streams)

    assert len(navigation) == 1
    assert navigation[0].keyword == 'Pasila'
    assert navigation[0].offset > 0


def test_search_pagination():
    res = areena.search('Pasila', offset=30, page_size=10)
    navigation = [x for x in res if isinstance(x, areena.SearchNavigationLink)]

    assert len(navigation) == 1
    assert navigation[0].keyword == 'Pasila'
    assert navigation[0].offset == 40


def test_playlist_one_season():
    # This series has only one season. Should list episodes directly
    # (without the season layer)
    playlist = areena.playlist('1-4022508', page_size=6)
    streams = [x for x in playlist if isinstance(x, areena.StreamLink)]
    navigation = [x for x in playlist if isinstance(x, areena.SeriesNavigationLink)]

    assert len(streams) > 0
    assert all(x.homepage for x in streams)
    assert all(x.title not in [None, '', '???'] for x in streams)
    assert all(x.duration_seconds is not None for x in streams)
    assert all(x.published is not None for x in streams)
    assert all(x.thumbnail is not None for x in streams)
    assert all(x.is_folder is False for x in streams)

    assert len(navigation) == 1
    assert navigation[0].offset > 0
    assert navigation[0].is_next_page


def test_playlist_many_seasons():
    # This series has multiple seasons. Should list only the seasons.
    playlist = areena.playlist('1-50688600')
    streams = [x for x in playlist if isinstance(x, areena.StreamLink)]
    navigation = [x for x in playlist if isinstance(x, areena.SeriesNavigationLink)]

    assert len(streams) == 0
    assert len(navigation) >= 2
    assert navigation[0].season_number == 1
    assert navigation[1].season_number == 2
    assert not any(x.is_next_page for x in navigation)


def test_playlist_many_seasons_reversed():
    playlist = areena.playlist('1-50640657')
    navigation = [x for x in playlist if isinstance(x, areena.SeriesNavigationLink)]

    # The order of seasons on this page is season from highest to lowest
    assert len(navigation) == 3
    assert navigation[0].season_number == 3
    assert navigation[1].season_number == 2
    assert navigation[2].season_number == 1


def test_navigate_into_a_seasons():
    # This series has multiple seasons
    playlist = areena.playlist('1-4446513')
    seasons = [x for x in playlist if isinstance(x, areena.SeriesNavigationLink)]
    assert len(seasons) >= 3

    # Select the season 2 and list the episodes
    episodes = areena.season_playlist(seasons[1].season_playlist_url)
    streams = [x for x in episodes if isinstance(x, areena.StreamLink)]

    assert len(streams) > 0
    assert all(x.homepage for x in streams)
    assert all(x.title not in [None, '', '???'] for x in streams)
    assert all(x.duration_seconds is not None for x in streams)
    assert all(x.published is not None for x in streams)
    assert all(x.thumbnail is not None for x in streams)
    assert all(x.is_folder is False for x in streams)


def test_playlist_pagination():
    playlist = areena.playlist('1-4446513')
    seasons = [x for x in playlist if isinstance(x, areena.SeriesNavigationLink)]
    assert len(seasons) >= 3

    season_url = seasons[2].season_playlist_url
    episodes = areena.season_playlist(season_url, offset=5, page_size=5)
    navigation = [x for x in episodes if isinstance(x, areena.SeriesNavigationLink)]
    streams = [x for x in episodes if isinstance(x, areena.StreamLink)]

    assert len(streams) > 0
    assert len(navigation) == 1
    assert navigation[0].offset == 10


def test_list_live_broadcasts():
    playlist = areena.get_live_broadcasts()

    # This will fail if there is ever a day when the Yle Areena "channel"
    # does not have any live broadcasts
    assert len(playlist) > 0
