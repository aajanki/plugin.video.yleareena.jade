import sys
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
from datetime import datetime
from typing import Any, Optional, Sequence, Tuple
from urllib.parse import urlencode, parse_qsl
from resources.lib import areenaclient
from resources.lib import logger
from resources.lib.extractor import extract_media_url
from resources.lib.searchhistory import get_search_history

_url = sys.argv[0]
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()
localized = _addon.getLocalizedString


def show_menu() -> None:
    yle_tv1_live_url = 'https://yletv.akamaized.net/hls/live/622365/yletv1fin/index.m3u8'
    yle_tv2_live_url = 'https://yletv.akamaized.net/hls/live/622366/yletv2fin/index.m3u8'
    yle_teema_fem_live_url = \
        'https://yletv.akamaized.net/hls/live/622367/yletvteemafemfin/index.m3u8'

    listing = [
        list_item_video('Yle TV1', yle_tv1_live_url,
                        icon=icon_path('tv1.png'), is_live=True),
        list_item_video('Yle TV2', yle_tv2_live_url,
                        icon=icon_path('tv2.png'), is_live=True),
        list_item_video('Yle Teema & Fem', yle_teema_fem_live_url,
                        icon=icon_path('teemafem.png'), is_live=True),
        list_item_search_menu(),
    ]

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_handle)


def list_item_video(
    label: str,
    path: str,
    icon: Optional[str] = None,
    thumbnail: Optional[str] = None,
    fanart: Optional[str] = None,
    published: Optional[datetime] = None,
    description: Optional[str] = None,
    duration: Optional[int] = None,
    action: str = 'play',
    is_live: bool = False
) -> Tuple[str, Any, bool]:
    query = urlencode({'action': action, 'path': path})
    item_url = f'{_url}?{query}'
    item = xbmcgui.ListItem(label, offscreen=True)

    item.setProperty('IsPlayable', 'true')
    if is_live:
        item.setProperty('IsLive', 'true')

    video_info = {'title': label}
    if published is not None:
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
    if icon:
        art['icon'] = icon
    if fanart:
        art['fanart'] = fanart
    item.setArt(art)

    is_folder = False
    return (item_url, item, is_folder)


def list_item_series(
    label: str,
    series_id: str,
    thumbnail: Optional[str] = None,
    offset: int = 0,
    page_size: int = areenaclient.DEFAULT_PAGE_SIZE
) -> Tuple[str, Any, bool]:
    q = urlencode({
        'action': 'series',
        'series_id': series_id,
        'offset': offset,
        'page_size': page_size
    })
    item_url = f'{_url}?{q}'
    item = xbmcgui.ListItem(label, offscreen=True)
    if thumbnail:
        item.setArt({'thumb': thumbnail})
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
    update_search_history: bool = False
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
    page_size: int = areenaclient.DEFAULT_PAGE_SIZE
) -> None:
    logger.info(f'Executing search: "{keyword}", offset = {offset}, page_size = {page_size}')

    searchresults = areenaclient.search(keyword, offset, page_size)
    show_links(searchresults)

    if not searchresults:
        show_notification(localized(30004))


def show_search() -> None:
    listing = [
        list_item_new_search(),
    ]

    history = get_search_history(_addon)
    listing.extend(
        list_item_search_pagination(x, x, offset=0,
                                    page_size=areenaclient.DEFAULT_PAGE_SIZE,
                                    update_search_history=True
                                    )
        for x in history.list()
    )

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_handle)


def show_series(series_id: str, offset: int, page_size: int) -> None:
    show_links(areenaclient.playlist(series_id, offset, page_size))


def show_links(links: Sequence[areenaclient.AreenaLink]) -> None:
    listing = []
    for link in links:
        if isinstance(link, areenaclient.StreamLink):
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
        elif isinstance(link, areenaclient.SearchNavigationLink):
            item = list_item_search_pagination(
                label=localized(30002),
                keyword=link.keyword,
                offset=link.offset,
                page_size=link.page_size
            )
        elif isinstance(link, areenaclient.SeriesNavigationLink):
            item = list_item_series(
                label=localized(30002),
                series_id=link.series_id,
                offset=link.offset,
                page_size=link.page_size
            )
        else:
            logger.warning(f'Unknown Areena link type: {type(link)}')
            continue

        listing.append(item)

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_handle)


def play_media(url: str) -> None:
    listitem = xbmcgui.ListItem(path=url)
    listitem.setProperty('inputstream', 'inputstream.adaptive')
    listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
    xbmcplugin.setResolvedUrl(_handle, True, listitem=listitem)


def show_notification(message: str, icon: str = xbmcgui.NOTIFICATION_INFO) -> None:
    xbmcgui.Dialog().notification('Yle Areena', message, icon)


def int_or_else(x: str, default: int) -> int:
    try:
        return int(x)
    except ValueError:
        return default


def icon_path(filename: str) -> str:
    return xbmcvfs.translatePath(
        _addon.getAddonInfo('path') + f'/resources/media/{filename}')


def router(paramstring: str) -> None:
    params = dict(parse_qsl(paramstring[1:]))
    if params:
        action = params.get('action')
        if action == 'play':
            play_media(params['path'])
        elif action == 'play_areenaurl':
            media_url = extract_media_url(params['path'])
            if media_url is None:
                logger.error(f'Failed to extract media URL for {params["path"]}')
                show_notification(localized(30003), icon=xbmcgui.NOTIFICATION_ERROR)
                return

            logger.info(f'Playing URL: {media_url}')
            play_media(media_url)
        elif action == 'series':
            offset = int_or_else(params.get('offset', ''), 0)
            page_size = int_or_else(params.get('page_size', ''), areenaclient.DEFAULT_PAGE_SIZE)
            show_series(params['series_id'], offset, page_size)
        elif action == 'search_menu':
            show_search()
        elif action == 'search_input':
            do_search_query()
        elif action == 'search_page':
            keyword = params.get('keyword', '')
            offset = int_or_else(params.get('offset', ''), 0)
            page_size = int_or_else(params.get('page_size', ''), areenaclient.DEFAULT_PAGE_SIZE)

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
