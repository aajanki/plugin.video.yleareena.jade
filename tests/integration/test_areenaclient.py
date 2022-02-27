from resource.lib import areenaclient


def test_search():
    res = areenaclient.search('Pasila')

    assert len(res) > 0
    assert all(x.get('homepage') for x in res)
    assert all(x.get('title') not in [None, '', '???'] for x in res)
    assert all(x.get('thumbnail_image_url') for x in res)

