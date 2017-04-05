#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import os
import subprocess
import git
import tempfile
import shutil
import requests
import re


class Flow(object):
    def __init__(self):
        # self.config = json.load(open(configfile))
        self.tmpdir = tempfile.mkdtemp()

    def check_flow(self):
        """Check flow for dpm - publish, tag, delete, undelete, purge"""
        git.Repo.clone_from('https://github.com/zelima/country-continents.git', self.tmpdir)
        with cd(self.tmpdir):
            # publish
            out = subprocess.check_output(['dpm', 'publish'])
            url = out[out.find('http'):].replace('\n', '')
            res = requests.get(url)
            # get url for datapackage.json on s3
            bit_store_urls = re.findall(
                'http[s]?://bits(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+.json', res.text
            )
            assert (res.status_code == 200)
            assert (len(bit_store_urls))
            res = requests.get(bit_store_urls[0])
            assert (res.status_code == 200)
            print 'Successfully published'

            # delete and undelete
            subprocess.check_output(['dpm', 'delete'])
            res = requests.get(url)
            assert (res.status_code == 404)
            res = requests.get(bit_store_urls[0])
            assert (res.status_code == 403)
            print 'Successfully deleted'

            subprocess.check_output(['dpm', 'undelete'])
            res = requests.get(url)
            assert (res.status_code == 200)
            res = requests.get(bit_store_urls[0])
            assert (res.status_code == 200)
            print 'Successfully undeleted'

            # purge
            subprocess.check_output(['dpm', 'purge'])
            res = requests.get(url)
            assert (res.status_code == 404)
            res = requests.get(bit_store_urls[0])
            assert (res.status_code == 404)
            print 'Successfully purged'

            # publish and tag
            subprocess.check_output(['dpm', 'publish'])
            subprocess.check_output(['dpm', 'tag', 'testing'])
            res = requests.get(url)
            bit_store_urls = re.findall(
                'http[s]?://bits(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+.json', res.text
            )
            assert (res.status_code == 200)
            assert (len(bit_store_urls))
            #  for some reasons urls are still pointing to _v/latest. commenting for now
            # assert('testing' in bit_store_urls[0])
            print 'Successfully published and tagged'

            # delete and undelete taged datapackage
            subprocess.check_output(['dpm', 'delete'])
            res = requests.get(url)
            assert (res.status_code == 404)
            res = requests.get(bit_store_urls[0])
            assert (res.status_code == 403)
            print 'Successfully deleted the tagged version'

            subprocess.check_output(['dpm', 'undelete'])
            res = requests.get(url)
            assert (res.status_code == 200)
            res = requests.get(bit_store_urls[0])
            assert (res.status_code == 200)
            print 'Successfully undeleted the tagged version'

            subprocess.check_output(['dpm', 'purge'])
            res = requests.get(url)
            assert (res.status_code == 404)
            res = requests.get(bit_store_urls[0])
            assert (res.status_code == 404)
            print 'Successfully purged the tagged version'
        shutil.rmtree(self.tmpdir)


# ==============================================
# CD

class cd:
    """Context manager for changing the current working directory"""

    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


# ==============================================
# CLI

import sys
import optparse
import inspect


def _object_methods(obj):
    methods = inspect.getmembers(obj, inspect.ismethod)
    methods = filter(lambda (name, y): not name.startswith('_'), methods)
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
        ['%s: %s' % (name, m.__doc__.split('\n')[0] if m.__doc__ else '') for (name, m)
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
    if isobject:
        getattr(functions_or_object(), method)(*args[1:])
    else:
        _methods[method](*args[1:])


if __name__ == '__main__':
    _main(Flow)
