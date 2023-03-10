import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
from datetime import datetime
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


def set_video_info(
    item: xbmcgui.ListItem,
    label: str,
    published: Optional[datetime] = None,
    plot: Optional[str] = None,
    duration: Optional[int] = None,
):
    if hasattr(xbmc.InfoTagVideo, 'setFirstAired'):
        set_video_info_v20(item, label, published, plot, duration)
    else:
        set_video_info_v19(item, label, published, plot, duration)


def set_video_info_v19(
    item: xbmcgui.ListItem,
    label: str,
    published: Optional[datetime] = None,
    plot: Optional[str] = None,
    duration: Optional[int] = None,
):
    video_info = {'title': label}
    if published is not None:
        video_info['date'] = published.strftime('%d.%m.%Y')
        video_info['aired'] = published.strftime('%Y-%m-%d')
    if plot is not None:
        video_info['plot'] = plot
        video_info['plotoutline'] = plot
    if duration is not None:
        video_info['duration'] = str(duration)

    item.setInfo('video', video_info)


def set_video_info_v20(
    item: xbmcgui.ListItem,
    label: str,
    published: Optional[datetime] = None,
    plot: Optional[str] = None,
    duration: Optional[int] = None,
):
    video_info = item.getVideoInfoTag()

    video_info.setTitle(label)
    if published is not None:
        video_info.setDateAdded(published.strftime('%d.%m.%Y %H:%M:%S'))
        video_info.setFirstAired(published.strftime('%d.%m.%Y'))
    if plot is not None:
        video_info.setPlot(plot)
    video_info.setPlotOutline(plot)
    if duration is not None:
        video_info.setDuration(duration)
