#!/bin/sh

set -eu

cd "${APP_PATH}"
flask run --host=0.0.0.0 --port=5042