import StringIO
import pytest
from amibaker.recipe import Recipe


def test_complains_no_base_ami():
    fake_recipe = StringIO.StringIO(b'''
# base_ami: ami-deadbeef
instance_type: t2.micro
''')

    with pytest.raises(ValueError):
        Recipe(fake_recipe)


def test_base_ami_in_recipe():
    fake_recipe = StringIO.StringIO(b'''
base_ami: ami-deadbeef
instance_type: t2.micro
''')

    a = Recipe(fake_recipe)
    assert a.base_ami == 'ami-deadbeef'


def test_default_imaging_behaviour():
    fake_recipe = StringIO.StringIO(b'''
base_ami: ami-deadbeef
''')
    recipe = Recipe(fake_recipe)
    assert recipe.imaging_behaviour == 'restart'


def test_unacceptable_imaging_behaviour():
    fake_recipe = StringIO.StringIO(b'''
base_ami: ami-deadbeef
imaging_behaviour: fly
''')
    recipe = Recipe(fake_recipe)
    assert recipe.imaging_behaviour == 'restart'


def test_behaviour_vs_behavior():
    fake_recipe = StringIO.StringIO(b'''
base_ami: ami-deadbeef
imaging_behavior: stop
''')
    recipe = Recipe(fake_recipe)
    assert recipe.imaging_behaviour == 'stop'
