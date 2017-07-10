import unittest
from main import Deployer
from moto import mock_s3


class TestItAll(unittest.TestCase):
    def test_config(self):
        deploy = Deployer(configfile='.env.template')
        assert deploy.config['PROJECT'] == 'datahub'
        assert deploy.config['DOMAIN'] == 'staging.datahub.io'

    def test_stackname(self):
        deploy = Deployer(configfile='.env.template')
        assert deploy.stackname == 'datahub-staging'

    @mock_s3
    def test_s3_created(self):
        deploy = Deployer(configfile='env.template')
        out = deploy.s3()
        self.assertTrue(out)
