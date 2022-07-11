import sys
import xbmcaddon
import xbmcgui
import xbmcplugin
from datetime import datetime
from typing import Any, Optional, Sequence, Tuple
from urllib.parse import urlencode, parse_qsl
from resources.lib import areena
from resources.lib import logger
from resources.lib.extractor import extract_media_url
from resources.lib.searchhistory import get_search_history
from resources.lib.kodi import play_media, show_notification, icon_path

_url = sys.argv[0]
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()
localized = _addon.getLocalizedString


def show_menu() -> None:
    listing = [
        list_item_video(
            'Yle TV1',
            areena.live_tv_manifest_url('622365', 'yletv1fin'),
            thumbnail=icon_path('tv1.png'),
            is_live=True
        ),
        list_item_video(
            'Yle TV2',
            areena.live_tv_manifest_url('622366', 'yletv2fin'),
            thumbnail=icon_path('tv2.png'),
            is_live=True
        ),
        list_item_video(
            'Yle Teema & Fem',
            areena.live_tv_manifest_url('622367', 'yletvteemafemfin'),
            thumbnail=icon_path('teemafem.png'),
            is_live=True
        ),
        list_item_search_menu(),
    ]

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_handle)


def list_item_video(
    label: str,
    path: str,
    thumbnail: Optional[str] = None,
    fanart: Optional[str] = None,
    published: Optional[datetime] = None,
    description: Optional[str] = None,
    duration: Optional[int] = None,
    action: str = 'play',
    is_live: bool = False
) -> Tuple[str, Any, bool]:
    manifest_type = 'hls' if '.m3u8' in path else 'mpd'
    query = urlencode({'action': action, 'path': path, 'manifest_type': manifest_type})
    item_url = f'{_url}?{query}'
    item = xbmcgui.ListItem(label, offscreen=True)

    item.setProperty('IsPlayable', 'true')
    if is_live:
        item.setProperty('IsLive', 'true')

    video_info = {'title': label}
    if published is not None:
        video_info['date'] = published.strftime('%d.%m.%Y')
        video_info['aired'] = published.strftime('%Y-%m-%d')
    if description is not None:
        video_info['plot'] = description
        video_info['plotoutline'] = description
    if duration is not None:
        video_info['duration'] = str(duration)
    item.setInfo('video', video_info)

    art = {}
    if thumbnail:
        art['thumb'] = thumbnail
    if fanart:
        art['fanart'] = fanart
    item.setArt(art)

    is_folder = False
    return (item_url, item, is_folder)


def list_item_series(
    label: str,
    series_id: str,
    thumbnail: Optional[str] = None,
) -> Tuple[str, Any, bool]:
    q = urlencode({
        'action': 'series',
        'series_id': series_id,
    })
    item_url = f'{_url}?{q}'
    item = xbmcgui.ListItem(label, offscreen=True)
    if thumbnail:
        item.setArt({'thumb': thumbnail})
    is_folder = True
    return (item_url, item, is_folder)


def list_item_series_next_page(
    label: str,
    season_playlist_url: str,
    offset: int,
    page_size: int,
    bottom: bool
):
    q = urlencode({
        'action': 'season',
        'season_playlist_url': season_playlist_url,
        'offset': offset,
        'page_size': page_size,
    })
    item_url = f'{_url}?{q}'
    item = xbmcgui.ListItem(label, offscreen=True)
    if bottom:
        item.setProperty('SpecialSort', 'bottom')
    is_folder = True
    return (item_url, item, is_folder)


def list_item_search_menu() -> Tuple[str, Any, bool]:
    item_url = f'{_url}?action=search_menu'
    item = xbmcgui.ListItem(localized(30000), offscreen=True)
    item.setArt({'thumb': icon_path('search.png')})
    is_folder = True
    return (item_url, item, is_folder)


def list_item_search_pagination(
    label: str,
    keyword: str,
    offset: int,
    page_size: int,
    update_search_history: bool = False,
    special_sort: Optional[str] = None
) -> Tuple[str, Any, bool]:
    qparams = {
        'action': 'search_page',
        'keyword': keyword,
        'offset': offset,
        'page_size': page_size
    }
    if update_search_history:
        qparams['update_search_history'] = 'true'

    query = urlencode(qparams)
    item_url = f'{_url}?{query}'
    item = xbmcgui.ListItem(label, offscreen=True)
    if special_sort:
        item.setProperty('SpecialSort', special_sort)
    is_folder = True
    return (item_url, item, is_folder)


def list_item_new_search() -> Tuple[str, Any, bool]:
    item_url = f'{_url}?action=search_input'
    item = xbmcgui.ListItem('[B]' + localized(30001) + '[/B]', offscreen=True)
    item.setArt({'thumb': icon_path('search.png')})
    is_folder = True
    return (item_url, item, is_folder)


