import json
import re
import requests  # type: ignore
from . import logger
from datetime import datetime
from typing import Any, Dict, Literal, Optional
from urllib.parse import urlparse


class AreenaPreviewApiResponse():
    def __init__(self, data: Dict[str, Any]) -> None:
        self.preview = data or {}

    def manifest_url(self) -> Optional[str]:
        return self.ongoing().get('manifest_url')

    def media_url(self) -> Optional[str]:
        return self.ongoing().get('media_url')

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
                data.get('ongoing_event', {}) or
                data.get('ongoing_channel', {}) or
                data.get('pending_event') or
                {})


def extract_media_url(areena_page_url: str) -> Optional[str]:
    """Resolve playable video stream URL for a given Areena page URL.

    Expected format of areena_page_url: yleareena://items/1-2250636"""
    logger.debug(f'Extracting stream URL from {areena_page_url}')
    pid = program_id_from_url(areena_page_url)
    return media_url_for_pid(pid)


def get_text(text_object: Dict[str, str], prefer_language: str = 'fi') -> Optional[str]:
    """Extract translated message from Areena API localized text object.

    Example text_object: {"fi": "teksti suomeksi", "sv": "samma på svenska"}

    Return text in prefer_language if available. Otherwise, return an arbitrary
    language. If text_object is empty, return None.
    """
    if prefer_language in text_object:
        return text_object[prefer_language]
    elif text_object:
        return list(text_object.values())[0]
    else:
        return None


def media_url_for_pid(pid: str) -> Optional[str]:
    preview = preview_parser(pid)

    if preview.is_expired():
        logger.warning(f'Stream {pid} has expired')

    if preview.is_pending():
        logger.warning(f'Stream {pid} not yet been published')

    return preview.manifest_url() or preview.media_url()


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


def parse_publication_event_date(episode_metadata: Dict) -> Optional[datetime]:
    """Parse the publication event from episode metadata.

    episode_metadata is an item from Areena API playlist response.

    Returns the timestamp of the earliest publication of the episode.
    Returns None if parsing fails for any reason.
    """
    events = episode_metadata.get('publicationEvent', [])

    # Prefer "current" events
    current_events = [e for e in events if e.get('temporalStatus') == 'currently']
    selected_events = current_events or events

    start_times = [e.get('startTime') for e in selected_events if e.get('startTime')]
    if start_times:
        first = min(start_times)
        return _parse_areena_timestamp(first)
    else:
        return None


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


def _parse_areena_timestamp(timestamp: str) -> Optional[datetime]:
    # Python prior to 3.7 doesn't support a colon in the timezone
    if re.search(r'\d\d:\d\d$', timestamp):
        timestamp = timestamp[:-3] + timestamp[-2:]

    return _strptime_or_none(timestamp, '%Y-%m-%dT%H:%M:%S%z')


def _strptime_or_none(timestamp: str, fmt: str) -> Optional[datetime]:
    try:
        return datetime.strptime(timestamp, fmt)
    except ValueError:
        return None


def duration_from_search_result(search_result: Dict) -> Optional[int]:
    """Extract duration in seconds from a Areena search API result item."""
    labels = search_result.get('labels', [])
    duration_labels = [x.get('raw') for x in labels if x.get('type') == 'duration']
    if duration_labels:
        return pt_duration_as_seconds(duration_labels[0])
    else:
        return None


def pt_duration_as_seconds(pt_duration: str) -> Optional[int]:
    """Convert PT duration string to integer seconds.

    Examples of PT durations: "PT1832S", "PT1H28M14S", "PT23M49.600S"
    """
    r = r'PT(?:(?P<hours>\d+)H)?(?:(?P<mins>\d+)M)?(?:(?P<secs>\d+)(?:\.\d+)?S)?$'
    m = re.match(r, pt_duration)
    if m:
        hours = m.group('hours') or 0
        mins = m.group('mins') or 0
        secs = m.group('secs') or 0
        return 3600 * int(hours) + 60 * int(mins) + int(secs)
    else:
        return None
