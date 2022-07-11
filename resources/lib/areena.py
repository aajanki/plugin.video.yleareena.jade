import requests  # type: ignore
from . import logger
from .playlist import download_playlist, parse_playlist_seasons
from .extractor import duration_from_search_result, parse_finnish_date
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlencode

DEFAULT_PAGE_SIZE = 30


class AreenaLink():
    pass


class StreamLink(AreenaLink):
    def __init__(
        self,
        homepage: str,
        title: Optional[str],
        description: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        published: Optional[datetime] = None,
        image_id: Optional[str] = None,
        image_version: Optional[str] = None,
        is_folder: bool = False
    ):
        self.homepage = homepage
        self.title = title or '???'
        self.description = description
        self.duration_seconds = duration_seconds
        self.published = published
        self.thumbnail: Optional[str] = None
        self.fanart: Optional[str] = None
        if image_id is not None:
            self.thumbnail = _thumbnail_url(image_id, image_version)
            self.fanart = _fanart_url(image_id, image_version)
        self.is_folder = is_folder


class SearchNavigationLink(AreenaLink):
    def __init__(
        self,
        keyword: str,
        offset: int,
        page_size: int
    ):
        self.keyword = keyword
        self.offset = offset
        self.page_size = page_size


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


def _parse_search_results(search_response: Dict) -> List[AreenaLink]:
    results: List[AreenaLink] = []
    for item in search_response.get('data', []):
        uri = item.get('pointer', {}).get('uri')
        pointer_type = item.get('pointer', {}).get('type')

        if item.get('type') == 'card' and uri:
            if pointer_type in ['program', 'clip']:
                title = item.get('title')
                image_data = item.get('image', {})
                duration = duration_from_search_result(item)

                # The description field is empty, contains the publish date or
                # the series name. Try to first parse as date. If parsing fails,
                # assume that it's the series name.
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
                    image_id=image_data.get('id'),
                    image_version=image_data.get('version')
                ))
            elif pointer_type == 'series':
                results.append(StreamLink(
                    homepage=uri,
                    title=item.get('title'),
                    is_folder=True
                ))
            elif pointer_type == 'package':
                logger.debug('Ignoring a search result of type "package"')
            else:
                logger.warning(f'Unknown pointer type: {pointer_type}')

    # pagination links
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
        'app_id': 'areena_web_personal_prod',
        'app_key': '6c64d890124735033c50099ca25dd2fe',
        'client': 'yle-areena-web',
        'language': 'fi',
        'v': 9,
        'episodes': 'true',
        'packages': 'true',
        'query': keyword,
        'service': 'tv',
        'offset': offset,
        'limit': page_size,
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
