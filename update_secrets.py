import copy
import inspect
import os
import subprocess
import optparse
import sys
from time import sleep
import dotenv
import yaml
import re

class Updater(object):

    def __init__(self, configfile='.env', envfile='kubernetes-envs.yml'):
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
        self.envs = os.environ
        self.configs = yaml.load(open(envfile).read())
        self.configs = self._update_with_envs(self.configs, self.envs)

    def _update_with_envs(self, configfile, env):
        for service in configfile:
            for env_ in configfile[service]['environment']:
                if not configfile[service]['environment'].get(env_):
                    configfile[service]['environment'][env_] = env.get(env_, '')
                else:
                    pattern = re.compile(r'\${.*}')
                    env_value = configfile[service]['environment'][env_]
                    to_replace = pattern.findall(str(env_value))
                    for rpl in to_replace:
                        configfile[service]['environment'][env_] = env.get(rpl[2:-1], '')
        return configfile


    def _run_commands(self, cmd, options=''):
        out = ''
        cmd = cmd.split('') + [options]
        cmd.remove('')
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as process_error:
            all_output = filter(None, process_error.output.split('\n'))
            for output in all_output:
                if not 'Error:' in output:
                    output = 'Error: ' + str(output.strip())
        print(output)
        return output

    def update(self, service=None):
        stage = self.envs.get('STAGE', 'testing')
        cmd = 'kubectl create secret generic %s-%s '
        cmd_del = 'kubectl delete secret %s-%s'
        if service:
            if not self.configs.get(service):
                print('Error: Service ["%s"] Not found' % service)
                return
            envs = self.configs[service]['environment']
            cmd = cmd % (service, stage)
            options = ''
            for env in envs:
                 options += '--from-literal=%s="%s" ' % (env, envs.get(env, ''))

            print('Deleting old secrets for %s' % service)
            out = self._run_commands(cmd_del % (service, stage))
            print('Creating new secrets for %s' % service)
            out = self._run_commands(cmd, options)
            return

        for serv in self.configs:
            cmd = cmd % (serv, stage)
            options = ''
            for env in self.configs[serv]['environment']:
                 options += '--from-literal=%s="%s" ' % (env, self.configs[serv]['environment'].get(env, ''))

            print('Deleting old secrets for %s' % serv)
            self._run_commands(cmd_del % (serv, stage))
            print('Creating new secrets for %s' % serv)
            self._run_commands(cmd, options)
            cmd = 'kubectl create secret generic %s-%s '


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
    _main(Updater)
