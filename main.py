import sys
import xbmcaddon
import xbmcgui
import xbmcplugin
from typing import Optional, Tuple
from urllib.parse import urlencode, parse_qsl
from resource.lib import areenaclient
from resource.lib import logger
from resource.lib import extractor

_url = sys.argv[0]
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()
ls = _addon.getLocalizedString


def show_menu():
    yle_tv1_live_url = 'https://yletv.akamaized.net/hls/live/622365/yletv1fin/index.m3u8'
    yle_tv1_thumbnail_url = 'https://images.cdn.yle.fi/image/upload/c_fill,f_auto,h_64,q_auto:eco/v1643371700/yle-tv1_vt.png'
    yle_tv2_live_url = 'https://yletv.akamaized.net/hls/live/622366/yletv2fin/index.m3u8'
    yle_tv2_thumbnail_url = 'https://images.cdn.yle.fi/image/upload/c_fill,f_auto,h_64,q_auto:eco/v1643371700/yle-tv2_vt.png'
    yle_teema_fem_live_url = 'https://yletv.akamaized.net/hls/live/622367/yletvteemafemfin/index.m3u8'
    yle_teema_fem_thumbnail_url = 'https://images.cdn.yle.fi/image/upload/c_fill,f_auto,h_64,q_auto:eco/v1643371700/yle-teema-fem_vt.png'

    listing = [
        list_item_video('YLE TV1', yle_tv1_live_url, yle_tv1_thumbnail_url),
        list_item_video('YLE TV2', yle_tv2_live_url, yle_tv2_thumbnail_url),
        list_item_video('YLE Teema/Fem', yle_teema_fem_live_url, yle_teema_fem_thumbnail_url),
        list_item_search(),
    ]

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_handle)


def list_item_video(
    label: str,
    path: str,
    thumbnail: Optional[str] = None,
    action: str = 'play'
) -> Tuple[str, str, str]:
    query = urlencode({'action': action, 'path': path})
    item_url = f'{_url}?{query}'
    item = xbmcgui.ListItem(label)
    item.setProperty('IsPlayable', 'true')
    item.setInfo('video', {'title': label})
    if thumbnail:
        item.setArt({'thumb': thumbnail})
    is_folder = False
    return (item_url, item, is_folder)


def list_item_search() -> Tuple[str, str, str]:
    item_url = f'{_url}?action=searchresults'
    item = xbmcgui.ListItem('Search')  # TODO translate
    is_folder = True
    return (item_url, item, is_folder)


def show_search_results(keyword: str):
    listing = []
    for res in areenaclient.search(keyword):
        listing.append(list_item_video(
            res['title'], res['homepage'], res['thumbnail_image_url'], action='play_areenaurl'))

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_handle)


def play_media(url: str):
    xbmcplugin.setResolvedUrl(_handle, True, listitem=xbmcgui.ListItem(path=url))


def router(paramstring: str):
    params = dict(parse_qsl(paramstring[1:]))
    if params:
        action = params.get('action')
        if action == 'play':
            play_media(params['path'])
        elif action == 'play_areenaurl':
            media_url = extractor.extract_media_url(params['path'])
            if not media_url:
                # TODO: error
                logger.error(f'Failed to extract media URL for {params["path"]}')

            logger.info(f'Playing URL: {media_url}')
            play_media(media_url)
        elif action == 'searchresults':
            show_search_results('Pasila')
        else:
            logger.error(f"Unknown action: {action or '(missing)'}")
    else:
        show_menu()


if __name__ == '__main__':
    router(sys.argv[2])
