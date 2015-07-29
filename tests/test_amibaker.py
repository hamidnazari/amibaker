import unittest

import StringIO
from argparse import Namespace

from amibaker.ami_baker import AmiBaker

class TestAmiBaker(unittest.TestCase):
    def setUp(self):
        pass

    def test_import(self):
        pass

    def test_complains_no_base_ami(self):
        fake_recipe = StringIO.StringIO(b'''
awscli_args:
  profile: my_profile
  region: ap-southeast-2 # TODO: optional, otherwise uses awscli profile region

# base_ami: ami-deadbeef
instance_type: t2.micro
subnet_id: subnet-deadbeef
key_name: my_key
associate_public_ip: no

        ''')
        with self.assertRaises(ValueError):
            a = AmiBaker(fake_recipe)

    def test_base_ami_in_recipie(self):
        fake_recipe = StringIO.StringIO(b'''
awscli_args:
  profile: my_profile
  region: ap-southeast-2 # TODO: optional, otherwise uses awscli profile region

base_ami: ami-deadbeef
instance_type: t2.micro
subnet_id: subnet-deadbeef
key_name: my_key
associate_public_ip: no

        ''')
        a = AmiBaker(fake_recipe)
        assert a._AmiBaker__recipe['base_ami'] == 'ami-deadbeef'


    def test_base_ami_overridden(self):
        fake_recipe = StringIO.StringIO(b'''
awscli_args:
  profile: my_profile
  region: ap-southeast-2 # TODO: optional, otherwise uses awscli profile region

base_ami: ami-notthisone
instance_type: t2.micro
subnet_id: subnet-deadbeef
key_name: my_key
associate_public_ip: no

        ''')
        a = AmiBaker(fake_recipe, override_base_ami='ami-overridden')
        assert a._AmiBaker__recipe['base_ami'] == 'ami-overridden'
