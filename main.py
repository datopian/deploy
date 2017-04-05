# !/usr/bin/python
# -*- coding: utf-8 -*-
import boto3
import json
import subprocess
import sys
import optparse
import inspect
import requests
from time import sleep

#  'item', 'value', 'description'
full_config = [
    ['app_debug', False, ''],

    # aws
    ['AWS_ACCESS_KEY_ID', '', 'AWS Access key'],

    # [postgres, MySQL],
    ['RDS_SUFFIX', 'ac143bs', ''],
    ['RDS_ENGINE', 'postgres', 'Database engine. May be postgres or MySQL'],
    ['RDS_DATABASE_NAME', 'dpr_db', 'Database name'],
    ['RDS_DATABASE_USERNAME', "%(PROJECT)s", 'User name for RDS DB'],
    ['RDS_DATABASE_PASSWORD', 'test_pass', 'Password for RDS'],
    ['RDS_DATABASE_SIZE', 10, 'Database size in GB'],
    ['RDS_DATABASE_BACKUP_RETENTION', 30, ''],
    ['RDS_INSTANCE_CLASS', 'db.t2.micro', 'Instance Class name Eg: db.t2.micro'],

    # git stuff
    ['DPR_API_PATH', '/tmp/frictionlessdata/dpr-api', ''],

    # heroku
    ["HEROKU_APP", "%(PROJECT)s-%(STAGE)s", 'App name on heroku'],
    ["GIT_HEROKU", "%(STAGE)s", 'Remote name for heroku'],

    # domain
    ['DOMAIN', "DOMAIN=%(stage)s.%(domain_base)s", "domain name"]
]


