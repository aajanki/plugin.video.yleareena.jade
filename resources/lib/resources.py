import xbmcvfs


def channel_icon(_addon, channel_name: str) -> str:
    return xbmcvfs.translatePath(
        _addon.getAddonInfo('path') + f'/resources/media/{channel_name}.png')
