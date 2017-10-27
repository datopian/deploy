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
import json

import boto3
from botocore.exceptions import ClientError
import dotenv
import psycopg2
import jwt
import dockercloud
import requests

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
        stack = 'docker-cloud stack inspect %s' % self.stackname
        process= subprocess.Popen(stack.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        output = json.loads(output)
        print("Docker status: %s" %output['state'])
        
    def check_apis(self):
        '''Check API call for all services'''
        valid_token = self.config['JWT_TOKEN']
        api_base_url = 'https://' + self.config['DOMAIN_API']
        if self.config['STAGE'] == "production":
            api_base_url = api_base_url.replace('-%s'%self.config['STAGE'], '')
        # Auth service
        url_auth_authorize = urljoin(api_base_url,'auth/authorize')
        response = requests.get(url_auth_authorize)
        assert response.status_code == 200, "Get permission for a auth service is unavailable"
        print("Get permission for a auth service - OK")
        if valid_token:
            url_auth_check = urljoin(api_base_url, 'auth/check')
            response = requests.get(url_auth_check, headers={'Auth-Token': valid_token})
            assert response.status_code == 200, "Check an authentication token's validity for VALID token is unavailable"
            if "true" in response.text:
                print("Check an authentication token's validity for VALID token - OK")
        else:
            print('Skipping Check an authentication token validity for VALID token')
        url_auth_update = urljoin(api_base_url, 'auth/update')
        data = '''
        {
          "Auth-Token": "test",
          "username": "test"
        }
        '''
        response = requests.post(url_auth_update, data)
        success = response.json()['success']
        assert not success, "Username should not change with invalid token"
        print("Not changing username with invalid token  - OK")
        url_auth_public_key = urljoin(api_base_url, 'auth/public-key')
        response = requests.get(url_auth_public_key)
        assert response.status_code == 200, "Receive authorization public key is unavailable"
        print("Receive authorization public key - OK")
        # Metastore service   
        url_metastore_search = urljoin(api_base_url, 'metastore/search')
        response = requests.get(url_metastore_search)
        assert response.status_code == 200, "Metastore search service is unavailable"
        print("Metastore search service - OK")
    
    def check_frontend(self):
        '''Check frontend'''
        api_base_url = 'https://' + self.config['DOMAIN']
        if self.config['STAGE'] == "production":
            api_base_url = 'https://' + self.config['DOMAIN_BASE'] 
        # Home page
        url_home = urljoin(api_base_url, '/')
        response = requests.get(url_home)
        assert response.status_code == 200, "Home page is unavailable"
        print("Home page - OK")
        # Showcase page
        url_showpage = urljoin(api_base_url, 'core/co2-ppm')
        response = requests.get(url_showpage)
        assert response.status_code == 200, "Showcase page is unavailable"
        print("Showcase page - OK")
        # Search page
        # include query string
        url_search = urljoin(api_base_url, 'search?q=co2')
        response = requests.get(url_search)
        assert response.status_code == 200, "Search page is unavailable"
        print("Search page - OK")
        # Pricing page
        url_pricing = urljoin(api_base_url, 'pricing')
        response = requests.get(url_pricing)
        assert response.status_code == 200, "Pricing page is unavailable"
        print("Pricing page - OK")
        # Owner page
        url_owner = urljoin(api_base_url, 'core')
        response = requests.get(url_owner)
        assert response.status_code == 200, "Owner page for valid publisher is unavailable"
        print("Owner page for valid publisher - OK")
        url_owner = urljoin(api_base_url, 'getsdfrbdbgrge')
        response = requests.get(url_owner)
        assert response.status_code == 404, "Owner page for invalid publisher is unavailable"
        print("Owner page for invalid publisher - OK")
        # Logout page
        url_logout = urljoin(api_base_url, 'logout')
        response = requests.get(url_logout)
        assert response.status_code == 200, "Logout page is unavailable"
        print("Logout page - OK")
        # Dashboard page
        valid_token = self.config.get('JWT_TOKEN')
        if valid_token:
            url_dashboard = urljoin(api_base_url, 'dashboard')
            response = requests.get(url_dashboard)
            assert (response.status_code == 404)
            print("Dashboard page without token - OK")
            cookies = dict(jwt=valid_token)
            response = requests.get(url_dashboard, cookies=cookies)
            assert response.status_code == 200, "Dashboard page with token is unavailable"
            print("Dashboard page with token - OK")
        else:
            print('Skipping dashboard test as no login token')
    
    def check(self):
        '''Check docker, API and services all together'''
        print("Checking docker stack status...")
        docker = self.check_docker()
        print("\n")
        print("Checking service API ...\n")
        apis = self.check_apis()
        print("\n")
        print("Checking frontend pages...\n")
        frontend = self.check_frontend()
        return docker, apis, frontend
        
    def users_total(self):
        '''Query number of users'''
        try:
            con = psycopg2.connect(self.config['RDS_URI'])
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) FROM users")
            con.commit()
            result = cur.fetchone()
            print("The number of users: %s" %result[0])
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        
        finally:
            if con is not None:
                con.close()
                
    def users_last_day(self):
        '''Query number of users for the last day'''
        try:
            con = psycopg2.connect(self.config['RDS_URI'])
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) FROM users WHERE join_date > (NOW() - INTERVAL '24 hours')")
            con.commit()
            result = cur.fetchone()
            print("The number of users registered in last day: %s" %result[0])
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if con is not None:
                con.close()
                
    def datasets_total(self):
        '''Total number of datasets and bytes returned from metastore'''
        valid_token = self.config['JWT_TOKEN']
        api_base_url = 'https://' + self.config['DOMAIN_API']
        if self.config['STAGE'] == "production":
            api_base_url = api_base_url.replace('-%s'%self.config['STAGE'], '')
        # Metastore service   
        url_metastore_search = urljoin(api_base_url, 'metastore/search')
        headers = {'Auth-Token': valid_token}
        response = requests.get(url_metastore_search, headers=headers)
        assert response.status_code == 200, "Metastore search service is unavailable"
        test = response.text
        test = json.loads(test)
        try:
            con = psycopg2.connect(self.config['RDS_URI'])
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) FROM specs")
            con.commit()
            result = cur.fetchone()
            print(result)
            print("The total number of datasets: %s" %result[0])
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        
        finally:
            if con is not None:
                con.close()
        print("Number of published datasets: %s" %test['summary'][ u'total'])
        print("Total number of bytes: %s" %test['summary'][ u'totalBytes'])
        
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
