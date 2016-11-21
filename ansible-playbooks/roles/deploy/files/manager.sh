venv=$1
${venv}/bin/python manager.py createdb
${venv}/bin/python manager.py populate
