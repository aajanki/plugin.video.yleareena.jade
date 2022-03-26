import requests  # type: ignore
from . import logger
from .extractor import duration_from_search_result, get_text, \
    parse_finnish_date, parse_publication_event_date, pt_duration_as_seconds
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


class SeriesNavigationLink(AreenaLink):
    def __init__(
        self,
        series_id: str,
        offset: int,
        page_size: int
    ):
        self.series_id = series_id
        self.offset = offset
        self.page_size = page_size


def live_tv_manifest_url(stream_id, stream_name):
    return f'https://yletv.akamaized.net/hls/live/{stream_id}/{stream_name}/index.m3u8'


def playlist(
    series_id: str,
    offset: int = 0,
    page_size: int = DEFAULT_PAGE_SIZE
) -> List[AreenaLink]:
    playlist_data = _load_playlist_page(series_id, offset, page_size)
    return _parse_playlist(playlist_data, series_id)


def search(
    keyword: str,
    offset: int = 0,
    page_size: int = DEFAULT_PAGE_SIZE
) -> List[AreenaLink]:
    search_response = _get_search_results(keyword, offset, page_size)
    return _parse_search_results(search_response)


def _load_playlist_page(series_id: str, offset: int, page_size: int) -> Dict:
    r = requests.get(_playlist_url(series_id, ascending=True, offset=offset, page_size=page_size))
    r.raise_for_status()
    return r.json()


def _parse_playlist(playlist_data: Dict, series_id: str) -> List[AreenaLink]:
    links: List[AreenaLink] = []
    for episode in playlist_data.get('data', []):
        if 'id' in episode:
            pid = episode['id']
            image_data = episode.get('image', {})
            if 'duration' in episode:
                duration = pt_duration_as_seconds(episode['duration'])
            else:
                duration = None

            links.append(StreamLink(
                homepage=f'yleareena://items/{pid}',
                title=get_text(episode.get('title', {})),
                description=get_text(episode.get('description', {})),
                duration_seconds=duration,
                image_id=image_data.get('id'),
                image_version=image_data.get('version'),
                published=parse_publication_event_date(episode)
            ))

    # Pagination links
    meta = playlist_data.get('meta', {})
    limit = meta.get('limit', DEFAULT_PAGE_SIZE)
    offset = meta.get('offset', 0)
    count = meta.get('count', 0)

    next_offset = offset + limit
    if next_offset < count:
        links.append(SeriesNavigationLink(series_id, next_offset, limit))

    return links


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


def _playlist_url(series_id: str, ascending: bool, offset: int, page_size: int) -> str:
    sort_order = 'asc' if ascending else 'desc'
    query = {
        'type': 'program',
        'availability': '',
        'limit': str(page_size),
        'order': f'episode.hash:{sort_order},publication.starttime:{sort_order},title.fi:asc',
        'app_id': 'areena_web_frontend_prod',
        'app_key': '4622a8f8505bb056c956832a70c105d4',
    }
    if offset:
        query['offset'] = str(offset)
    q = urlencode(query)
    return f'https://areena.yle.fi/api/programs/v1/episodes/{series_id}.json?{q}'


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
