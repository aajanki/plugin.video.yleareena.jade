#!/bin/bash

set -eu

cd ..
rm -rf plugin.video.yleareena.jade.zip
zip -r plugin.video.yleareena.jade.zip plugin.video.yleareena.jade \
  -x '*/.git/*' -x '*/__pycache__/*' -x '*/.pytest_cache/*' \
  -x '*/.mypy_cache/*' -x '*/venv/*' -x '*/.idea/*' -x '*~'
