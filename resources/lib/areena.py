import requests  # type: ignore
from . import logger
from .playlist import download_playlist, parse_playlist_seasons
from .extractor import duration_from_search_result, parse_finnish_date
from dataclasses import dataclass, InitVar
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlencode

DEFAULT_PAGE_SIZE = 30


class AreenaLink:
    pass


@dataclass
class StreamLink(AreenaLink):
    homepage: str
    title: str
    description: Optional[str] = None
    duration_seconds: Optional[int] = None
    published: Optional[datetime] = None
    image_id: InitVar[Optional[str]] = None
    image_version: InitVar[Optional[str]] = None
    is_folder: bool = False
    thumbnail: Optional[str] = None
    fanart: Optional[str] = None

    def __post_init__(self, image_id, image_version):
        if not self.title:
            self.title = '???'

        if image_id is not None:
            if self.thumbnail is None:
                self.thumbnail = _thumbnail_url(image_id, image_version)


@dataclass(frozen=True)
class SearchNavigationLink(AreenaLink):
    keyword: str
    offset: int
    page_size: int


@dataclass(frozen=True)
class SeriesNavigationLink(AreenaLink):
    season_playlist_url: str
    season_number: int
    offset: int
    page_size: int
    is_next_page: bool


def live_tv_manifest_url(stream_id, stream_name):
    return f'https://yletv.akamaized.net/hls/live/{stream_id}/{stream_name}/index.m3u8'


def playlist(
    series_id: str,
    offset: int = 0,
    page_size: int = DEFAULT_PAGE_SIZE
) -> List[AreenaLink]:
    seasons = parse_playlist_seasons(series_id)
    if seasons is None:
        logger.warning('Failed to parse the playlist')
        return []

    season_urls = seasons.season_playlist_urls()

    if len(season_urls) == 1:
        return season_playlist(season_urls[0][1], offset, page_size)
    else:
        return [
            SeriesNavigationLink(url, i, 0, DEFAULT_PAGE_SIZE, False)
            for i, url in season_urls
        ]


def season_playlist(
    season_url: str,
    offset: int = 0,
    page_size: int = DEFAULT_PAGE_SIZE
) -> List[AreenaLink]:
    playlist, meta = download_playlist(season_url, offset, page_size)

    links: List[AreenaLink] = [
        StreamLink(
            homepage=ep.homepage,
            title=ep.title,
            description=ep.description,
            duration_seconds=ep.duration_seconds,
            published=ep.published,
            image_id=ep.image_id,
            image_version=ep.image_version
        )
        for ep in playlist
    ]

    # Pagination links
    limit = meta.get('limit', DEFAULT_PAGE_SIZE)
    offset = meta.get('offset', 0)
    count = meta.get('count', 0)

    next_offset = offset + limit
    if next_offset < count:
        links.append(SeriesNavigationLink(season_url, 0, next_offset, limit, True))

    return links


def search(
    keyword: str,
    offset: int = 0,
    page_size: int = DEFAULT_PAGE_SIZE
) -> List[AreenaLink]:
    search_response = _get_search_results(keyword, offset, page_size)
    return _parse_search_results(search_response)


def _get_search_results(keyword: str, offset: int, page_size: int) -> Dict:
    r = requests.get(_search_url(keyword, offset=offset, page_size=page_size))
    r.raise_for_status()
    return r.json()


