import html5lib
import json
import re
import requests  # type: ignore
from . import logger
from dataclasses import dataclass
from datetime import datetime
from typing import List, Mapping, Optional, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from .extractor import iso_duration_as_seconds, label_by_type


@dataclass(frozen=True)
class SeriesSeasons:
    base_url: str
    season_parameters: dict

    def season_playlist_urls(self):
        if self.season_parameters:
            season_urls = [
                update_url_query(self.base_url, q)
                for q in self.season_parameters
            ]
            return list(enumerate(season_urls, start=1))
        else:
            return [(1, self.base_url)]


@dataclass(frozen=True)
class EpisodeMetadata:
    homepage: str
    title: str
    description: Optional[str]
    duration_seconds: Optional[int]
    published: Optional[datetime]
    image_id: Optional[str]
    image_version: Optional[str]


def parse_playlist_seasons(series_id):
    r = requests.get(f'https://areena.yle.fi/{series_id}')
    r.raise_for_status()

    html_tree = html5lib.parse(r.text, namespaceHTMLElements=False)
    next_data = _parse_next_data(html_tree)
    tabs = next_data.get('props', {}).get('pageProps', {}).get('view', {}).get('tabs', [])
    episodes_tab = [tab for tab in tabs if tab.get('title') == 'Jaksot']
    if episodes_tab:
        episodes_content = episodes_tab[0].get('content', [])
        if episodes_content:
            playlist_data = episodes_content[0]
            uri = playlist_data.get('source', {}).get('uri')

            series_parameters = {}
            filters = playlist_data.get('filters', [])
            if filters:
                options = filters[0].get('options', [])
                series_parameters = [x['parameters'] for x in options]

            return SeriesSeasons(uri, series_parameters)

    return None


def download_playlist(
    season_url: str,
    offset: int,
    page_size: int
) -> Tuple[List[EpisodeMetadata], dict]:
    # Areena server fails (502 Bad gateway) if page_size is larger
    # than 100.
    assert 0 < page_size <= 100

    params = {
        'offset': str(offset),
        'limit': str(page_size),
        'app_id': 'areena-web-items',
        'app_key': 'v9No1mV0omg2BppmDkmDL6tGKw1pRFZt',
    }
    playlist_page_url = update_url_query(season_url, params)
    return _parse_series_episode_data(playlist_page_url)


def _parse_next_data(html_tree):
    next_data_text = html_tree.findtext('./body/script[@id="__NEXT_DATA__"]')
    if next_data_text:
        return json.loads(next_data_text)
    else:
        return None


def _parse_series_episode_data(playlist_page_url):
    logger.debug(f'Downloading playlist page {playlist_page_url}')
    r = requests.get(playlist_page_url)
    if r.status_code >= 400:
        logger.warning(
            f'Failed to download playlist page {playlist_page_url}. Some episodes may be missing!')
        return [], {}

    playlist = r.json()

    episodes = []
    for data in playlist.get('data', []):
        uri = data.get('pointer', {}).get('uri')

        labels = data.get('labels')

        duration = None
        duration_str = label_by_type(labels, 'progress', 'raw')
        if duration_str:
            duration = iso_duration_as_seconds(duration_str[0])

        release_date = None
        generics = label_by_type(labels, 'generic', 'formatted')
        for val in generics:
            m = re.match(r'[a-z]{2} (?P<day>\d{1,2})\.(?P<month>\d{1,2})\.(?P<year>\d{4})', val)
            if m:
                release_date = datetime(
                    int(m.group('year')),
                    int(m.group('month')),
                    int(m.group('day'))
                )
                break

        if uri:
            media_id = uri.rsplit('/')[-1]
            uri = f'https://areena.yle.fi/{media_id}'
            episodes.append(EpisodeMetadata(
                homepage=uri,
                title=data.get('title'),
                description=data.get('description'),
                duration_seconds=duration,
                published=release_date,
                image_id=data.get('image', {}).get('id'),
                image_version=data.get('image', {}).get('version')
            ))

    meta = playlist.get('meta')

    return episodes, meta


def update_url_query(url: str, new_query_parameters: Mapping[str, str]) -> str:
    """Add the key-value pairs in new_query_parameters in the input URL query.

    Overwrite existing query parameters with the same name.
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    params_one_value = {k: v[0] for k, v in params.items()}
    params_one_value.update(new_query_parameters)
    q = urlencode(params_one_value)
    parts = (parsed[0], parsed[1], parsed[2], '', q, '')
    return urlunparse(parts)
