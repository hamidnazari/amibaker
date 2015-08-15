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
''')

    a = Recipe(fake_recipe)
    assert a.base_ami == 'ami-deadbeef'


@pytest.mark.parametrize("value,expected", [
    (b'''
base_ami: ami-deadbeef
''', 'reboot'),
    (b'''
base_ami: ami-deadbeef
imaging_behaviour: fly
''', 'reboot'),
    (b'''
base_ami: ami-deadbeef
imaging_behavior: stop
''', 'stop')
])
def test_default_imaging_behaviour(value, expected):
    fake_recipe = StringIO.StringIO(value)
    recipe = Recipe(fake_recipe)
    assert recipe.imaging_behaviour == expected


def test_behavior_vs_behaviour():
    fake_recipe = StringIO.StringIO(b'''
base_ami: ami-deadbeef
imaging_behaviour: none
imaging_behavior: stop
''')
    recipe = Recipe(fake_recipe)
    assert recipe.imaging_behaviour == 'none'
