   # !/usr/bin/python
# -*- coding: utf-8 -*-
import inspect
import os
import subprocess
import optparse
import sys
import time

import boto3
import dotenv


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
            aws_access_key_id=self.config['OBJECT_STORAGE_ACCESS_KEY'],
            aws_secret_access_key=self.config['OBJECT_STORAGE_SECRET_KEY']
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
