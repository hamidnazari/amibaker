import StringIO
from amibaker.recipe import Recipe
from amibaker.ami_ec2 import AmiEc2
from mock import patch


# @patch('amibaker.ami_ec2.AmiEc2.stop', return_value=True)
# @patch('amibaker.ami_ec2.AWSCLPy.ec2', return_value={'ImageId': 'ami-a1b2c3d4'})
# def test_default_imaging_behaviour(awsclpy_ec2, stop):
def test_default_imaging_behaviour():
    fake_recipe = StringIO.StringIO(b'''
base_ami: ami-deadbeef
ami_tags:
  Name: DEADBEEF
''')
    recipe = Recipe(fake_recipe)
    # ec2 = AmiEc2(recipe=recipe)
    # print recipe
    # ec2._AmiEc2__instance = {'InstanceId': 'i-a1b2c3d4'}

    # ec2.create_image()
    # assert stop.call_count == 0
    # assert awsclpy_ec2.call_count == 2  # 1. create image, 2. tag image
    # awsclpy_ec2.assert_called_with('create-image', '--instance-id',
    #                                'i-a1b2c3d4', '--name', u'DEADBEEF',
    #                                '--reboot')
    # awsclpy_ec2.assert_called_with('create-tags', '--resources',
    #                                'ami-a1b2c3d4', '--tags',
    #                                [u'Key=Name,Value=DEADBEEF'])


# @patch('amibaker.ami_ec2.AmiEc2.stop', return_value=True)
# # @patch('amibaker.ami_ec2.AWSCLPy.ec2', return_value={'ImageId': 'ami-a1b2c3d4'})
# # def test_stop_imaging_behaviour(awsclpy_ec2, stop):
def test_stop_imaging_behaviour():
    fake_recipe = StringIO.StringIO(b'''
base_ami: ami-deadbeef
imaging_behaviour: stop
''')
    recipe = Recipe(fake_recipe)
    # ec2 = AmiEc2(recipe=recipe)
    # ec2._AmiEc2__instance = {'InstanceId': 'i-a1b2c3d4'}

    # ec2.create_image()
    # assert stop.call_count == 1
