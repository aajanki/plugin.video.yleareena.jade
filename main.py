import sys
import xbmcaddon  # type: ignore
import xbmcgui  # type: ignore
import xbmcplugin  # type: ignore
from typing import Any, Optional, Sequence, Tuple, Union
from urllib.parse import urlencode, parse_qsl
from resource.lib import areenaclient
from resource.lib import logger
from resource.lib import extractor

_url = sys.argv[0]
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()
ls = _addon.getLocalizedString


def show_menu() -> None:
    yle_tv1_live_url = 'https://yletv.akamaized.net/hls/live/622365/yletv1fin/index.m3u8'
    yle_tv1_thumbnail_url = 'https://images.cdn.yle.fi/image/upload/c_fill,f_auto,h_64,q_auto:eco/v1643371700/yle-tv1_vt.png'
    yle_tv2_live_url = 'https://yletv.akamaized.net/hls/live/622366/yletv2fin/index.m3u8'
    yle_tv2_thumbnail_url = 'https://images.cdn.yle.fi/image/upload/c_fill,f_auto,h_64,q_auto:eco/v1643371700/yle-tv2_vt.png'
    yle_teema_fem_live_url = 'https://yletv.akamaized.net/hls/live/622367/yletvteemafemfin/index.m3u8'
    yle_teema_fem_thumbnail_url = 'https://images.cdn.yle.fi/image/upload/c_fill,f_auto,h_64,q_auto:eco/v1643371700/yle-teema-fem_vt.png'

    listing = [
        list_item_video('YLE TV1', yle_tv1_live_url, yle_tv1_thumbnail_url, is_live=True),
        list_item_video('YLE TV2', yle_tv2_live_url, yle_tv2_thumbnail_url, is_live=True),
        list_item_video('YLE Teema/Fem', yle_teema_fem_live_url, yle_teema_fem_thumbnail_url, is_live=True),
        list_item_search_menu(),
    ]

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_handle)


def list_item_video(
    label: str,
    path: str,
    thumbnail: Optional[str] = None,
    action: str = 'play',
    is_live: bool = False
) -> Tuple[str, Any, bool]:
    query = urlencode({'action': action, 'path': path})
    item_url = f'{_url}?{query}'
    item = xbmcgui.ListItem(label)
    item.setProperty('IsPlayable', 'true')
    if is_live:
        item.setProperty('IsLive', 'true')
    item.setInfo('video', {'title': label})
    if thumbnail:
        item.setArt({'thumb': thumbnail})
    is_folder = False
    return (item_url, item, is_folder)


def list_item_folder(
    label: str,
    path: str,
    thumbnail: Optional[str] = None
) -> Tuple[str, Any, bool]:
    query = urlencode({'action': 'folder', 'path': path})
    item_url = f'{_url}?{query}'
    item = xbmcgui.ListItem(label)
    if thumbnail:
        item.setArt({'thumb': thumbnail})
    is_folder = True
    return (item_url, item, is_folder)


def list_item_search_menu() -> Tuple[str, Any, bool]:
    item_url = f'{_url}?action=search_menu'
    item = xbmcgui.ListItem('Search')  # TODO translate
    is_folder = True
    return (item_url, item, is_folder)


def list_item_search_pagination(
    label: str,
    keyword: str,
    offset: int,
    page_size: int
) -> Tuple[str, Any, bool]:
    query = urlencode({
        'action': 'search_page',
        'keyword': keyword,
        'offset': offset,
        'page_size': page_size
    })
    item_url = f'{_url}?{query}'
    item = xbmcgui.ListItem(label)
    is_folder = True
    return (item_url, item, is_folder)


def list_item_new_search() -> Tuple[str, Any, bool]:
    item_url = f'{_url}?action=search_input'
    item = xbmcgui.ListItem('[B]New search[/B]')  # TODO translate
    is_folder = True
    return (item_url, item, is_folder)


def do_search_query() -> None:
    dialog = xbmcgui.Dialog()
    keyword = dialog.input('Search', '', type=xbmcgui.INPUT_ALPHANUM)

    if keyword:
        show_search_result_page(keyword)


def show_search_result_page(
    keyword: str,
    offset: int = 0,
    page_size: int = areenaclient.DEFAULT_PAGE_SIZE
) -> None:
    logger.info(f'Executing search: "{keyword}", offset = {offset}, page_size = {page_size}')

    # TODO: show an error message if no results are found
    searchresults = areenaclient.search(keyword, offset, page_size)
    show_links(searchresults)


def show_search() -> None:
    listing = [
        list_item_new_search(),
    ]
    # TODO: search history

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_handle)


def show_folder(path: str) -> None:
    series_id = path.rsplit('/', 1)[-1]
    show_links(areenaclient.playlist(series_id))


def show_links(
    links: Sequence[Union[areenaclient.StreamLink, areenaclient.SearchNavigationLink]]
) -> None:
    listing = []
    for link in links:
        if isinstance(link, areenaclient.StreamLink):
            if link.is_folder:
                item = list_item_folder(
                    label=link.title,
                    path=link.homepage,
                    thumbnail=link.thumbnail_url
                )
            else:
                item = list_item_video(
                    label=link.title,
                    path=link.homepage,
                    thumbnail=link.thumbnail_url,
                    action='play_areenaurl'
                )
        elif isinstance(link, areenaclient.SearchNavigationLink):
            item = list_item_search_pagination(
                label='Next page',
                keyword=link.keyword,
                offset=link.offset,
                page_size=link.page_size
            )

        listing.append(item)

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_handle)


def play_media(url: str) -> None:
    xbmcplugin.setResolvedUrl(_handle, True, listitem=xbmcgui.ListItem(path=url))


def int_or_else(x: str, default: int) -> int:
    try:
        return int(x)
    except ValueError:
        return default


def router(paramstring: str) -> None:
    logger.info(f'router @ {paramstring}')

    params = dict(parse_qsl(paramstring[1:]))
    if params:
        action = params.get('action')
        if action == 'play':
            play_media(params['path'])
        elif action == 'play_areenaurl':
            media_url = extractor.extract_media_url(params['path'])
            if media_url is None:
                # TODO: error
                logger.error(f'Failed to extract media URL for {params["path"]}')
                return

            logger.info(f'Playing URL: {media_url}')
            play_media(media_url)
        elif action == 'folder':
            show_folder(params['path'])
        elif action == 'search_menu':
            show_search()
        elif action == 'search_input':
            do_search_query()
        elif action == 'search_page':
            offset = int_or_else(params.get('offset', ''), 0)
            page_size = int_or_else(params.get('page_size', ''), areenaclient.DEFAULT_PAGE_SIZE)
            show_search_result_page(params.get('keyword', ''), offset, page_size)
        else:
            logger.error(f"Unknown action: {action or '(missing)'}")
    else:
        show_menu()


if __name__ == '__main__':
    router(sys.argv[2])
