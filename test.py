import unittest
from main import Deployer
from moto import mock_rds, mock_s3


class TestItAll(unittest.TestCase):
    def test_config(self):
        deploy = Deployer(configfile='env.template')
        assert deploy.config['PROJECT'] == 'dpr'
        assert deploy.config['DOMAIN'] == 'staging.datapackaged.com'
        assert deploy.config['HEROKU_APP'] == 'dpr-staging'

    def test__env_string_for_heroku(self):
        deploy = Deployer(configfile='env.template')
        out = deploy._env_string_for_heroku()
        print out
        self.assertEqual(out, 'AWS_ACCESS_KEY_ID=access_key_id AWS_SECRET_ACCESS_KEY=secret_key '
                              'AWS_REGION=us-west-2 GITHUB_CLIENT_ID=client_id '
                              'GITHUB_CLIENT_SECRET=client_secret S3_BUCKET_NAME=bucket.name '
                              'JWT_SEED=bucket.name SQLALCHEMY_DATABASE_URI=database@uri')

    def test_heroku_app_exists(self):
        deploy = Deployer(configfile='env.template')
        out = deploy._check_heroku_app_exists('dpr-staging')
        self.assertIsNotNone(out)
        out = deploy._check_heroku_app_exists('app-that-does-not-exist')
        assert (not out)

    @mock_rds
    def test_rds_created_and_exists(self):
        deploy = Deployer(configfile='env.template')
        out = deploy.rds()
        out = deploy.rds_exists()
        self.assertTrue(out)

    @mock_s3
    def test_s3_created(self):
        deploy = Deployer(configfile='env.template')
        out = deploy.s3()
        self.assertTrue(out)

    @mock_s3
    def test_s3_deleted(self):
        deploy = Deployer(configfile='env.template')
        out = deploy.destroy_s3_bucket()
        self.assertTrue(out)