class Deployer(object):

    def __init__(self, configfile='env.template'):
        extconfig = self._load_env_file(configfile)
        config = dict([x[:2] for x in full_config])
        # do config.update(extconfig) but allow for empty string keys in external config
        # (override them with defaults)
        for key, value in extconfig.items():
            if value != '':
                config[key] = value

        # TODO: do some checks to ensure we have all the config we need ...
        # what ones MUST be set by user to non-default values ...
        # if not config['AWS_ACCESS_KEY_ID']:
        #     raise Exception('You need to provide: AWS_ACCESS_KEY_ID')

        # do this x times to make sure we do all variable substitutions
        for x in [1, 2]:
            for key, value in config.items():
                if isinstance(value, basestring):
                    config[key] = value % config
        self.config = config
        self.rds_client = boto3.client(
            'rds',
            region_name=config['AWS_REGION'],
            aws_access_key_id=config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=config['AWS_SECRET_ACCESS_KEY']
        )
        self.s3_client = boto3.client(
            's3',
            region_name=config['AWS_REGION'],
            aws_access_key_id=config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=config['AWS_SECRET_ACCESS_KEY']
        )
        self.ec2_client = boto3.client(
            'ec2',
            region_name=config['AWS_REGION'],
            aws_access_key_id=config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=config['AWS_SECRET_ACCESS_KEY']
        )

    @classmethod
    def _load_env_file(cls, file_name=None):
        with open(file_name, 'r') as f:
            content = f.readlines()

        # removes whitespace chars like '\n' at the end of each line
        return dict([x.strip().split('=') for x in content if '=' in x])

    def run(self):
        self.s3()
        self.rds()
        self.heroku()

    def teardown(self):
        self.destroy_s3_bucket()
        self.rds_destroy()
        self.heroku_destroy()

    @classmethod
    def _check_heroku_app_exists(cls, app_name):
        existing_apps = subprocess.check_output(['heroku', 'apps', '--json'])
        existing_apps = [x['name'] for x in json.loads(existing_apps)]
        heroku_exists = (app_name in existing_apps)
        return heroku_exists

    def _env_string_for_heroku(self):
        vars_to_set = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_REGION',
            'GITHUB_CLIENT_ID',
            'GITHUB_CLIENT_SECRET',
            'S3_BUCKET_NAME',
            'JWT_SEED',
            'SQLALCHEMY_DATABASE_URI'
        ]
        envstring = ' '.join(
            ['%s=%s' % (key.upper(), self.config[key]) for key in vars_to_set]
        )
        return envstring

    def heroku(self):
        heroku_exists = self._check_heroku_app_exists(self.config['HEROKU_APP'])
        if heroku_exists:
            cmd = 'heroku git:remote -a %(HEROKU_APP)s -r %(GIT_HEROKU)s' % self.config
        else:
            cmd = 'heroku apps:create %(HEROKU_APP)s -r %(GIT_HEROKU)s' % self.config
        # execute commands
        try:
            out = subprocess.check_output(cmd, shell=True)

            # set env variables
            envstring = self._env_string_for_heroku()
            cmd = 'heroku config:set %s -a %s' % (envstring, self.config['HEROKU_APP'])
            out = subprocess.check_output(cmd, shell=True)

            # push changes
            cmd = 'git push %(GIT_HEROKU)s master' % self.config
            out = subprocess.check_output(cmd, shell=True)

            # set custom domain
            cmd = 'heroku domains:add %(domain)s -a %(HEROKU_APP)s' % self.config
            out = subprocess.check_output(cmd, shell=True)
        except Exception as e:
            print e
            sys.exit()

    def heroku_destroy(self):
        cmd = 'heroku apps:destroy -a %(HEROKU_APP)s' % self.config
        out = subprocess.check_output(cmd, shell=True)

    def rds(self):
        try:
            self.rds_create()
            return self.rds_enable_public_access()
        except Exception as e:
            if 'DBInstanceAlreadyExists' in e.message:
                print('RDS instance already exists - reusing')
                return True
            else:
                print(e.message)
                return False

    def rds_create(self):
        """Create an RDS instance"""

        rds_instance = '%(PROJECT)s-%(STAGE)s-%(RDS_SUFFIX)s' % self.config
        self.rds_client.create_db_instance(
            DBName=self.config['RDS_DATABASE_NAME'],
            DBInstanceIdentifier=rds_instance,
            AllocatedStorage=self.config['RDS_DATABASE_SIZE'],
            Engine=self.config['RDS_ENGINE'],
            MasterUsername=self.config['RDS_DATABASE_USERNAME'],
            MasterUserPassword=self.config['RDS_DATABASE_PASSWORD'],
            AvailabilityZone=self.config['AWS_REGION'] + 'b',
            BackupRetentionPeriod=self.config['RDS_DATABASE_BACKUP_RETENTION'],
            Port=5432,
            MultiAZ=False,
            PubliclyAccessible=True,
            DBInstanceClass=self.config['RDS_INSTANCE_CLASS']
        )
        # check it worked ...
        if self.rds_exists(wait=1500):
            response = self.rds_client.describe_db_instances(DBInstanceIdentifier=rds_instance)
            instance = response['DBInstances'][0]
            # sets the DB URI for rds in config
            self.config['sqlalchemy_database_uri'] = '{engine}://{user}:{password}@{endpoint}:{port}/{db}'.format(
                engine=instance['Engine'],
                user=instance['MasterUsername'],
                password=self.config['RDS_DATABASE_PASSWORD'],
                endpoint=instance['Endpoint']['Address'],
                port=instance['Endpoint']['Port'],
                db=instance['DBName']
            )
            status = response['DBInstances'][0]['DBInstanceStatus']
            zone = response['DBInstances'][0]['AvailabilityZone']
            print('RDS DB instance created in %s' % zone, 'status: %s' % status)
            return True
        else:
            raise Exception('Failed to create database')

    def rds_destroy(self):
        """Destroy an RDS instance"""
        rds_instance = '%(PROJECT)s-%(STAGE)s-%(RDS_SUFFIX)s' % self.config
        self.rds_client.delete_db_instance(
            DBInstanceIdentifier=rds_instance,
            SkipFinalSnapshot=True,
        )
        if self.rds_exists(wait=1500):
            print('RDS DB instance destroyed')
            return True
        else:
            raise Exception('Failed to Destroy database')

    def rds_exists(self, wait=0):
        """Will check rds instance is already exists or not"""
        rds_instance = '%(PROJECT)s-%(STAGE)s-%(RDS_SUFFIX)s' % self.config
        seconds = 0
        while True:
            response = self.rds_client.describe_db_instances(DBInstanceIdentifier=rds_instance)
            if response['DBInstances'][0]['DBInstanceStatus'] == "available":
                break
            print("%s: %d seconds elapsed" % (response['DBInstances'][0]['DBInstanceStatus'], seconds))
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
        """
        Creates S3 Bucket if not exist
        """
        try:
            response = self.s3_client.create_bucket(
                Bucket=self.config['S3_BUCKET_NAME'],
                CreateBucketConfiguration={
                    'LocationConstraint': self.config['AWS_REGION']
                },
                ACL='public-read',
            )
            self.s3_enable_cors()
            print 'S3 bucket is created: %s' % response.get('Location')
            response = self.s3_client.create_bucket(
                Bucket=self.config['S3_BUCKET_NAME'] + '_log',
                CreateBucketConfiguration={
                    'LocationConstraint': self.config['AWS_REGION']
                }
            )
            print 'S3 log bucket is created: %s' % response.get('Location')
            self._s3_enable_logs()
            print 'S3 log enabled for bucket: %s' % self.config['S3_BUCKET_NAME']
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
            Bucket=self.config['S3_BUCKET_NAME'],
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

    def _s3_enable_logs(self):
        self.s3_client.put_bucket_logging(
            Bucket=self.config['S3_BUCKET_NAME'],
            BucketLoggingStatus={
                'LoggingEnabled': {
                    'TargetBucket': self.config['S3_BUCKET_NAME'] + '_log',
                    'TargetPrefix': '%(PROJECT)s-%(STAGE)s' % self.config
                }
            }
        )

    def destroy_s3_bucket(self):
        """
        Deletes s3 bucket
        """
        s3 = boto3.resource(
            's3',
            region_name=self.config['AWS_REGION'],
            aws_access_key_id=self.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=self.config['AWS_SECRET_ACCESS_KEY']
        )
        try:
            bucket = s3.Bucket(self.config['S3_BUCKET_NAME'])
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

    def help_config(self):
        """Mandatory config options"""
        mandatory_configs = {
            'AWS_ACCESS_KEY_ID': 'aws access key',
            'AWS_SECRET_ACCESS_KEY': 'aws secret key',
            'AWS_REGION': 'aws region name e.g us-west-2',
            'PROJECT': 'project name',
            'DOMAIN_BASE': 'domain base name e.g datapackaged.com',
            'STAGE': 'project deploy stage e.g dev, stage',
            'GITHUB_CLIENT_ID': 'github app client id',
            'GITHUB_CLIENT_SECRET': 'github app client secret',
            'S3_BUCKET_NAME': 'bit store bucket name',
            'JWT_SEED': 'some unique key for signing JWT token',
            'SQLALCHEMY_DATABASE_URI': 'RDS db url',
            'DPR_API_GIT': 'git url for dpr-api'

        }

        config_options = '''Configs:'''
        for k, v in mandatory_configs.iteritems():
            config_options = config_options + '\n \t{key}{s}: {desc}'.format(key=k, desc=v,
                                                                             s=' ' * (25-len(k)))
        print config_options

    def show_config(self):
        """Show all computed config"""
        config_options = '''Configs:'''
        for k in sorted(self.config.keys()):
            value = self.config[k]
            config_options = config_options + '\n \t{key}{s}: {desc}'.format(key=k, desc=value,
                                                                             s=' ' * (30 - len(k)))
        print config_options

    def verify(self):
        """verify the infrastructure"""

        print "checking s3 is working..."
        response = self.s3_client.get_bucket_acl(
            Bucket=self.config['S3_BUCKET_NAME']
        )

        for permission in response['Grants']:
            if permission['Grantee']['Type'] == 'Group':
                assert (permission['Permission'] == 'READ' or permission['Permission'] == 'READ_ACP')
        print "s3 permissions - OK"
        response = self.s3_client.get_bucket_cors(
            Bucket=self.config['S3_BUCKET_NAME']
        )
        assert (response['CORSRules'][0]['AllowedHeaders'][0] == '*')
        assert (response['CORSRules'][0]['AllowedMethods'][0] == 'GET')
        assert (response['CORSRules'][0]['AllowedOrigins'][0] == '*')

        print "s3 CORS - OK"

        url = 'https://%s' %self.config['S3_BUCKET_NAME']
        res = requests.get(url)
        assert (res.status_code == 200)
        print '%s is working over HTTPS - OK'%self.config['S3_BUCKET_NAME']

        url = 'http://%s' %self.config['S3_BUCKET_NAME']
        res = requests.get(url)
        assert (res.status_code == 200)
        print '%s is working over HTTP - OK'%self.config['S3_BUCKET_NAME']

        # RDS
        print
        print "checking RDS is working..."
        response = self.rds_client.describe_db_instances(
            DBInstanceIdentifier='%(PROJECT)s-%(STAGE)s-%(RDS_SUFFIX)s' % self.config)
        assert (response['DBInstances'][0]['DBInstanceStatus'] == "available")
        print "RDS is working - OK"

        # Heroku
        print
        print "checking %s Heroku app is working..." % self.config['HEROKU_APP']
        response = self._check_heroku_app_exists(self.config['HEROKU_APP'])
        assert response
        print "Heroku app is working - OK"

        print
        print 'Checking website is UP and working ...'
        url = 'https://%s' %self.config['DOMAIN']
        res = requests.get(url)
        assert (res.status_code == 200)
        print '%s is working over HTTPS - OK'%self.config['DOMAIN']

        url = 'http://%s' %self.config['DOMAIN']
        res = requests.get(url)
        assert (res.status_code == 200)
        print '%s is working over HTTP - OK'%self.config['DOMAIN']

        url = 'https://%s' %self.config['DOMAIN']
        res = requests.get(url)
        assert (res.headers['Access-Control-Allow-Credentials'])
        print 'Access-Control-Allow-Credentials - OK'
        assert (res.headers['Access-Control-Allow-Origin'] == '*')
        print 'Access-Control-Allow-Origin - OK'
        print
        print 'Everything is OK'