def _parse_search_results(search_response: Dict, pagination_links: bool = True) -> List[AreenaLink]:
    results: List[AreenaLink] = []
    for item in search_response.get('data', []):
        uri = item.get('pointer', {}).get('uri')
        pointer_type = item.get('pointer', {}).get('type')
        transmissions = item.get('transmissions', [])
        is_upcoming = transmissions and all(
            x.get('broadcastStatus') == 'upcoming'
            for x in transmissions
        )

        if item.get('type') == 'card' and uri and not is_upcoming:
            if pointer_type in ['program', 'clip']:
                title = item.get('title', {})
                image_data = item.get('image', {})
                duration = duration_from_search_result(item)

                # If the description field is not empty, it contains either the
                # publication date or the series name. Try to first parse as
                # date. If parsing fails, assume that it's the series name.
                published = None
                description = item.get('description')
                if description:
                    published = parse_finnish_date(description)
                    if published is None and len(description) < 100:
                        title = f'{description}: {title}'

                results.append(StreamLink(
                    homepage=uri,
                    title=title,
                    duration_seconds=duration,
                    published=published,
                    description=title,
                    image_id=image_data.get('id'),
                    image_version=image_data.get('version')
                ))
            elif pointer_type == 'series':
                title = item.get('title', {})
                image_data = item.get('image', {})
                results.append(StreamLink(
                    homepage=uri,
                    title=title,
                    description=title,
                    image_id=image_data.get('id'),
                    image_version=image_data.get('version'),
                    is_folder=True
                ))
            elif pointer_type == 'package':
                logger.debug('Ignoring a search result of type "package"')
            else:
                logger.warning(f'Unknown pointer type: {pointer_type}')

    # pagination links
    if pagination_links:
        meta = search_response.get('meta', {})
        keyword = (
            meta
            .get('analytics', {})
            .get('onReceive', {})
            .get('comscore', {})
            .get('yle_search_phrase', '')
        )
        offset = meta.get('offset', 0)
        limit = meta.get('limit', DEFAULT_PAGE_SIZE)
        count = meta.get('count', 0)

        next_offset = offset + limit
        if next_offset < count:
            results.append(SearchNavigationLink(keyword, next_offset, limit))

    return results


def _search_url(keyword: str, offset: int, page_size: int) -> str:
    q = urlencode({
        'app_id': 'areena-web-items',
        'app_key': 'wlTs5D9OjIdeS9krPzRQR4I1PYVzoazN',
        'client': 'yle-areena-web',
        'language': 'fi',
        'v': 10,
        'episodes': 'true',
        'packages': 'true',
        'query': keyword,
        'service': 'tv',
        'offset': offset,
        'limit': page_size,
        'country': 'FI',
        'isPortabilityRegion': 'true',
    })
    return f'https://areena.api.yle.fi/v1/ui/search?{q}'


def _thumbnail_url(image_id: str, version: Optional[str] = None) -> str:
    version = version or '1624522786'
    return (
        f'https://images.cdn.yle.fi/image/upload/w_320,dpr_1.0,fl_lossy,f_auto,'
        f'q_auto,d_yle-elava-arkisto.jpg/v{version}/{image_id}.jpg'
    )


def _fanart_url(image_id: str, version: Optional[str] = None) -> str:
    version = version or '1624522786'
    return (
        f'https://images.cdn.yle.fi/image/upload/w_auto,dpr_auto,fl_lossy,f_auto,'
        f'q_auto,d_yle-elava-arkisto.jpg/v{version}/{image_id}.jpg'
    )


def get_live_broadcasts():
    r = requests.get(_live_broadcast_url(0, 10))
    r.raise_for_status()

    return _parse_search_results(r.json(), False)


def _live_broadcast_url(offset: int, page_size: int) -> str:
    # Extracted from https://areena.yle.fi/suorat
    q = urlencode({
        'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzb3VyY2UiOiJodHRwczovL3Byb2dyYW1zLmFwaS55bGUuZmkvdjMvc2NoZW1hL3YzL3NjaGVkdWxlcy9ub3c_Y2xhc3NpZmljYXRpb249MzEtMS0zITMxLTItMy42JmxpdmU9dHJ1ZSZwdWJsaWNhdGlvbl90eXBlPWJyb2FkY2FzdCx3ZWJjYXN0JnNlcnZpY2U9eWxlLXR2MSx5bGUtdHYyLHlsZS10ZWVtYS1mZW0seWxlLWFyZWVuYSIsImNhcmRPcHRpb25zVGVtcGxhdGUiOiJ1cGNvbWluZyIsImFuYWx5dGljcyI6eyJjb250ZXh0Ijp7ImNvbXNjb3JlIjp7InlsZV9yZWZlcmVyIjoiY29tbW9uLmxpdmUubm9faWQuc3VvcmF0LnVudGl0bGVkLnVyaGVpbHUifX19fQ.dMfaRQv7n1-2VJI5PPMsSc7yNTwTLbp1-usPXv5FIUI',  # noqa: E501
        'language': 'fi',
        'v': '10',
        'client': 'yle-areena-web',
        'offset': str(offset),
        'limit': str(page_size),
        'country': 'FI',
        'isPortabilityRegion': 'true',
        'app_id': 'areena-web-items',
        'app_key': 'wlTs5D9OjIdeS9krPzRQR4I1PYVzoazN'
    })
    return f'https://areena.api.yle.fi/v1/ui/content/list?{q}'
