#!/usr/bin/env python

import yaml
import argparse
import time
# import amibaker
from jinja2 import Template
from awsclpy import AWSCLPy
from fabric.api import run, env, settings, hide, show

VERSION = '0.1'

class AmiBaker:
    def __init__(self, recipe, **kwargs):
        self.__recipe = yaml.load(recipe)
        self.__render_tags()
        self.__quiet = kwargs.get('quiet', False)
        self.__keep_instance = kwargs.get('keep_instance', False)

    def __render_tags(self):
        def render(tags, **kwargs):
            for key, value in tags.iteritems():
                template = Template(value)
                tags[key] = template.render(**kwargs)

        if not self.__recipe['ami_tags']['Name']:
            self.__recipe['ami_tags']['Name'] = 'amibaker - {{ timestamp }}'

        if not self.__recipe['ec2_tags']['Name']:
            self.__recipe['ec2_tags']['Name'] = self.__recipe['ami_tags']['Name']

        timestamp = int(time.time())

        render(self.__recipe['ec2_tags'], timestamp=timestamp)
        render(self.__recipe['ami_tags'], timestamp=timestamp)

    def bake(self):
        ec2 = AmiEc2(quiet=self.__quiet, recipe=self.__recipe)
        ec2.instantiate()

        provisioner = Provisioner(ec2, quiet=self.__quiet)
        provisioner.provision(self.__recipe['provisioning_script'])

        image_id = ec2.create_image()

        if not self.__keep_instance:
            ec2.wait_until_image_available()
            ec2.terminate()

        print 'Your AMI has been cooked and is ready to be consumed: ' + image_id


class AmiEc2:
    def __init__(self, **kwrags):
        self.__quiet = kwrags.get('quiet', False)
        self.__awscli = AWSCLPy(quiet=self.__quiet, **kwrags['recipe']['awscli_args'])
        self.__recipe = kwrags['recipe']

    def instantiate(self):
        security_group = self.__recipe.get('security_groups')
        if not security_group:
            self.__create_security_group()
            security_group = self.security_group

        key_name = self.__recipe.get('key_name')
        if not key_name:
            self.__generate_key_pair()
            key_name = self.key_name

        instance = self.__awscli.ec2('run-instances',
                                     '--image-id', self.__recipe['base_ami'],
                                     '--key-name', key_name,
                                     '--security-group-ids', security_group,
                                     '--instance-type', self.__recipe['instance_type'],
                                     '--subnet-id', self.__recipe['subnet_id'],
                                     '--associate-public-ip-address' if self.__recipe['associate_public_ip'] else '--no-associate-public-ip-address')

        self.__instance = instance['Instances'][0]

        self.tag(self.__instance['InstanceId'], self.__recipe['ec2_tags'])

        self.__describe_instance()

    def terminate(self):
        self.__awscli.ec2('terminate-instances',
                          '--instance-ids', self.__instance['InstanceId'])

        if hasattr(self, 'security_group'):
            self.wait_until_terminated()
            self.__delete_security_group()

        if hasattr(self, 'key_name'):
            self.__delete_key_pair()

    def wait_until_running(self):
        self.__awscli.ec2('wait', 'instance-running',
                          '--instance-ids', self.__instance['InstanceId'])

    def wait_until_terminated(self):
        self.__awscli.ec2('wait', 'instance-terminated',
                          '--instance-ids', self.__instance['InstanceId'])

    def wait_until_image_available(self):
        self.__awscli.ec2('wait', 'image-available',
                          '--image-ids', self.__image['ImageId'])

    def get_hostname(self):
        if self.__instance.get('PublicDnsName'):
            return self.__instance['PublicDnsName']
        else:
            if self.__instance.get('PublicIpAddress'):
                return self.__instance['PublicIpAddress']
            elif self.__instance.get('PrivateIpAddress'):
                return self.__instance['PrivateIpAddress']

    def get_username(self):
        return self.__recipe.get('ssh_username')

    def tag(self, resource, tags):
        tags = ["Key=%s,Value=%s" % (key, value) for key, value in tags.iteritems()]

        self.__awscli.ec2('create-tags',
                          '--resources', resource,
                          '--tags', tags)

    def create_image(self):
        self.__image = self.__awscli.ec2('create-image',
                                         '--instance-id', self.__instance['InstanceId'],
                                         '--name', self.__recipe['ami_tags']['Name'],
                                         '--reboot')

        if not self.__image:
            raise Exception('Image creation for instance %s failed.' % self.__instance['InstanceId'])

        self.tag(self.__image['ImageId'], self.__recipe['ami_tags'])

        return self.__image['ImageId']

    def __describe_instance(self):
        self.wait_until_running()

        instance = self.__awscli.ec2('describe-instances',
                                     '--instance-ids', self.__instance['InstanceId'])

        self.__instance = instance['Reservations'][0]['Instances'][0]

    def __get_vpc_id(self):
        subnet = self.__awscli.ec2('describe-subnets',
                                   '--subnet-ids', self.__recipe['subnet_id'])

        return subnet['Subnets'][0]['VpcId']

    def __create_security_group(self):
        vpc_id = self.__get_vpc_id()

        security_group = self.__awscli.ec2('create-security-group',
                                           '--group-name', self.__recipe['ec2_tags']['Name'],
                                           '--description', 'Allows temporary SSH access to the box.',
                                           '--vpc-id', vpc_id)

        self.__awscli.ec2('authorize-security-group-ingress',
                          '--group-id', security_group['GroupId'],
                          '--protocol', 'tcp',
                          '--port', 22,
                          '--cidr', '0.0.0.0/0')

        self.__awscli.ec2('authorize-security-group-egress',
                          '--group-id', security_group['GroupId'],
                          '--protocol', 'tcp',
                          '--port', '0-65535',
                          '--cidr', '0.0.0.0/0')

        self.security_group = security_group['GroupId']

    def __delete_security_group(self):
        self.__awscli.ec2('delete-security-group',
                          '--group-id', self.security_group)

    def __generate_key_pair(self):
        # TODO: generate keypair if not provided
        self.key_name = None

    def __delete_key_pair(self):
        # TODO: delete key pair if autogenerated
        pass