# ==============================================
# CLI

def _object_methods(obj):
    methods = inspect.getmembers(obj, inspect.ismethod)
    methods = filter(lambda (name, y): not name.startswith('_'), methods)
    methods = dict(methods)
    return methods


def _main(functions_or_object):
    is_object = inspect.isclass(functions_or_object)

    _methods = _object_methods(functions_or_object)
    ## this is not working if some options are passed to Deployer
    # if is_object:
    #     _methods = _object_methods(functions_or_object)
    # else:
    #     _methods = _module_functions(functions_or_object)

    usage = '''%prog {action}
Actions:
    '''
    usage += '\n    '.join(
        ['%s %s: %s' % (name, (' ' * (25-len(name))), m.__doc__.split('\n')[0] if m.__doc__ else '') for (name, m)
         in sorted(_methods.items())])
    parser = optparse.OptionParser(usage)
    # Optional: for a config file
    # parser.add_option('-c', '--config', dest='config',
    #         help='Config file to use.')
    options, args = parser.parse_args()

    if not args or not args[0] in _methods:
        parser.print_help()
        sys.exit(1)

    method = args[0]
    if is_object:
        getattr(functions_or_object(), method)(*args[1:])
    else:
        _methods[method](*args[1:])


if __name__ == '__main__':
    _main(Deployer(configfile='.env'))
