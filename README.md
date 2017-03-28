Deployment automation for the DPR.

## Installation

Make sure you have `npm` and `python` installed.
Also you will need to have [Heroku account](https://signup.heroku.com/) and [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli#download-and-install) installed
to deploy application on Heroku

```bash
cd ~
git clone https://gitlab.com/atomatic/dpr-deploy
cd dpr-deploy
pip install -r requirements.txt

# setup configuration and replace variables as needed in external_config.json
# you can leave out sqlalchemy_database_uri (will be computed)
cp external_config.json.template external_config.json

# Run script
python main.py run

# Verify all is set up and running
python main.py verify
```

You can run deploy script to boot each instance separately

```bash
# boot s3
python main.py s3

# boot RDS
python main.py rds

# boot Heroku (in this case you will have to set sqlalchemy_database_uri variable manually)
python main.py heroku
```

Destroy Application

```bash
# Tear down all together
python main.py teardown

# Or separately
python main.py destroy_s3_bucket
python main.py rds_destroy
python main.py heroku_destroy
```

For tests

```bash
pytest main.py
```
