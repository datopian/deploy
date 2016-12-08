venv=$1
${venv}/bin/python manager.py dropdb
${venv}/bin/python manager.py createdb
${venv}/bin/python manager.py populate
