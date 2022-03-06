# Areena plugin for Kodi


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
