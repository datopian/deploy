 #!/usr/bin/python
# -*- coding: utf-8 -*-
import boto3
import json
import os
import subprocess
from moto import mock_rds
from time import sleep

#  'item', 'value', 'description'
fullconfig = [
    [ 'app_debug', False, '' ],

    # aws
    [ 'aws_access_key_id', '', 'AWS Access key'],

    # [postgres, MySQL],
    [ 'rds_suffix', 'ac143bs', '' ],
    [ 'rds_engine', 'postgres', 'Database engine. May be postgres or MySQL' ],
    [ 'rds_database_name', 'dpr_db', 'Database name' ],
    [ 'rds_database_username', "%(project)s", 'User name for RDS DB' ],
    [ 'rds_database_password', 'test_pass', 'Password for RDS' ],
    [ 'rds_database_size', 10, 'Database size in GB'],
    [ 'rds_database_backup_retention', 30, '' ],
    [ 'rds_instance_class', 'db.t2.micro', 'Instance Class name Eg: db.t2.micro' ],

    # git stuff
    [ 'dpr_api_path', '/tmp/frictionlessdata/dpr-api', '' ],
    [ 'override_region', '', '' ],

    # heroku
    [ "heroku_app", "%(project)s-%(stage)s", 'App name on heroku' ],
    [ "git_heroku", "%(stage)s", 'Remote name for heroku' ]
]

class Deployer(object):

    def __init__(self, configfile='external_config.json'):
        extconfig = json.load(open(configfile))
        config = dict([ x[:2] for x in fullconfig ])
        # do config.update(extconfig) but allow for empty string keys in external config
        # (override them with defaults)
        for key,value in extconfig.items():
            if value != '':
                config[key] = value

        # TODO: do some checks to ensure we have all the config we need ...
        # what ones MUST be set by user to non-default values ...
        # if not config['aws_access_key_id']:
        #     raise Exception('You need to provide: aws_access_key_id')

        # do this x times to make sure we do all variable substitutions
        for x in [1,2]:
            for key,value in config.items():
                if isinstance(value, basestring):
                    config[key] = value % config
        self.config = config

    def run(self):
        pass

    def _check_heroku_app_exists(self, app_name):
        existing_apps = subprocess.check_output(['heroku', 'apps', '--json'])
        existing_apps = [ x['name'] for x in json.loads(existing_apps) ]
        heroku_exists = ( app_name in existing_apps )
        return heroku_exists

    def _env_string_for_heroku(self):
        vars_to_set = [
            'aws_access_key_id',
            'aws_secret_access_key',
            'aws_region',
            'github_client_id',
            'github_client_secret',
            's3_bucket_name',
            'flasks3_bucket_name',
            'sqlalchemy_database_uri'
        ]
        envstring = ' '.join(
            [ '%s=%s' % (key.upper(), self.config[key]) for key in vars_to_set ]
            )
        return envstring

    def heroku(self):
        heroku_exists = self._check_heroku_app_exists(self.config['heroku_app'])
        if heroku_exists:
            cmd = 'heroku git:remote -a %(heroku_app)s -r %(git_heroku)s' % self.config
        else:
            cmd = 'heroku apps:create %(heroku_app)s -r %(git_heroku)s' % self.config
        # execute commands
        try:
            out = subprocess.check_output(cmd, shell=True)

            # set env variables
            envstring = self._env_string_for_heroku()
            cmd = 'heroku config:set %s' %envstring
            out = subprocess.check_output(cmd, shell=True)

            # push changes
            cmd = 'git push %(git_heroku)s master' % self.config
            out = subprocess.check_output(cmd, shell=True)

            # set custom domain
            cmd = 'heroku domains:add %(domain)s -a %(heroku_app)s' % self.config
            out = subprocess.check_output(cmd, shell=True)
        except Exception as e:
            print e
            sys.exit()

    def rds(self):
        try:
            return self.rds_create()
        except Exception as e:
            if 'DBInstanceAlreadyExists' in e.message:
                print('RDS instance already exists - reusing')
                return True
            else:
                print(e.message)
                return False


    def rds_create(self):
        '''Create an RDS instance'''
        rds = boto3.client(
            'rds',
            aws_access_key_id=self.config['aws_access_key_id'],
            aws_secret_access_key=self.config['aws_secret_access_key']
        )
        rds_instance = '%(project)s-%(stage)s-%(rds_suffix)s' % self.config
        rds.create_db_instance(
            DBName=self.config['rds_database_name'],
            DBInstanceIdentifier=rds_instance,
            AllocatedStorage=self.config['rds_database_size'],
            Engine=self.config['rds_engine'],
            MasterUsername=self.config['rds_database_username'],
            MasterUserPassword=self.config['rds_database_password'],
            ### For some resons if AvailabilityZone is specified it is throwing error:
            ### us-west-2 is not a valid availability zone. (does on any region)
            # AvailabilityZone=self.config['aws_region'],
            BackupRetentionPeriod=self.config['rds_database_backup_retention'],
            Port=5423,
            MultiAZ=False,
            PubliclyAccessible=True,
            DBInstanceClass=self.config['rds_instance_class']
        )
        # check it worked ...
        if self.rds_exists(wait=1500):
            response = rds.describe_db_instances(DBInstanceIdentifier=rds_instance)
            status = response ['DBInstances'][0]['DBInstanceStatus']
            zone = response ['DBInstances'][0]['AvailabilityZone']
            print('RDS DB instance created in %s'% zone, 'status: %s' %status )
            return True
        else:
            raise Exception('Failed to create database')

    def rds_destroy(self):
        rds = boto3.client(
            'rds',
            aws_access_key_id=self.config['aws_access_key_id'],
            aws_secret_access_key=self.config['aws_secret_access_key']
        )
        rds_instance = '%(project)s-%(stage)s-%(rds_suffix)s' % self.config
        rds.delete_db_instance(
            DBInstanceIdentifier=rds_instance,
            SkipFinalSnapshot=True,
        )
        if self.rds_exists(wait=1500):
            print( 'RDS DB instance destroyed' )
            return True
        else:
            raise Exception('Failed to Destroy database')


    def rds_exists(self, wait=0):
        rds = boto3.client(
            'rds',
            aws_access_key_id=self.config['aws_access_key_id'],
            aws_secret_access_key=self.config['aws_secret_access_key']
        )
        rds_instance = '%(project)s-%(stage)s-%(rds_suffix)s' % self.config
        seconds = 0
        while True:
            response = rds.describe_db_instances(DBInstanceIdentifier=rds_instance)
            if response['DBInstances'][0]['DBInstanceStatus'] == "available":
                break
            print("%s: %d seconds elapsed"%(response['DBInstances'][0]['DBInstanceStatus'],seconds))
            sleep(5)
            seconds += 5
            if seconds > wait:
                return False
        return True

