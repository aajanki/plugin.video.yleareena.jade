import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode
from resources.lib.manifesturl import ManifestUrl


def play_media(handle: int, manifest: ManifestUrl) -> None:
    listitem = xbmcgui.ListItem(path=manifest.url)
    listitem.setMimeType('application/x-mpegurl')
    listitem.setContentLookup(False)
    listitem.setProperty('inputstream', 'inputstream.adaptive')
    if manifest.headers:
        headers_string = urlencode(manifest.headers)
        listitem.setProperty('inputstream.adaptive.manifest_headers', headers_string)

    xbmcplugin.setResolvedUrl(handle, True, listitem=listitem)


def show_notification(message: str, icon: str = xbmcgui.NOTIFICATION_INFO) -> None:
    xbmcgui.Dialog().notification('Yle Areena', message, icon)


def icon_path(filename: str) -> str:
    addon_path = xbmcaddon.Addon().getAddonInfo('path')
    return xbmcvfs.translatePath(f'{addon_path}/resources/media/{filename}')


def set_video_info(
    item: xbmcgui.ListItem,
    *,
    published: Optional[datetime] = None,
    plot: Optional[str] = None,
    duration: Optional[int] = None,
):
    video_info = item.getVideoInfoTag()

    if published is not None:
        video_info.setDateAdded(published.strftime('%d.%m.%Y %H:%M:%S'))
        video_info.setFirstAired(published.strftime('%d.%m.%Y'))
    if plot is not None:
        video_info.setPlot(plot)
    if duration is not None:
        video_info.setDuration(duration)
