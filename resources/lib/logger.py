try:
    import xbmc
    import xbmcaddon
except ImportError:
    xbmc = None


def log_xbmc(message: str, level: int) -> None:
    xbmc.log(f'[{_addonid}] {message}', level)


def log_print(message: str, level: int) -> None:
    print(f'[{_addonid}] {message}')


def debug(message: str) -> None:
    log(message, LOGDEBUG)


def info(message: str) -> None:
    log(message, LOGINFO)


def warning(message: str) -> None:
    log(message, LOGWARNING)


def error(message: str) -> None:
    log(message, LOGERROR)


if xbmc is None:
    # xbmc is not available. Use print for logging.
    # This is useful for testing in development environment. On Kodi, the xbmc
    # is of course available and we'll go to the else branch.
    log = log_print
    _addonid = ''

    LOGDEBUG = 10
    LOGINFO = 20
    LOGWARNING = 30
    LOGERROR = 30
else:
    log = log_xbmc
    _addonid = xbmcaddon.Addon().getAddonInfo('id')

    LOGDEBUG = xbmc.LOGDEBUG
    LOGINFO = xbmc.LOGINFO
    LOGWARNING = xbmc.LOGWARNING
    LOGERROR = xbmc.LOGERROR
