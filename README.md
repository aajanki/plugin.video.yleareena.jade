# Areena Jade - Yle Areena plugin for Kodi

[![Kodi version 21](https://img.shields.io/badge/kodi%20version-21-blue)](https://kodi.tv/)
[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-yellow.svg)](https://opensource.org/licenses/GPL-3.0)

Kodi plugin for watching video content from [Yle Areena](https://areena.yle.fi/tv). The plugin supports video-on-demand and live TV streams (but not audio streams).

The plugin supports Kodi 21 and later versions.

The plugin is not officially supported by Yle. Some content is available only in Finland.

## Development

### Linting and type checks

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

pre-commit run --all-files

# To automatically run checks on each commit:
pre-commit install
```

### Integration and unit tests

```
python3 -m pytest tests
```

## Known problems

#### Problem: Live TV streams stall

Live TV streams (TV1, TV2, Teema) stall after a few minutes. There is no known fix at the moment.

## License

GPL v3