class TestItAll:
    def test_config(self):
        deploy = Deployer(configfile='external_config.json.template')
        assert deploy.config['project'] == 'dpr'
        assert deploy.config['domain'] == 'staging.datapackaged.com'
        assert deploy.config['heroku_app'] == 'dpr-staging'

    def test__env_string_for_heroku(self):
        deploy = Deployer(configfile='external_config.json.template')
        out = deploy._env_string_for_heroku()
        assert out =='AWS_ACCESS_KEY_ID=access_key_id AWS_SECRET_ACCESS_KEY=secret_key '+\
         'AWS_REGION=region GITHUB_CLIENT_ID=client_id GITHUB_CLIENT_SECRET=clien_secret '+\
         'S3_BUCKET_NAME=bucket.name FLASKS3_BUCKET_NAME=flusk.bucket.name SQLALCHEMY_DATABASE_URI=database@uri'


    def test_heroku_app_exists(self):
        deploy = Deployer(configfile='external_config.json.template')
        out = deploy._check_heroku_app_exists('dpr-staging')
        assert(out)
        out = deploy._check_heroku_app_exists('app-that-does-not-exist')
        assert(not out)

    @mock_rds
    def test_rds_created_and_exists(self):
        deploy = Deployer(configfile='external_config.json.template')
        out = deploy.rds()
        out = deploy.rds_exists()
        assert(out)


## ==============================================
## CLI

import sys
import optparse
import inspect

def _object_methods(obj):
    methods = inspect.getmembers(obj, inspect.ismethod)
    methods = filter(lambda (name,y): not name.startswith('_'), methods)
    methods = dict(methods)
    return methods

def _main(functions_or_object):
    isobject = inspect.isclass(functions_or_object)
    if isobject:
        _methods = _object_methods(functions_or_object)
    else:
        _methods = _module_functions(functions_or_object)

    usage = '''%prog {action}
Actions:
    '''
    usage += '\n    '.join(
        [ '%s: %s' % (name, m.__doc__.split('\n')[0] if m.__doc__ else '') for (name,m)
        in sorted(_methods.items()) ])
    parser = optparse.OptionParser(usage)
    # Optional: for a config file
    # parser.add_option('-c', '--config', dest='config',
    #         help='Config file to use.')
    options, args = parser.parse_args()

    if not args or not args[0] in _methods:
        parser.print_help()
        sys.exit(1)

    method = args[0]
    if isobject:
        getattr(functions_or_object(), method)(*args[1:])
    else:
        _methods[method](*args[1:])

if __name__ == '__main__':
    _main(Deployer)

	# deploy = Deployer()
    # deploy.run()
