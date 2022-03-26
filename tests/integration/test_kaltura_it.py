from resources.lib import kaltura


def test_kaltura_manifest_url():
    media_id = '29-1_fypgqef8'  # Pasila episode 4
    manifest_url = kaltura.manifest_url(media_id)

    assert manifest_url is not None
    assert manifest_url.manifest_type == 'mpd'
    assert '/manifest.mpd' in manifest_url.url
