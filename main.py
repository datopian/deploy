 #!/usr/bin/python
# -*- coding: utf-8 -*-
import boto3
import json
import os
import subprocess
from moto import mock_rds, mock_s3
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
        self.rds_client = boto3.client(
            'rds',
            aws_access_key_id=config['aws_access_key_id'],
            aws_secret_access_key=config['aws_secret_access_key']
        )
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config['aws_access_key_id'],
            aws_secret_access_key=config['aws_secret_access_key']
        )
        self.ec2_client = boto3.client(
            'ec2',
            aws_access_key_id=config['aws_access_key_id'],
            aws_secret_access_key=config['aws_secret_access_key']
        )

    def run(self):
        self.s3()
        self.rds()
        self.heroku()

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
            cmd = 'heroku config:set %s -a %s' %(envstring, self.config['heroku_app'])
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
            self.rds_create()
            return self.rds_enable_public_acces()
        except Exception as e:
            if 'DBInstanceAlreadyExists' in e.message:
                print('RDS instance already exists - reusing')
                return True
            else:
                print(e.message)
                return False


    def rds_create(self):
        '''Create an RDS instance'''

        rds_instance = '%(project)s-%(stage)s-%(rds_suffix)s' % self.config
        self.rds_client.create_db_instance(
            DBName=self.config['rds_database_name'],
            DBInstanceIdentifier=rds_instance,
            AllocatedStorage=self.config['rds_database_size'],
            Engine=self.config['rds_engine'],
            MasterUsername=self.config['rds_database_username'],
            MasterUserPassword=self.config['rds_database_password'],
            AvailabilityZone=self.config['aws_region']+'b',
            BackupRetentionPeriod=self.config['rds_database_backup_retention'],
            Port=5432,
            MultiAZ=False,
            PubliclyAccessible=True,
            DBInstanceClass=self.config['rds_instance_class']
        )
        # check it worked ...
        if self.rds_exists(wait=1500):
            response = self.rds_client.describe_db_instances(DBInstanceIdentifier=rds_instance)
            instance = response['DBInstances'][0]
            # sets the DB URI for rds in config
            self.config['sqlalchemy_database_uri'] = '{engine}://{user}:{password}@{endpoint}:{port}/{db}'.format(
                engine=instance['Engine'],
                user=instance['MasterUsername'],
                password=self.config['rds_database_password'],
                endpoint=instance['Endpoint']['Address'],
                port=instance['Endpoint']['Port'],
                db=instance['DBName']
            )
            status = response ['DBInstances'][0]['DBInstanceStatus']
            zone = response ['DBInstances'][0]['AvailabilityZone']
            print('RDS DB instance created in %s'% zone, 'status: %s' %status )
            return True
        else:
            raise Exception('Failed to create database')

    def rds_destroy(self):
        rds_instance = '%(project)s-%(stage)s-%(rds_suffix)s' % self.config
        self.rds_client.delete_db_instance(
            DBInstanceIdentifier=rds_instance,
            SkipFinalSnapshot=True,
        )
        if self.rds_exists(wait=1500):
            print( 'RDS DB instance destroyed' )
            return True
        else:
            raise Exception('Failed to Destroy database')


    def rds_exists(self, wait=0):
        rds_instance = '%(project)s-%(stage)s-%(rds_suffix)s' % self.config
        seconds = 0
        while True:
            response = self.rds_client.describe_db_instances(DBInstanceIdentifier=rds_instance)
            if response['DBInstances'][0]['DBInstanceStatus'] == "available":
                break
            print("%s: %d seconds elapsed"%(response['DBInstances'][0]['DBInstanceStatus'],seconds))
            sleep(5)
            seconds += 5
            if seconds > wait:
                return False
        return True

    def rds_enable_public_access(self):
        try:
            self.ec2_client.authorize_security_group_ingress(
                GroupId='sg-a42732c2',
                IpProtocol="-1",
                CidrIp="0.0.0.0/0",
                FromPort=0,
                ToPort=65535
            )
            return True
        except Exception as e:
            if 'InvalidPermission.Duplicate' in e.message:
                print('the specified rule already exists')
                return True
            else:
                print(e.message)
                return False



    def s3(self):
        '''
        Creates S3 Bucket if not exist
        '''
        try:
            response = self.s3_client.create_bucket(
                Bucket=self.config['s3_bucket_name'].replace('.','-'),
                CreateBucketConfiguration={
                    'LocationConstraint': self.config['aws_region']
                },
                ACL='public-read',
            )
            self.s3_enable_cors()
            print 'S3 bucket is created: %s'%response.get('Location')
            return True
        except Exception as e:
            if 'BucketAlreadyOwnedByYou' in e.message:
                print('S3 Bucket already exists')
                return True
            else:
                print(e.message)
                return False


    def s3_enable_cors(self):
        response = self.s3_client.put_bucket_cors(
            Bucket= self.config['s3_bucket_name'].replace('.','-'),
            CORSConfiguration={
                'CORSRules': [
                    {
                        'AllowedHeaders': [
                            '*',
                        ],
                        'AllowedMethods': [
                            'GET'
                        ],
                        'AllowedOrigins': [
                            '*',
                        ]
                    },
                ]
            }
        )
        return True


    def destroy_s3_bucket(self):
        '''
        Deletes s3 bucket
        '''
        s3 = boto3.resource(
            's3',
            aws_access_key_id=self.config['aws_access_key_id'],
            aws_secret_access_key=self.config['aws_secret_access_key']
        )
        try:
            bucket = s3.Bucket(self.config['s3_bucket_name'].replace('.','-'))
            for key in bucket.objects.all():
                key.delete()
            bucket.delete()
            print 'Bucket deleted'
            return True
        except Exception as e:
            if 'NoSuchBucket' in e.message:
                print('S3 Bucket does not  exist')
                return True
            else:
                print(e.message)
                return False


    def test_deploy(self):
        # S3
        response = self.s3_client.get_bucket_acl(
            Bucket=self.config['s3_bucket_name'].replace('.','-')
        )

        for permission in response['Grants']:
            if permission['Grantee']['Type'] == 'Group':
                assert(permission['Permission'] == 'READ')
        response = self.s3_client.get_bucket_cors(
            Bucket=self.config['s3_bucket_name'].replace('.','-')
        )
        assert(response['CORSRules'][0]['AllowedHeaders'][0] == '*')
        assert(response['CORSRules'][0]['AllowedMethods'][0] == 'GET')
        assert(response['CORSRules'][0]['AllowedOrigins'][0] == '*')

        # RDS
        response = self.rds_client.describe_db_instances(DBInstanceIdentifier='%(project)s-%(stage)s-%(rds_suffix)s' % self.config)
        assert(response['DBInstances'][0]['DBInstanceStatus'] == "available")

        # Heroku
        response = self._check_heroku_app_exists(self.config['heroku_app'])
        assert(response)
        print 'Everything is OK'

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
        assert(out == True)

    @mock_s3
    def test_s3_created(self):
        deploy = Deployer(configfile='external_config.json.template')
        out = deploy.s3()
        assert(out == True)

    @mock_s3
    def test_s3_deleted(self):
        deploy = Deployer(configfile='external_config.json.template')
        out = deploy.destroy_s3_bucket()
        assert(out == True)




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
