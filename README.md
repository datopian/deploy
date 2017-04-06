Deployment automation for the DPR.

These python scripts automate the setup and teardown of an entire Data Package Registry instance including all associated infrastructure.

The scripts are designed to be idempotent so you can run them again and again for an instance without an issue.

In addition, the scripts include two useful test utilities:

* `verify`: verify all infrastructure is setup
* `checkflow`: check basic publishing flow works (depends on python `dpm` library)

    ```bash
    python flow.py verify
    ```

## Installation

Make sure you have `npm` and `python` installed.

Also you will need to have [Heroku account](https://signup.heroku.com/) and
[Heroku
CLI](https://devcenter.heroku.com/articles/heroku-cli#download-and-install)
installed to deploy application on Heroku.

Grab the code and install requirements:

```bash
git clone https://gitlab.com/atomatic/dpr-deploy
cd dpr-deploy
pip install -r requirements.txt

# if you want to run tests
pip install -r requirements.test.txt

# if you want to run dpm
pip install ...
```

## Setup configuration

1. Copy over external config:

    ```bash
    cp external_config.json.template external_config.json
    ```
2. Edit config to set essential variables.
3. There are many more variables you can set and replace their default values. Run `python main.py -h` to see details.

## Run the script

```bash
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

## Tests

Install pytest and then run:

```bash
pytest main.py
```

