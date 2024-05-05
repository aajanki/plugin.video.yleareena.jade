import html5lib
import json
import requests  # type: ignore
from . import logger
from .playlist import download_playlist, parse_playlist_seasons
from .extractor import duration_from_search_result, parse_finnish_date, \
    program_id_from_url, preview_parser
from dataclasses import dataclass, InitVar
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlencode, urljoin

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


def _parse_search_results(search_response: Dict) -> List[AreenaLink]:
    results: List[AreenaLink] = []
    for item in search_response.get('data', []):
        uri = item.get('pointer', {}).get('uri')
        pointer_type = item.get('pointer', {}).get('type')

        if item.get('type') == 'card' and uri:
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
    url = 'https://areena.yle.fi/tv/suorat'
    r = requests.get(url)
    r.raise_for_status()

    html_tree = html5lib.parse(r.text, namespaceHTMLElements=False)
    return _parse_areena_live_programs(url, html_tree)


def _parse_areena_live_programs(baseurl, html_tree):
    containers = _find_live_containers(html_tree)
    if not containers:
        logger.warning(f'Failed to find the live broadcast container at {baseurl}')
        return []

    live_data = []
    for container in containers:
        cards = container.findall('section/ul/li/ul/li')
        if cards is not None:
            live_cards = [x for x in cards if _is_live_card(x)]
            for card in live_cards:
                link = card.find('a')
                if link is not None and link.get('href') is not None:
                    broadcast_time = link.findtext(
                        'div[@class="schedule-card-small__header"]'
                        '/div[@class="schedule-card-small__broadcast-info"]'
                        '/span[@class="schedule-card-small__publication"]')
                    broadcast_time = broadcast_time or '00:00'
                    title = link.findtext(
                        'div[@class="schedule-card-small__header"]'
                        '/span[@class="schedule-card-small__title"]'
                        '/span[@itemprop="name"]')
                    title = title or 'Live'
                    homepage = urljoin(baseurl, link.get('href'))
                    pid = program_id_from_url(homepage)
                    preview = preview_parser(pid)

                    stream = StreamLink(
                        homepage=homepage,
                        title=f'{broadcast_time} {title}',
                        description=preview.description(),
                        image_id=preview.image().get('id'),
                        image_version=preview.image().get('version'),
                    )
                    live_data.append((broadcast_time, stream))

    live_data = sorted(live_data, key=lambda x: x[0])

    return [x[1] for x in live_data]


def _find_live_containers(html_tree):
    live_containers = []
    containers = html_tree.findall('.//div[@class="view-lists"]/div[@class="card-list-container"]')
    for container in containers:
        if _is_areena_live_container(container):
            live_containers.append(container)

    return live_containers


def _is_areena_live_container(html_element):
    dataliststr = html_element.get('data-list')
    if not dataliststr:
        return False

    try:
        datalist = json.loads(dataliststr)
    except json.JSONDecodeError:
        datalist = {}

    title = datalist.get('title')
    return title not in ['Yle TV1', 'Yle TV2', 'Yle Teema Fem']


def _is_live_card(html_element):
    is_tv_episode = html_element.get('itemtype') == 'http://schema.org/TVEpisode'
    html_class = html_element.get('class') or ''
    is_non_empty = (
        'expired' in html_class or
        'current' in html_class or
        'upcoming' in html_class
    )

    return is_tv_episode and is_non_empty
