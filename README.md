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
  default_region: ap-southeast-2

base_ami: ami-fd9cecc7
instance_type: t2.micro
subnet_id: subnet-a1b2c3d4
key_name: my_key
associate_public_ip: no
security_groups:
  - sg-b2c3d4e5
ssh_username: ec2-user

ami_tags:
  Name: Base Image {{ timestamp }}
  Cost Centre: My Project
  Provisioner: AmiBaker

ec2_tags:
  Name: amibaker - Base Image {{ timestamp }}
  Cost Centre: My Project
  Availability: Manual

provisioning_script: |
 sudo yum update -y
 sudo yum install -y telnet
```


## Roadmap
* Add tests
* Support image sharing
* Support simple file sharing / one-way sync
* Support execution from one or more scripts
