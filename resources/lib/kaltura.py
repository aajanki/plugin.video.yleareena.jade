import json
import requests  # type: ignore
from . import logger
from typing import Optional

_client_tag = 'html5:v1.7.1'
_partner_id = '1955031'
_widget_id = '_1955031'


class ManifestUrl():
    def __init__(
        self,
        url: str,
        manifest_type: str,
        *,
        headers: Optional[dict] = None,
        source_name: Optional[str] = None
    ):
        self.url = url
        self.manifest_type = manifest_type
        self.headers = headers
        self.debug_source_name = source_name


def manifest_url(media_id: str) -> Optional[ManifestUrl]:
    """Get a stream manifest URL from the Kaltura API"""
    referrer = 'https://areena.yle.fi/'
    entry_id = _kaltura_entry_id_from_media_id(media_id)
    context = _playback_context(entry_id, referrer)
    if context is None:
        return None

    headers = {'Referer': referrer}

    # Prefer MPEG-DASH, fallback to HLS if DASH is not available
    url = _manifest_from_context(context, 'mpegdash', referrer)
    if url is not None:
        return ManifestUrl(url, 'mpd', headers=headers, source_name='Kaltura')

    url = _manifest_from_context(context, 'applehttp', referrer)
    if url is not None:
        return ManifestUrl(url, 'hls', headers=headers, source_name='Kaltura')

    return None


def _kaltura_entry_id_from_media_id(media_id: str) -> str:
    return media_id.split('-', 1)[-1]


def _playback_context(entry_id, referrer):
    subrequests = [
        _start_widget_session_action(_widget_id),
        _get_playback_context_action(entry_id, '{1:result:ks}')
    ]
    mreq = _multi_request(subrequests, _client_tag, _partner_id)

    logger.debug(f'Sending Kaltura API flavors request:\n{json.dumps(mreq, indent=2)}')

    response = _perform_request(mreq, referrer, 'https://areena.yle.fi')

    logger.debug(f'Kaltura API response:\n{json.dumps(response, indent=2)}')

    return next((x for x in response if x.get('objectType') == 'KalturaPlaybackContext'), None)


def _manifest_from_context(playback_context, source_format, referrer):
    # Select the first source with the matching format. The different sources
    # have different delivery profiles. The first one seems to always include
    # the 1080p stream.
    sources = playback_context.get('sources', [])
    fmt_sources = (s for s in sources if s.get('format') == source_format)
    selected_source = next(fmt_sources, None)

    if selected_source:
        return selected_source.get('url')
    else:
        return None


def _multi_request(subrequests, client_tag, partner_id):
    mrequest = {
        'apiVersion': '3.3.0',
        'format': 1,
        'ks': '',
        'clientTag': client_tag,
        'partnerId': partner_id
    }
    mrequest.update({str(i+1): req for i, req in enumerate(subrequests)})
    return mrequest


def _start_widget_session_action(widget_id):
    return {
        'service': 'session',
        'action': 'startWidgetSession',
        'widgetId': widget_id
    }


def _get_playback_context_action(entry_id, ks):
    return {
        'service': 'baseEntry',
        'action': 'getPlaybackContext',
        'entryId': entry_id,
        'ks': ks,
        'contextDataParams': {
            'objectType': 'KalturaContextDataParams',
            'flavorTags': 'all'
        }
    }


def _perform_request(data, referrer, origin):
    extra_headers = {
        'Referer': referrer,
        'Origin': origin,
        'Cache-Control': 'max-age=0'
    }
    r = requests.post(_service_api_url('multirequest'), json=data, headers=extra_headers)
    return r.json()


def _service_api_url(service):
    return f'https://cdnapisec.kaltura.com/api_v3/service/{service}'
