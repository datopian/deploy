#!/bin/sh
venv=$1
${venv}/exec python manager.py dropdb
${venv}/exec python manager.py createdb
${venv}/exec python manager.py populate
