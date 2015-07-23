import json
from awsclpy import AWSCLPy


class AmiEc2:
    def __init__(self, **kwrags):
        self.__quiet = kwrags.get('quiet', False)
        self.__awscli = AWSCLPy(quiet=self.__quiet,
                                **kwrags['recipe']['awscli_args'])
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

        instance_profile = self.__recipe.get('iam_instance_profile')
        ami_roles = self.__recipe.get('ami_roles')

        if instance_profile:
            instance_profile_arn = instance_profile.get('arn')
            instance_profile_name = instance_profile.get('name')
        elif isinstance(ami_roles, list):
            instance_profile_arn, instance_profile_name = \
                self.__create_iam_instance_profile(ami_roles)
        else:
            instance_profile_arn = instance_profile_name = None

        iam_instance_profile = []

        if instance_profile_arn:
            iam_instance_profile.append(
                '='.join(['Arn', instance_profile_arn])
            )

        if instance_profile_name:
            iam_instance_profile.append(
                '='.join(['Name', instance_profile_name])
            )

        if iam_instance_profile:
            iam_instance_profile = [
                '--iam-instance-profile',
                ','.join(iam_instance_profile)
            ]

        associate_public_ip_address = \
            '--associate-public-ip-address' \
            if self.__recipe['associate_public_ip'] \
            else '--no-associate-public-ip-address'

        instance = self.__awscli.ec2(
            'run-instances',
            '--image-id', self.__recipe['base_ami'],
            '--key-name', key_name,
            '--security-group-ids', security_group,
            '--instance-type', self.__recipe['instance_type'],
            '--subnet-id', self.__recipe['subnet_id'],
            associate_public_ip_address,
            iam_instance_profile
            )

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

        if hasattr(self, 'iam_instance_profile'):
            self.__delete_iam_instance_profile()

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
        tags = ["Key=%s,Value=%s" % (key, value) for key, value in
                tags.iteritems()]

        self.__awscli.ec2('create-tags',
                          '--resources', resource,
                          '--tags', tags)

    def create_image(self):
        self.__image = self.__awscli.ec2(
            'create-image',
            '--instance-id', self.__instance['InstanceId'],
            '--name', self.__recipe['ami_tags']['Name'],
            '--reboot')

        ami_permissions = self.__recipe.get('ami_permissions')

        if ami_permissions:
            self.__share_image(ami_permissions)

        if not self.__image:
            raise Exception('Image creation for instance %s failed.' %
                            self.__instance['InstanceId'])

        self.tag(self.__image['ImageId'], self.__recipe['ami_tags'])

        return self.__image['ImageId']

    def __share_image(self, account_ids):
        permissions = {'Add': []}

        for account_id in account_ids:
            permissions['Add'].append({'UserId': str(account_id)})

        self.wait_until_image_available()
        self.__awscli.ec2('modify-image-attribute',
                          '--image-id', self.__image['ImageId'],
                          '--launch-permission', json.dumps(permissions))

    def __describe_instance(self):
        self.wait_until_running()

        instance = self.__awscli.ec2('describe-instances',
                                     '--instance-ids',
                                     self.__instance['InstanceId'])

        self.__instance = instance['Reservations'][0]['Instances'][0]

    def __get_vpc_id(self):
        subnet = self.__awscli.ec2('describe-subnets',
                                   '--subnet-ids', self.__recipe['subnet_id'])

        return subnet['Subnets'][0]['VpcId']

    def __create_security_group(self):
        vpc_id = self.__get_vpc_id()

        security_group = self.__awscli.ec2(
            'create-security-group',
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

    def __create_iam_instance_profile(self, ami_roles):
        iam_instance_profile = self.__awscli.iam(
            'create-instance-profile',
            '--instance-profile-name', 'AmiBaker')

        self.iam_instance_profile = iam_instance_profile['InstanceProfile']

        for role in ami_roles:
            self.__awscli.iam('add-role-to-instance-profile',
                              '--instance-profile-name', 'AmiBaker',
                              '--role-name', role)

        return (self.iam_instance_profile['InstanceProfileName'],
                self.iam_instance_profile['Arn'])

    def __delete_iam_instance_profile(self):
        self.__awscli.iam('delete-instance-profile',
                          '--instance-profile-name', 'AmiBaker')

        self.iam_instance_profile = None
