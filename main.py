 #!/usr/bin/python
# -*- coding: utf-8 -*-
import boto3
import json
import os
import subprocess


fullconfig = {
    'app_debug': False,
    # [postgres, MySQL],
    'rds_suffix': 'ac143bs',
    'rds_engine': 'postgres',
    'rds_database_name': 'dpr_db',
    'rds_database_username': "%(project)s",
    'rds_database_password': 'test_pass',
    'rds_database_size': 10, # GB
    'rds_database_backup_retention': 30,

    # git stuff
    'dpr_api_path': '/tmp/frictionlessdata/dpr-api',

    'submodule_branch': 'gh-pages',
    'submodule_path': 'dpr-js',
    'override_region': '',

    # heroku
    "heroku_app": "%(project)s-%(stage)s",
    "git_heroku": "%(stage)s"
}

class Deployer(object):

    def __init__(self, configfile='external_config.json'):
        extconfig = json.load(open(configfile))
        # TODO: do some checks to ensure we have all the config we need ...
        config = dict(fullconfig)
        config.update(extconfig)
        # do this x times to make sure we do all variable substitutions
        for x in [1,2]:
            for key,value in config.items():
                if isinstance(value, basestring):
                    config[key] = value % config
        self.config = config

    def run(self):
        pass

    def _check_heroku_app_exists(self, app_name):
        cmd = 'heroku apps --json'
        existing_apps = subprocess.check_output(['heroku', 'apps', '--json'])
        existing_apps = [ x['name'] for x in json.loads(existing_apps) ]
        heroku_exists = ( app_name in existing_apps )
        return heroku_exists

    def _env_string_for_heroku(self):
        # XXX=yyy ZZZ=abc
        vars_to_set = [ 'github_client_id', 'github_client_secret',
            'bit_store_bucket_name' ]
        envstring = ' '.join(
            [ '%s=%s' % (key.upper(), self.config[key]) for key in vars_to_set ]
            )
        return envstring

    def heroku(self):
        heroku_exists = self._check_heroku_app_exists(self.config['heroku_app'])
        if heroku_exists:
            cmd = 'heroku git:remote -a %(heroku_app)s' % self.config
        else:
            cmd = 'heroku apps:create %(heroku_app)s --remote %(git_heroku)s' % self.config
        # TODO: check if we had an error??
        out = subprocess.check_output(cmd, shell=True)
        print(out)

        # Now, set up the .env and push
        envstring = self._env_string_for_heroku()

        cmd = 'heroku config:set %s' % envstring
        out = subprocess.check_output(cmd, shell=True)
        print(out)

        cmd = 'git push %(git_heroku) master' % self.config
        out = subprocess.check_output(cmd, shell=True)
        print(out)

        cmd = 'git heroku:domains ...' % self.config
        # out = subprocess.check_output(cmd, shell=True)
        # print(out)


class TestItAll:
    def test_config(self):
        deploy = Deployer()
        assert deploy.config['project'] == 'datahub'
        assert deploy.config['domain'] == 'staging.datapackaged.com'
        assert deploy.config['heroku_app'] == 'datahub-staging'

    def test__env_string_for_heroku(self):
        deploy = Deployer()
        out = deploy._env_string_for_heroku()
        assert out == 'GITHUB_CLIENT_ID= GITHUB_CLIENT_SECRET= BIT_STORE_BUCKET_NAME=bits.staging.datapackaged.com'

    def test_heroku_app_exists(self):
        deploy = Deployer()
        out = deploy._check_heroku_app_exists('data-okfn-org')
        assert(out)
        out = deploy._check_heroku_app_exists('app-that-does-not-exist')
        assert(not out)
    

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

