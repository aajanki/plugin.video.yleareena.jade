import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
from typing import Optional
from urllib.parse import urlencode


def play_media(handle: int, url: str, manifest_type: str, headers: Optional[dict] = None) -> None:
    listitem = xbmcgui.ListItem(path=url)
    listitem.setMimeType('application/x-mpegurl')
    listitem.setContentLookup(False)
    listitem.setProperty('inputstream', 'inputstream.adaptive')
    listitem.setProperty('inputstream.adaptive.manifest_type', manifest_type)
    if headers:
        headers_string = urlencode(headers)
        listitem.setProperty('inputstream.adaptive.stream_headers', headers_string)

    xbmcplugin.setResolvedUrl(handle, True, listitem=listitem)


def show_notification(message: str, icon: str = xbmcgui.NOTIFICATION_INFO) -> None:
    xbmcgui.Dialog().notification('Yle Areena', message, icon)


def icon_path(filename: str) -> str:
    addon_path = xbmcaddon.Addon().getAddonInfo('path')
    return xbmcvfs.translatePath(f'{addon_path}/resources/media/{filename}')
