import requests
from . import extractor, logger
from typing import Dict, List, Optional, Union
from urllib.parse import urlencode

DEFAULT_PAGE_SIZE = 30


class StreamLink():
    def __init__(
        self,
        homepage: str,
        title: Optional[str],
        thumbnail_url: Optional[str],
        is_folder: bool = False
    ):
        self.homepage = homepage
        self.title = title or '???'
        self.thumbnail_url = thumbnail_url
        self.is_folder = is_folder


class SearchNavigationLink():
    def __init__(
        self,
        keyword: str,
        offset: int,
        page_size: int
    ):
        self.keyword = keyword
        self.offset = offset
        self.page_size = page_size


def playlist(series_id: str, page_size: int = 20, offset: int = 0) -> List[StreamLink]:
    playlist_data = _load_playlist_page(series_id, page_size, offset)
    return _parse_playlist(playlist_data)


def search(
    keyword: str,
    offset: int = 0,
    page_size: int = DEFAULT_PAGE_SIZE
) -> List[Union[StreamLink, SearchNavigationLink]]:
    search_response = _get_search_results(keyword, offset, page_size)
    return _parse_search_results(search_response)


def _load_playlist_page(series_id: str, page_size: int, offset: int) -> List:
    r = requests.get(_playlist_url(series_id, page_size=page_size, offset=offset))
    r.raise_for_status()
    return r.json().get('data', [])


def _parse_playlist(playlist_data: List) -> List[StreamLink]:
    links = []
    for episode in playlist_data:
        if 'id' in episode:
            pid = episode['id']
            image_id = episode.get('image').get('id')

            links.append(StreamLink(
                homepage=f'yleareena://items/{pid}',
                title=extractor.get_text(episode.get('title', {})),
                thumbnail_url=_image_url_from_id(image_id)
            ))
    return links


def _get_search_results(keyword: str, offset: int, page_size: int) -> Dict:
    r = requests.get(_search_url(keyword, offset=offset, page_size=page_size))
    r.raise_for_status()
    return r.json()


def _parse_search_results(search_response: Dict) -> List[Union[StreamLink, SearchNavigationLink]]:
    results: List[Union[StreamLink, SearchNavigationLink]] = []
    for item in search_response.get('data', []):
        uri = item.get('pointer', {}).get('uri')
        pointer_type = item.get('pointer', {}).get('type')

        if item.get('type') == 'card' and uri:
            image_id = item.get('image', {}).get('id')
            if pointer_type in ['program', 'clip']:
                results.append(StreamLink(
                    homepage=uri,
                    title=item.get('title'),
                    thumbnail_url=_image_url_from_id(image_id),
                ))
            elif pointer_type == 'series':
                results.append(StreamLink(
                    homepage=uri,
                    title=item.get('title'),
                    thumbnail_url=_image_url_from_id(image_id),
                    is_folder=True
                ))
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
    
    if offset + limit < count:
        next_offset = offset + limit
        results.append(SearchNavigationLink(keyword, next_offset, DEFAULT_PAGE_SIZE))

    return results


def _playlist_url(series_id: str, ascending: bool = True, page_size: int = 20, offset: int = 0) -> str:
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


def _image_url_from_id(image_id: str) -> str:
    return (
        f'https://images.cdn.yle.fi/image/upload/'
        f'ar_1.0,c_fill,d_yle-areena.jpg,dpr_auto,f_auto,'
        f'fl_lossy,q_auto:eco,w_65/v1644410176/{image_id}.jpg'
    )
