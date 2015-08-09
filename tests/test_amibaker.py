import pytest
import StringIO
from amibaker.ami_baker import AmiBaker


def test_complains_no_base_ami():
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

    with pytest.raises(ValueError):
        AmiBaker(fake_recipe)


def test_base_ami_in_recipe():
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


def test_base_ami_overridden():
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
