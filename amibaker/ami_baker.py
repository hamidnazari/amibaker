import yaml
import time
from jinja2 import Template
from .ami_ec2 import AmiEc2
from .provisioner import Provisioner


class AmiBaker:
    def __init__(self, recipe, **kwargs):
        self.__recipe = yaml.load(recipe)
        self.__render_tags()
        self.__quiet = kwargs.get('quiet', False)
        self.__keep_instance = kwargs.get('keep_instance', False)
        self.__parse_base_ami(kwargs.get('override_base_ami', None))

    @staticmethod
    def __default_name():
        return 'amibaker - {{ timestamp }}'

    def __render_tags(self):
        def render(tags, **kwargs):
            for key, value in tags.iteritems():
                template = Template(value)
                tags[key] = template.render(**kwargs)

        if 'ami_tags' in self.__recipe:
            if not self.__recipe['ami_tags']['Name']:
                self.__recipe['ami_tags']['Name'] = self.__default_name()
        else:
            self.__recipe['ami_tags'] = dict(Name=self.__default_name())

        if 'ec2_tags' in self.__recipe:
            if not self.__recipe['ec2_tags']['Name']:
                self.__recipe['ec2_tags']['Name'] = \
                    self.__recipe['ami_tags']['Name']
        else:
            self.__recipe['ec2_tags'] = dict(Name=self.__recipe['ami_tags']['Name'])

        timestamp = int(time.time())

        render(self.__recipe['ec2_tags'], timestamp=timestamp)
        render(self.__recipe['ami_tags'], timestamp=timestamp)

    def __parse_base_ami(self, override_base_ami):
        if override_base_ami:
            self.__recipe['base_ami'] = override_base_ami

        if 'base_ami' not in self.__recipe:
            raise ValueError('You must specify a base_ami on the command line or in the recipe')
        self._foo = self.__recipe

    def bake(self):
        ec2 = AmiEc2(quiet=self.__quiet, recipe=self.__recipe)
        ec2.instantiate()

        provisioner = Provisioner(ec2, quiet=self.__quiet)

        provision_args = {}

        copy = self.__recipe.get('copy')
        if copy:
            provision_args['copy'] = copy

        script = self.__recipe.get('provisioning_script')
        if script:
            provision_args['script'] = script

        provisioner.provision(**provision_args)

        image_id = ec2.create_image()

        if not self.__keep_instance:
            ec2.wait_until_image_available()
            ec2.terminate()

        print('Your AMI has been baked and is ready to be consumed: ' +
              image_id)