def do_search_query() -> None:
    dialog = xbmcgui.Dialog()
    keyword = dialog.input(localized(30000), '', type=xbmcgui.INPUT_ALPHANUM)

    if keyword:
        history = get_search_history(_addon)
        history.update(keyword)

        show_search_result_page(keyword)


def show_search_result_page(
    keyword: str,
    offset: int = 0,
    page_size: int = areena.DEFAULT_PAGE_SIZE
) -> None:
    logger.info(f'Executing search: "{keyword}", offset = {offset}, page_size = {page_size}')

    searchresults = areena.search(keyword, offset, page_size)
    show_links(searchresults)

    if not searchresults:
        show_notification(localized(30004))


def show_search() -> None:
    listing = [
        list_item_new_search(),
    ]

    history = get_search_history(_addon)
    listing.extend(
        list_item_search_pagination(
            label,
            label,
            offset=0,
            page_size=areena.DEFAULT_PAGE_SIZE,
            update_search_history=True
        )
        for label in history.list()
    )

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_handle)


def show_series(series_id: str, offset: int, page_size: int) -> None:
    show_links(areena.playlist(series_id, offset, page_size))


def show_season(season_playlist_url: str, offset: int, page_size: int) -> None:
    show_links(areena.season_playlist(season_playlist_url, offset, page_size))


def show_links(links: Sequence[areena.AreenaLink]) -> None:
    listing = []
    for link in links:
        if isinstance(link, areena.StreamLink):
            if link.is_folder:
                series_id = link.homepage.rsplit('/', 1)[-1]
                item = list_item_series(
                    label=link.title,
                    series_id=series_id,
                    thumbnail=link.thumbnail,
                )
            else:
                item = list_item_video(
                    label=link.title,
                    path=link.homepage,
                    thumbnail=link.thumbnail,
                    fanart=link.fanart,
                    published=link.published,
                    description=link.description,
                    duration=link.duration_seconds,
                    action='play_areenaurl'
                )
        elif isinstance(link, areena.SearchNavigationLink):
            item = list_item_search_pagination(
                label=localized(30002),
                keyword=link.keyword,
                offset=link.offset,
                page_size=link.page_size,
                special_sort='bottom'
            )
        elif isinstance(link, areena.SeriesNavigationLink):
            if link.is_next_page:
                label = localized(30002)
                bottom = True
            else:
                label = f'{localized(30005)} {link.season_number}'
                bottom = False

            item = list_item_series_next_page(
                label=label,
                season_playlist_url=link.season_playlist_url,
                offset=link.offset,
                page_size=link.page_size,
                bottom=bottom
            )
        else:
            logger.warning(f'Unknown Areena link type: {type(link)}')
            continue

        listing.append(item)

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_DURATION)
    xbmcplugin.endOfDirectory(_handle)


def int_or_else(x: str, default: int) -> int:
    try:
        return int(x)
    except ValueError:
        return default


def router(paramstring: str) -> None:
    params = dict(parse_qsl(paramstring[1:]))
    if params:
        action = params.get('action')
        if action == 'play':
            play_media(_handle, params['path'], params['manifest_type'])
        elif action == 'play_areenaurl':
            media_url = extract_media_url(params['path'])
            if media_url is None:
                logger.error(f'Failed to extract media URL for {params["path"]}')
                show_notification(localized(30003), icon=xbmcgui.NOTIFICATION_ERROR)
                return

            logger.info(f'Playing URL: {media_url.url}')
            play_media(_handle, media_url.url, media_url.manifest_type, media_url.headers)
        elif action == 'series':
            offset = int_or_else(params.get('offset', ''), 0)
            page_size = int_or_else(params.get('page_size', ''), areena.DEFAULT_PAGE_SIZE)
            show_series(params['series_id'], offset, page_size)
        elif action == 'season':
            offset = int_or_else(params.get('offset', ''), 0)
            page_size = int_or_else(params.get('page_size', ''), areena.DEFAULT_PAGE_SIZE)
            show_season(params['season_playlist_url'], offset, page_size)
        elif action == 'search_menu':
            show_search()
        elif action == 'search_input':
            do_search_query()
        elif action == 'search_page':
            keyword = params.get('keyword', '')
            offset = int_or_else(params.get('offset', ''), 0)
            page_size = int_or_else(params.get('page_size', ''), areena.DEFAULT_PAGE_SIZE)

            if params.get('update_search_history') and keyword:
                # Move the selected keyword to the top of the search history
                history = get_search_history(_addon)
                history.update(keyword)

            show_search_result_page(keyword, offset, page_size)
        else:
            logger.error(f"Unknown action: {action or '(missing)'}")
    else:
        show_menu()


if __name__ == '__main__':
    router(sys.argv[2])
