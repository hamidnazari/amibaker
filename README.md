# AmiBaker

This is tool for provisioning Linux AWS AMIs. Alternatively you can use [Packer](https://www.packer.io/), however it has two big issues when it comes to creating images in AWS.

0. Packer makes a big assumption that the EC2 you are basing your image off is a public instance, i.e. accessible from the internet. This is not necessarily true if your environment is private with no internet access.
0. Packer will ignore your `~/.ssh/config` file. Therefore you won't be able to jump through a bastion box in order to access your temporary EC2.

## Installation

```
$ pip install amibaker
```

## Usage
```
$ amibaker myimage.yaml
```

## Template
AmiBaker templates are [YAML](http://yaml.org/) files.

### Sample

```yaml
awscli_args:
  profile: my_profile
  region: ap-southeast-2 # TODO: optional, otherwise uses awscli profile region

base_ami: ami-fd9cecc7
instance_type: t2.micro
subnet_id: subnet-a1b2c3d4
key_name: my_key
associate_public_ip: no

ssh_username: ec2-user

iam_instance_profile:
  name: my-profile
  arn:

iam_roles:
  - my-role-1
  - my-role-2

security_groups: # optional, otherwise creates a temporary SG with proper rules
  - sg-e5f6g7h8

ec2_tags:
  Name: amibaker - Base Image {{ timestamp }}
  Cost Centre: My Project
  Availability: Manual

ami_tags:
  Name: Base Image {{ timestamp }}
  Cost Centre: My Project
  Provisioner: AmiBaker

ami_permissions:
  - 123456789012
  - 345678901234
  - 567890123456

imaging_behaviour: restart # restart by default, also accepts 'none' and 'stop'

tasks:
  - copy:
    - src: /path/to/some_file
      dest: /path/to/destination_dir/
    - src: /path/to/another_file
      dest: /path/to/destination_file
      mode: 0600
      sudo: True
  - run:
    - src: /path/to/local/script
      dest: /path/to/remote/dir
      cwd: /path/to/another/remote/dir
    - cwd: /path/to/remote/dir
      body: |
       yum update -y
       yum install -y telnet
      sudo: True
  - copy:
    - src: /path/to/some_other_file
      dest: /path/to/some_other_dir/
  - run:
    - source: /path/to/another/local/script
      cwd: /path/to/another/remote/dir
      sudo: True
```

## Roadmap
* Add more and more tests
* Replace AWSCLI with Boto3
* Improve documentation
* Generate keys if not provided
* Eliminate dependency to Fabric and use Paramiko instead
* CLI argument to pass identity files

## Contributers
* [Chris Speck](https://github.com/cgspeck)
