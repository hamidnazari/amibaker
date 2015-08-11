from .ami_ec2 import AmiEc2
from .provisioner import Provisioner
from .recipe import Recipe


class AmiBaker(object):
    def __init__(self, recipe, **kwargs):
        self.__quiet = kwargs.get('quiet', False)
        self.__keep_instance = kwargs.get('keep_instance', False)

        override = {}
        override['base_ami'] = kwargs.get('override_base_ami', None)

        self.__recipe = Recipe(recipe, **override)

    def bake(self):
        ec2 = AmiEc2(quiet=self.__quiet, recipe=self.__recipe)
        ec2.instantiate()

        ec2.wait_until_healthy()
        provisioner = Provisioner(ec2, quiet=self.__quiet)

        provisioner.provision(self.__recipe.tasks)

        image_id = ec2.create_image()

        if not self.__keep_instance:
            ec2.wait_until_image_available()
            ec2.terminate()

        print('Your AMI has been baked and is ready to be consumed: ' +
              image_id)
