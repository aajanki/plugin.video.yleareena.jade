# Areena Jade - Yle Areena plugin for Kodi

[![Kodi version 19](https://img.shields.io/badge/kodi%20version-19-blue)](https://kodi.tv/)
[![Kodi version 20](https://img.shields.io/badge/kodi%20version-20-blue)](https://kodi.tv/)
[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-yellow.svg)](https://opensource.org/licenses/GPL-3.0)

Kodi plugin for watching video content from [Yle Areena](https://areena.yle.fi/tv). The plugin supports video-on-demand and live TV streams (but not audio streams).

The plugin supports Kodi 19 Matrix and later versions.

The plugin is not officially supported by Yle. Some content is available only in Finland.

## Development

### Linting and type checks

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

pre-commit run --all-files
```

### Integration and unit tests

```
python3 -m pytest tests
```

## Known problems

#### Problem: Subtitles are not shown

Try to enable the subtitles in the subtitle menu. Sometimes subtitles are not enabled automatically because the language is misdetected.

Live TV and some other streams are available only as HLS streams, and Kodi 19 doesn't fully support subtitles on those kind of streams. The subtitles might work better on Kodi 20.

## License

GPL v3