class Provisioner:
    def __init__(self, ec2, **kwargs):
        self.__ec2 = ec2
        self.__quiet = kwargs.get('quiet', False)

    def provision(self, script):
        env.host_string = self.__ec2.get_hostname() # host to connect to
        env.user = self.__ec2.get_username() # ssh user to be used for this session
        env.password = None # no passwords available, use private key
        env.use_ssh_config = True # use ~/.ssh/config if avaialble
        env.eagerly_disconnect = True # disconnect right after work is done
        env.skip_bad_hosts = True # no need to check fingerprint
        env.connection_attempts = 6 # number of ssh attemps
        env.timeout = 15 # how many seconds until considered failed attempt
        env.colorize_errors = True

        if self.__quiet:
            settings(hide('warnings', 'running', 'stdout', 'stderr'))

        run(script)

def main():
    argparser = argparse.ArgumentParser()

    argparser.add_argument('recipe',
                           nargs='+',
                           type=argparse.FileType('r'),
                           help='Recipe to bake image from.')

    argparser.add_argument('-q', '--quiet',
                           action='store_true',
                           help='Prevents messages from being printed to stdout.')

    argparser.add_argument('-k', '--keep-instance',
                           action='store_true',
                           help='Keeps EC2 instance after provisioning is done.')

    argparser.add_argument('-v', '--version',
                           action='version',
                           version='%(prog)s ' + VERSION,
                           help='Shows version number.')

    args = argparser.parse_args()

    for recipe in args.recipe:
        baker = AmiBaker(recipe,
                         quiet=args.quiet,
                         keep_instance=args.keep_instance)
        baker.bake()
