import json
import requests
from . import logger
from typing import Dict
from urllib.parse import urlparse


class AreenaPreviewApiResponse():
    def __init__(self, data):
        self.preview = data or {}

    def manifest_url(self):
        return self.ongoing().get('manifest_url')

    def media_url(self):
        return self.ongoing().get('media_url')

    def media_type(self):
        if not self.preview:
            return None
        elif self.ongoing().get('content_type') == 'AudioObject':
            return 'audio'
        else:
            return 'video'

    def is_live(self):
        data = self.preview.get('data', {})
        return data.get('ongoing_channel') is not None

    def is_pending(self):
        data = self.preview.get('data', {})
        pending = data.get('pending_event') or data.get('pending_ondemand')
        return pending is not None

    def is_expired(self):
        data = self.preview.get('data', {})
        return data.get('gone') is not None

    def ongoing(self):
        data = self.preview.get('data', {})
        return (data.get('ongoing_ondemand') or
                data.get('ongoing_event', {}) or
                data.get('ongoing_channel', {}) or
                data.get('pending_event') or
                {})


def extract_media_url(url: str) -> str:
    metadata = extract(url)
    return metadata.get('url')


def extract(url: str) -> Dict:
    logger.info(f'Extracting stream URL from {url}')
    pid = program_id_from_url(url)
    logger.info(f'program ID = {pid}')
    metadata = metadata_for_pid(pid)
    if not metadata:
        return {}

    logger.info(f'preview response: {json.dumps(metadata)}')

    return metadata


def metadata_for_pid(pid: str) -> Dict:
    if not pid:
        return None

    preview = preview_parser(pid)

    if preview.is_expired():
        logger.warning(f'Stream {pid} has expired')

    if preview.is_pending():
        logger.warning(f'Stream {pid} not yet published')

    url = preview.manifest_url() or preview.media_url()

    return {'url': url}


def program_id_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.path.split('/')[-1]


def preview_parser(pid: str) -> AreenaPreviewApiResponse:
    preview_headers = {
        'Referer': 'https://areena.yle.fi/tv',
        'Origin': 'https://areena.yle.fi'
    }

    try:
        r = requests.get(preview_url(pid), headers=preview_headers)
        r.raise_for_status()
        preview_json = r.json()
    except requests.HTTPError as ex:
        if ex.response.status_code == 404:
            logger.warning(f'Preview API result not found in {preview_url(pid)}')
            preview_json = {}
        else:
            raise

    logger.debug('preview data:' + json.dumps(preview_json))

    return AreenaPreviewApiResponse(preview_json)


def preview_url(pid: str) -> str:
    return f'https://player.api.yle.fi/v1/preview/{pid}.json?' \
        'language=fin&ssl=true&countryCode=FI&host=areenaylefi' \
        '&app_id=player_static_prod' \
        '&app_key=8930d72170e48303cf5f3867780d549b'
