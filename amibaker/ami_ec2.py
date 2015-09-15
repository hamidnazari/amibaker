import boto3


class AmiEc2(object):
    def __init__(self, **kwrags):
        self.__quiet = kwrags.get('quiet', False)
        self.__recipe = kwrags['recipe']
        self.__ec2 = boto3.client('ec2')

    def instantiate(self):
        security_group = self.__recipe.security_groups
        if not security_group:
            self.__create_security_group()
            security_group = self.security_group

        key_name = self.__recipe.key_name
        if not key_name:
            self.__generate_key_pair()
            key_name = self.key_name

        instance_profile = self.__recipe.iam_instance_profile
        iam_roles = self.__recipe.iam_roles

        if instance_profile:
            instance_profile_arn = instance_profile.arn
            instance_profile_name = instance_profile.name
        elif isinstance(iam_roles, list):
            instance_profile_arn, instance_profile_name = \
                self.__create_iam_instance_profile(iam_roles)
        else:
            instance_profile_arn = instance_profile_name = None

        iam_instance_profile = {}

        if instance_profile_arn:
            iam_instance_profile['Arn'] = instance_profile_arn

        if instance_profile_name:
            iam_instance_profile['Name'] = instance_profile_name

        # if iam_instance_profile:
        #     iam_instance_profile = [
        #         '--iam-instance-profile',
        #         ','.join(iam_instance_profile)
        #     ]

        # associate_public_ip_address = \
        #     '--associate-public-ip-address' \
        #     if self.__recipe.associate_public_ip \
        #     else '--no-associate-public-ip-address'

        instance = self.__ec2.run_instances(
            ImageId=self.__recipe.base_ami,
            KeyName=key_name,
            # SecurityGroupIds = security_group,
            InstanceType=self.__recipe.instance_type,
            # SubnetId = self.__recipe.subnet_id,
            NetworkInterfaces=[
                {
                    'DeviceIndex': 0,
                    'SubnetId': self.__recipe.subnet_id,
                    'Groups': [security_group],
                    'AssociatePublicIpAddress': self.__recipe.associate_public_ip,
                }
            ],
            IamInstanceProfile=iam_instance_profile,
            MinCount=1,
            MaxCount=1
        )

        self.__instance = instance['Instances'][0]

        self.tag(self.__instance['InstanceId'], self.__recipe.ec2_tags)

        self.__describe_instance()

    def get_instance(self, ec2_id):
        self.__describe_instance(ec2_id)

    def terminate(self):
        self.__ec2.terminate_instances(
            InstanceIds=[self.__instance['InstanceId']]

        )

        if hasattr(self, 'security_group'):
            self.wait_until_terminated()
            self.__delete_security_group()

        if hasattr(self, 'key_name'):
            self.__delete_key_pair()

        if hasattr(self, 'iam_instance_profile'):
            self.__delete_iam_instance_profile()

    def wait(self, waiter_name):
        waiter = self.__ec2.get_waiter(waiter_name)
        waiter.wait(InstanceIds=[self.__instance['InstanceId']])

    def wait_until_running(self):
        self.wait('instance_running')

    def wait_until_healthy(self):
        self.wait('instance_status_ok')

    def wait_until_stopped(self):
        self.wait('instance_stopped')

    def wait_until_terminated(self):
        self.wait('instance_terminated')

    def wait_until_image_available(self):
        waiter = self.__ec2.get_waiter('image_available')
        waiter.wait(
            ImageIds=[self.__image['ImageId']]
        )

    def stop(self):
        self.__ec2.stop_instances(
            InstanceIds=[self.__instance['InstanceId']]
        )

    def get_hostname(self):
        if self.__instance.get('PublicDnsName'):
            return self.__instance['PublicDnsName']
        else:
            if self.__instance.get('PublicIpAddress'):
                return self.__instance['PublicIpAddress']
            elif self.__instance.get('PrivateIpAddress'):
                return self.__instance['PrivateIpAddress']

    def get_username(self):
        return self.__recipe.ssh_username

    def tag(self, resource, tags):
        tags = [{'Key': key, 'Value': value} for key, value in
                tags.iteritems()]

        self.__ec2.create_tags(
            Resources=[resource],
            Tags=tags
        )

    def create_image(self):
        if self.__recipe.imaging_behaviour == 'stop':
            self.stop()
            self.wait_until_stopped()
            no_reboot = True
        elif self.__recipe.imaging_behaviour == 'reboot':
            no_reboot = False

        self.__image = self.__ec2.create_image(
            InstanceId=self.__instance['InstanceId'],
            Name=self.__recipe.ami_tags.Name,
            NoReboot=no_reboot)

        ami_permissions = self.__recipe.ami_permissions

        if ami_permissions:
            self.__share_image(ami_permissions)

        if not self.__image:
            raise Exception('Image creation for instance %s failed.' %
                            self.__instance['InstanceId'])

        self.tag(self.__image['ImageId'], self.__recipe.ami_tags)

        return self.__image['ImageId']

    def __share_image(self, account_ids):
        permissions = {'Add': []}

        for account_id in account_ids:
            permissions['Add'].append({'UserId': str(account_id)})

        self.wait_until_image_available()
        self.__ec2.modify_image_attribute(
            ImageId=self.__image['ImageId'],
            LaunchPermission=permissions
        )

    def __describe_instance(self, instance_id=None):
        if instance_id:
            instance = self.__ec2.describe_instances(
                InstanceIds=[instance_id])
        else:
            self.wait_until_running()
            instance = self.__ec2.describe_instances(
                InstanceIds=[self.__instance['InstanceId']])

        self.__instance = instance['Reservations'][0]['Instances'][0]

    def __get_vpc_id(self):
        subnet = self.__ec2.describe_subnets(
            SubnetIds=[self.__recipe.subnet_id])

        return subnet['Subnets'][0]['VpcId']

    def __create_security_group(self):
        vpc_id = self.__get_vpc_id()

        security_group = self.__ec2.create_security_group(
            GroupName=self.__recipe.ec2_tags.Name,
            Description='Allows temporary SSH access to the box.',
            VpcId=vpc_id)

        self.__ec2.authorize_security_group_ingress(
            GroupId=security_group['GroupId'],
            IpProtocol='tcp',
            FromPort=22,
            ToPort=22,
            CidrIp='0.0.0.0/0')

        self.__ec2.authorize_security_group_egress(
            GroupId=security_group['GroupId'],
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 0,
                    'ToPort': 65535,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
        )

        self.security_group = security_group['GroupId']

    def __delete_security_group(self):
        self.__ec2.delete_security_group(
            GroupId=self.security_group)

    def __generate_key_pair(self):
        # TODO: generate keypair if not provided
        self.key_name = None

    def __delete_key_pair(self):
        # TODO: delete key pair if autogenerated
        pass

    def __create_iam_instance_profile(self, iam_roles):
        iam = boto3.client('iam')

        self.iam_instance_profile = iam.create_instance_profile(
            InstanceProfileName='AmiBaker')

        for role in iam_roles:
            iam.add_role_to_instance_profile(
                InstanceProfileName='AmiBaker',
                RoleName=role)

        return (self.iam_instance_profile['InstanceProfileName'],
                self.iam_instance_profile['Arn'])

    def __delete_iam_instance_profile(self):
        iam = boto3.client('iam')
        iam.delete_instance_profile(InstanceProfileName='AmiBaker')

        self.iam_instance_profile = None
