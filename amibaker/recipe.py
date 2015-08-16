import yaml
from ostruct import OpenStruct
from jinja2 import Template
from .util import EpochDateTime


class Recipe(OpenStruct):
    def __init__(self, recipe_file, **override):
        recipe = yaml.load(recipe_file)

        OpenStruct.__init__(self, **recipe)

        if override:
            self.__override_recipe(override)

        self.__render_tags()
        self.__validate()

    def __override_recipe(self, override):
        # TODO: Merge dictionaries instead of this
        if override.get('base_ami'):
            self.base_ami = override['base_ami']

    def __render_tags(self):
        def render(tags, **kwargs):
            for key, value in tags.iteritems():
                template = Template(value)
                tags.__dict__[key] = template.render(**kwargs)

        if not self.ami_tags.Name:
            self.ami_tags.Name = self.__default_name()

        if not self.ec2_tags.Name:
            self.ec2_tags.Name = self.ami_tags.Name

        timestamp = EpochDateTime.now()

        render(self.ec2_tags, timestamp=timestamp)
        render(self.ami_tags, timestamp=timestamp)

    @staticmethod
    def __default_name():
        return 'amibaker - {{ timestamp }}'

    def __validate(self):
        if 'base_ami' not in self.__dict__:
            raise ValueError('You must specify a base_ami on the command \
            line or in the recipe')

        # There's only one behaviour, and it's not behavior!
        if 'imaging_behavior' in self.__dict__ and \
           'imaging_behaviour' not in self.__dict__:
            self.imaging_behaviour = self.imaging_behavior

        if self.imaging_behaviour not in ('stop', 'none'):
            self.imaging_behaviour = 'reboot'
