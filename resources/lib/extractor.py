import re
import requests  # type: ignore
from . import logger, kaltura
from .kaltura import ManifestUrl
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urlparse


class AreenaPreviewApiResponse:
    def __init__(self, data: Dict[str, Any]) -> None:
        self.preview = data or {}

    def media_id(self) -> Optional[str]:
        if self.is_live():
            return self.ongoing().get('adobe', {}).get('yle_media_id')
        else:
            return self.ongoing().get('media_id')

    def manifest_url(self) -> Optional[ManifestUrl]:
        url = self.ongoing().get('manifest_url')
        if url is None:
            return None

        return ManifestUrl(url, 'hls', debug_source_name='preview manifest URL')

    def media_url(self) -> Optional[ManifestUrl]:
        url = self.ongoing().get('media_url')
        if url is None:
            return None

        return ManifestUrl(url, 'hls', debug_source_name='preview media URL')

    def media_type(self) -> Optional[Literal['audio', 'video']]:
        if not self.preview:
            return None
        elif self.ongoing().get('content_type') == 'AudioObject':
            return 'audio'
        else:
            return 'video'

    def is_live(self) -> bool:
        data = self.preview.get('data', {})
        return data.get('ongoing_channel') is not None

    def is_pending(self) -> bool:
        data = self.preview.get('data', {})
        pending = data.get('pending_event') or data.get('pending_ondemand')
        return pending is not None

    def is_expired(self) -> bool:
        data = self.preview.get('data', {})
        return data.get('gone') is not None

    def ongoing(self) -> Dict[str, Any]:
        data = self.preview.get('data', {})
        return (data.get('ongoing_ondemand') or
                data.get('ongoing_event') or
                data.get('ongoing_channel') or
                data.get('pending_event') or
                {})


def extract_media_url(areena_page_url: str) -> Optional[ManifestUrl]:
    """Resolve playable video stream URL for a given Areena page URL.

    Expected format of areena_page_url: yleareena://items/1-2250636"""
    logger.debug(f'Extracting stream URL from {areena_page_url}')
    pid = program_id_from_url(areena_page_url)
    return media_url_for_pid(pid)


def media_url_for_pid(pid: str) -> Optional[ManifestUrl]:
    preview = preview_parser(pid)

    if preview.is_expired():
        logger.warning(f'Stream {pid} has expired')

    if preview.is_pending():
        logger.warning(f'Stream {pid} not yet been published')

    media_id = preview.media_id()
    if media_id is not None:
        manifest_url = kaltura.manifest_url(media_id)
    else:
        manifest_url = None

    manifest_url = manifest_url or preview.manifest_url() or preview.media_url()
    if manifest_url is None:
        return None

    logger.info(
        f'Manifest URL {manifest_url.manifest_type} '
        f'from {manifest_url.debug_source_name}'
    )

    return manifest_url


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

    return AreenaPreviewApiResponse(preview_json)


def preview_url(pid: str) -> str:
    return f'https://player.api.yle.fi/v1/preview/{pid}.json?' \
        'language=fin&ssl=true&countryCode=FI&host=areenaylefi' \
        '&app_id=player_static_prod' \
        '&app_key=8930d72170e48303cf5f3867780d549b'


def parse_finnish_date(date_string: str) -> Optional[datetime]:
    """Parse a date string "14.05.2021" as a datetime object.

    Returns None if date_string is not formatted like a date or parsing fails.
    """
    m = re.match(r'^(\d{2})\.(\d{2})\.(\d{4})$', date_string)
    if m is None:
        return None

    try:
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def duration_from_search_result(search_result: Dict) -> Optional[int]:
    """Extract duration in seconds from a Areena search API result item."""
    labels = search_result.get('labels', [])
    duration_labels = [x.get('raw') for x in labels if x.get('type') == 'duration']
    if duration_labels:
        return iso_duration_as_seconds(duration_labels[0])
    else:
        return None


def iso_duration_as_seconds(duration_str: str) -> Optional[int]:
    """Convert an ISO 8601 duration string to integer seconds.

    Supports only hours, minutes and seconds.

    Examples of ISO durations: "PT1832S", "PT1H28M14S", "PT23M49.600S"
    """
    r = r'PT(?:(?P<hours>\d+)H)?(?:(?P<mins>\d+)M)?(?:(?P<secs>\d+)(?:\.\d+)?S)?$'
    m = re.match(r, duration_str)
    if m:
        hours = m.group('hours') or 0
        mins = m.group('mins') or 0
        secs = m.group('secs') or 0
        return 3600 * int(hours) + 60 * int(mins) + int(secs)
    else:
        return None


def label_by_type(labels: dict, type_name: str, key_name: str) -> List[str]:
    """Return a key value of an Areena API label object which as the given type."""
    matches = [x for x in labels if x.get('type') == type_name]
    return [x[key_name] for x in matches if key_name in x]
