   # !/usr/bin/python
# -*- coding: utf-8 -*-
import inspect
import os
import subprocess
import optparse
import sys
from time import sleep
import datetime
from urlparse import urljoin

import boto3
from botocore.exceptions import ClientError
import dotenv
import psycopg2
import jwt
import dockercloud
import requests
import subprocess


class Deployer(object):

    def __init__(self, configfile='.env'):
        '''Initialize.

        @param: configfile a .env style config file. See README for more.
        '''
        if os.path.exists(configfile):
            # we set ourselves as load_dotenv has system env variables to take
            # precedence which in our experience is confusing as a user changes a
            # var and re-runs and nothing happens
            # dotenv.load_dotenv('.env')
            out = dotenv.main.dotenv_values(configfile)
            # we need stuff in the environment for docker
            os.environ.update(out)
        self.config = os.environ
        rds_uri = self.config.get('RDS_URI')
        if not rds_uri:
            print('Warning: RDS_URI is not set. please set, or run `python main.py rds`')

    @property
    def stackname(self):
        stackname = '{PROJECT}-{STAGE}'.format(**self.config)
        return stackname

    def _run(self, cmd):
        out = ''
        try:
            out = subprocess.check_output(cmd.split(' '))
        except subprocess.CalledProcessError:
            out = 'Error: ' + out
        print(out)
        return out

    def docker(self):
        '''Deploy app to docker'''
        cmd = 'docker-cloud stack inspect %s' % self.stackname
        out = self._run(cmd)
        if 'Error: ' in out:
            print('No existing stack found. Creating ...')
            self.docker_create()
        else:
            self.docker_update()
            self.docker_deploy()

    def docker_create(self):
        '''Create the docker stack'''
        cmd = 'docker-cloud stack up -f docker-cloud.yml -n %s' % self.stackname
        self._run(cmd)

    def docker_update(self):
        '''Update the docker stack and redeploy'''
        cmd = 'docker-cloud stack update -f docker-cloud.yml --sync %s' % self.stackname
        self._run(cmd)

    def docker_deploy(self):
        '''(Re)Deploy stack.'''
        print('Redeploying stack ...')
        cmd2 = 'docker-cloud stack redeploy --sync %s' % self.stackname
        self._run(cmd2)

    def docker_terminate(self):
        '''...'''
        pass

    def show_config(self):
        """Show computed config

        environment plus .env variables
        """
        config_options = '''Configs:'''
        for k in sorted(self.config.keys()):
            value = self.config[k]
            config_options = config_options + '\n \t{key}{s}: {desc}'.format(key=k, desc=value,
                                                                             s=' ' * (30 - len(k)))
        print (config_options)

    def s3(self):
        """Creates regular and logging S3 Buckets if not exist"""
        s3_client = boto3.client(
            's3',
            aws_access_key_id=self.config['AWS_ACCESS_KEY'],
            aws_secret_access_key=self.config['AWS_SECRET_KEY']
        )
        bucket_list = [self.config[env] for env in self.config if 'BUCKET' in env]
        for bucket in bucket_list:
            try:
                response = s3_client.create_bucket(
                    Bucket=bucket,
                    ACL='public-read',
                )
                self._s3_enable_cors(s3_client, bucket)
                print ('S3 bucket is created: %s' % response.get('Location'))
                response = s3_client.create_bucket(
                    Bucket=bucket + '.log',
                    ACL='log-delivery-write'
                )
                print ('S3 log bucket is created: %s' % response.get('Location'))
                self._s3_enable_logs(s3_client, bucket)
                print ('S3 log enabled for bucket: %s' % response.get('Location'))
                return True
            except Exception as e:
                if 'BucketAlreadyOwnedByYou' in e.message:
                    print('S3 Bucket already exists')
                else:
                    print(e.message)
                return False

    def _s3_enable_cors(self, client, bucket):
        """Enable s3 CORS"""
        response = client.put_bucket_cors(
            Bucket=bucket,
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

    def _s3_enable_logs(self, client, bucket):
        client.put_bucket_logging(
            Bucket=bucket,
            BucketLoggingStatus={
                'LoggingEnabled': {
                    'TargetBucket': bucket + '.log',
                    'TargetPrefix': '%(PROJECT)s-%(STAGE)s' % self.config
                }
            }
        )

    def rds(self):
        """Create an RDS instance and enable public access"""
        client = boto3.client(
            'rds',
            aws_access_key_id=self.config['AWS_ACCESS_KEY'],
            aws_secret_access_key=self.config['AWS_SECRET_KEY']
        )
        try:
            self._rds_create(client)
            return self._rds_enable_public_access()
        except Exception as e:
            if 'DBInstanceAlreadyExists' in e.message:
                print('RDS instance already exists - reusing')
                self._rds_exists(client)
                return True
            else:
                print(e.message)
                return False

    def _rds_create(self, client):
        """Boot an RDS instance"""

        rds_instance = '%(PROJECT)s-%(STAGE)s' % self.config
        while not self.config.get('RDS_PASSWORD'):
            self.config['RDS_PASSWORD'] = raw_input('Please enter password for RDS: ')
        client.create_db_instance(
            DBName=rds_instance.replace('-','_'),
            DBInstanceIdentifier=rds_instance,
            AllocatedStorage=10,
            Engine='postgres',
            MasterUsername=self.config['PROJECT'],
            MasterUserPassword=self.config['RDS_PASSWORD'],
            BackupRetentionPeriod=30,
            Port=5432,
            MultiAZ=False,
            PubliclyAccessible=True,
            DBInstanceClass='db.t2.micro'
        )
        self._rds_exists(client, wait=1500)


    def _rds_exists(self, client, wait=0):
        """Will check rds instance is already exists or not"""
        rds_instance = '%(PROJECT)s-%(STAGE)s' % self.config
        seconds = 0
        while True:
            response = client.describe_db_instances(DBInstanceIdentifier=rds_instance)
            instance = response['DBInstances'][0]
            if instance['DBInstanceStatus'] == "available":
                rds_uri = 'postgresql://{user}:{password}@{endpoint}:{port}/{db}'\
                    .format(
                        user=self.config['PROJECT'],
                        password=self.config.get('RDS_PASSWORD', '<Replace this with Password>'),
                        endpoint=instance['Endpoint']['Address'],
                        port=5432,
                        db=rds_instance.replace('-','_')
                    )
                self.config['RDS_URI'] = rds_uri
                print('Please set RDS_URI in your .env file:\n%s' % rds_uri)
                break
            print("%s: %d seconds elapsed" % (response['DBInstances'][0]['DBInstanceStatus'], seconds))
            sleep(5)
            seconds += 5
            if seconds > wait:
                return False
        return True

    def _rds_enable_public_access(self):
        """Enable public access for RDS database """
        client = boto3.client(
            'ec2',
            aws_access_key_id=self.config['AWS_ACCESS_KEY'],
            aws_secret_access_key=self.config['AWS_SECRET_KEY']
        )
        try:
            client.authorize_security_group_ingress(
                GroupId='sg-c20048bf',
                IpProtocol="-1",
                CidrIp="0.0.0.0/0",
                FromPort=0,
                ToPort=65535
            )
            return True
        except Exception as e:
            if 'InvalidPermission.Duplicate' in e.message:
                print('The specified rule already exists')
                return True
            else:
                print(e.message)
                return False

    def elasticsearch(self):
        '''Create AWS elasticsearch Domain
        '''
        client = boto3.client(
            'es',
            aws_access_key_id=self.config['AWS_ACCESS_KEY'],
            aws_secret_access_key=self.config['AWS_SECRET_KEY']
        )
        message = 'Please provide Docker Node IP'
        message += '\nTo get node IP run:'
        message += '\ndocker-cloud node ls\ndocker-cloud node inspect UUID\n'
        node_ip = raw_input(message)
        self.config.update(node_ip=node_ip)
        client.create_elasticsearch_domain(
            DomainName= '%(PROJECT)s-%(STAGE)s' % self.config,
            ElasticsearchVersion='5.3',
            ElasticsearchClusterConfig={
                'InstanceType': 't2.small.elasticsearch',
                'InstanceCount': 1,
                'DedicatedMasterEnabled': False,
                'ZoneAwarenessEnabled': False
            },
            AccessPolicies= '''{
                "Version": "2012-10-17",
                "Statement": [
                    {
                      "Effect": "Allow",
                      "Principal": {
                        "AWS": "*"
                      },
                      "Action": [
                        "es:*"
                      ],
                      "Condition": {
                        "IpAddress": {
                          "aws:SourceIp": [
                            "%(node_ip)s"
                          ]
                        }
                      },
                      "Resource": "arn:aws:es:us-east-1:280736841384:domain/%(PROJECT)s-%(STAGE)s/*"
                    }
                ]
            }''' % self.config,
            EBSOptions={
                'EBSEnabled': True,
                'VolumeType': 'standard',
                'VolumeSize': 10
            }
        )
        status  = self._check_es_status(client, process='creating', wait=1500)

        if status:
            print('Making sure everything is ok.\nThis will take 30 seconds')
            sleep(30)
            response = client.describe_elasticsearch_domain(
                DomainName= '%(PROJECT)s-%(STAGE)s' % self.config
            )
            print('Elastic Search Domain has been created successfully!')
            print('Endpoint: %s' % response['DomainStatus']['Endpoint'])
            return True
        return False

    def elasticsearch_destroy(self):
        '''Delete AWS elasticsearch Domain
        '''
        client = boto3.client(
            'es',
            aws_access_key_id=self.config['AWS_ACCESS_KEY'],
            aws_secret_access_key=self.config['AWS_SECRET_KEY']
        )
        response = client.delete_elasticsearch_domain(
            DomainName= '%(PROJECT)s-%(STAGE)s' % self.config
        )
        self._check_es_status(client, process='deleting', wait=1500)
        return True

    def _check_es_status(self, client, process='creating', wait=0):
        seconds = 0
        while True:
            try:
                response = client.describe_elasticsearch_domain(
                    DomainName= '%(PROJECT)s-%(STAGE)s' % self.config
                )
            except ClientError as ex:
                if ex.response['Error']['Code'] == 'ResourceNotFoundException':
                    print('Elastic Search Domain deleted successfully!')
                    break
            if not response['DomainStatus']['Processing']:
                break
            print("%d seconds elapsed - %s..." % (seconds, process))
            sleep(5)
            seconds += 5
            if seconds > wait:
                return False
        return True

    def user_create(self, userid='core'):
        '''Create user in the database directly.'''
        try:
            con = psycopg2.connect(self.config['RDS_URI'])
            cur = con.cursor()
            cur.execute("insert into users values ('core', 'core', 'core', 'Core Datasets', 'datasets@okfn.org', '', '%s')" % datetime.datetime.now())
            con.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if con is not None:
                con.close()

    def user_token(self, userid='core'):
        '''Generate an authorization token for user with userid supplied on cli (defaults to core)
        '''
        ret = {
            "userid": userid,
            "permissions": "*",
            "service": "world"
        }
        token = jwt.encode(ret, self.config['PRIVATE_KEY'])
        print(token)
    
    def check_docker(self):
        '''Check docker services status'''
        stack = "docker-cloud stack inspect datahub-production"
        try:
            process= subprocess.Popen(stack.split(), stdout=subprocess.PIPE)
            output, error = process.communicate()
            output = output.split(',')
            print(output[5])
        except:
            print("Command not found")
        
    def check_apis(self):
        '''Check API call for all services'''
        valid_token = self.config['JWT_TOKEN']
        invalid_token = 'ivalid_token'
        api_base_url = 'http://api.' + self.config['DOMAIN_BASE'] 
        # Auth service
        url_auth_authorize = urljoin(api_base_url,'auth/authorize')
        response = requests.get(url_auth_authorize)
        try:
            assert (response.status_code == 200)
            print("Get permission for a service - successfull connected")
        except:
            print("Get permission for a service is unavailable")
        if valid_token:
            url_auth_check = urljoin(api_base_url, 'auth/check')
            response = requests.get(url_auth_check, headers={'Auth-Token': valid_token})
            try:
                assert (response.status_code == 200) 
                if "true" in response.text:
                    print("Check an authentication token's validity for VALID token - successfull connected")
            except:
                print("Check an authentication token's validity for VALID token is unavailable")
        else:
            print('Skipping Check an authentication token validity for VALID token')
        url_auth_check = urljoin(api_base_url, 'auth/check')
        response = requests.get(url_auth_check, headers={'Auth-Token': invalid_token})
        try:
            assert (response.status_code == 200)
            if "false" in response.text:
                print("Check an authentication token's validity for INVALID token - successfull connected")
        except:
            print("Check an authentication token's validity for INVALID token is unavailable")    
        url_auth_update = urljoin(api_base_url, 'auth/update')
        data = '''
        {
          "Auth-Token": "test",
          "username": "test"
        }
        '''
        response = requests.post(url_auth_update, data)
        try:
            assert (response.status_code == 200)
            print("Change the username - successfully connected")
        except: 
            print("Change the username is unavailable")    
        url_auth_public_key = urljoin(api_base_url, 'auth/public-key')
        response = requests.get(url_auth_public_key)
        try: 
            assert (response.status_code == 200)
            print("Receive authorization public key - successfully connected")
        except:
            print("Receive authorization public key is unavailable")
        # Metastore service   
        url_metastore_search = urljoin(api_base_url, 'metastore/search')
        response = requests.get(url_metastore_search)
        try:
            assert (response.status_code == 200)
            print("Metastore search service - successfully connected")
        except:
            print("Metastore search service is unavailable")
            
    def check_frontend(self):
        '''Check frontend'''

        api_base_url = 'http://' + self.config['DOMAIN_BASE'] 
        # Home page
        url_home = urljoin(api_base_url, '/')
        response = requests.get(url_home)
        try:
            assert (response.status_code == 200)
            print("Home page - successfully connected")
        except:
            print("Home page is unavailable")
        # Showcase page
        url_showpage = urljoin(api_base_url, 'core/co2-ppm')
        response = requests.get(url_showpage)
        try:
            assert (response.status_code == 200)
            print("Showcase page - successfully connected")
        except:
            print("Showcase page is unavailable")
        # Search page
        # include query string
        url_search = urljoin(api_base_url, 'search?q=co2')
        response = requests.get(url_search)
        try:
            assert (response.status_code == 200)
            print("Search page - successfully connected")
        except:
            print("Search page is unavailable")
        # Pricing page
        url_pricing = urljoin(api_base_url, 'pricing')
        response = requests.get(url_pricing)
        try:
            assert (response.status_code == 200)
            print("Pricing page - successfully connected")
        except:
            print("Pricing page is unavailable")
        # Owner page
        url_owner = urljoin(api_base_url, 'core')
        response = requests.get(url_owner)
        try:
            assert (response.status_code == 200)
            print("Owner page for valid publisher - successfully connected")
        except:
            print("Owner page for valid publisher is unavailable")
        url_owner = urljoin(api_base_url, 'getsdfrbdbgrge')
        response = requests.get(url_owner)
        try:
            assert (response.status_code == 404)
            print("Owner page for invalid publisher - successfully connected")
        except:
            print("Owner page for invalid publisher is unavailable")
        # Logout page
        url_logout = urljoin(api_base_url, 'logout')
        response = requests.get(url_logout)
        try:
            assert (response.status_code == 200)
            print("Logout page - successfully connected")
        except:
            print("Logout page is unavailable")
        # Login page
        url_login = urljoin(api_base_url, 'login')
        response = requests.get(url_login)
        try: 
            assert (response.status_code == 200)
            print("Login page - successfully connected")
        except:
            print("Login page is unavailable")

        # Dashboard page
        valid_token = self.config.get('JWT_TOKEN', '')
        if valid_token:
            invalid_token = 'ivalid_token'
            url_dashboard = urljoin(api_base_url, 'dashboard')
            cookies = dict(cookies=invalid_token)
            response = requests.get(url_dashboard, cookies=cookies)
            assert (response.status_code == 404)
            print("Dashboard page without cookies - successfully connected")
            
            cookies = dict(cookies=valid_token)
            response = requests.get(url_dashboard, cookies=cookies)
            try:
                assert (response.status_code == 200)
                print("Dashboard page with cookies - successfully connected")
            except:
                print("Dashboard page with cookies is unavailable")
        else:
            print('Skipping dashboard test as no login token')
    
    def check(self):
        '''Check docker, API and services altogether'''
        print("Checking docker stack status...")
        docker = self.check_docker()
        print("\n")
        print("Checking service API ...\n")
        apis = self.check_apis()
        print("\n")
        print("Checking frontend pages...\n")
        frontend = self.check_frontend()
        return docker, apis, frontend
        
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
    _main(Deployer)
