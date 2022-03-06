try:
    import xbmc

    LOGDEBUG = xbmc.LOGDEBUG
    LOGINFO = xbmc.LOGINFO
    LOGWARNING = xbmc.LOGWARNING
    LOGERROR = xbmc.LOGERROR

    # TODO
    def log(message: str, level: int = LOGDEBUG) -> None:
        xbmc.log(f'[{_addonid}] {message}', level)

except ImportError:
    LOGDEBUG = 10
    LOGINFO = 20
    LOGWARNING = 30
    LOGERROR = 30

    def log(message: str, level: int = LOGDEBUG) -> None:
        print(f'[{_addonid}] {message}')

_addonid = 'plugin.video.areenatest'


def debug(message: str) -> None:
    log(message, LOGDEBUG)


def info(message: str) -> None:
    log(message, LOGINFO)


def warning(message: str) -> None:
    log(message, LOGWARNING)


def error(message: str) -> None:
    log(message, LOGERROR)
