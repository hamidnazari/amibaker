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


def test_behavior_should_be_behaviour():
    fake_recipe = StringIO.StringIO(b'''
base_ami: ami-deadbeef
imaging_behavior: stop
''')
    recipe = Recipe(fake_recipe)
    assert recipe.imaging_behaviour == 'stop'


def test_behavior_vs_behaviour():
    fake_recipe = StringIO.StringIO(b'''
base_ami: ami-deadbeef
imaging_behaviour: none
imaging_behavior: stop
''')
    recipe = Recipe(fake_recipe)
    assert recipe.imaging_behaviour == 'none'


def test_boolean_values():
    def boolean_recipe(value):
        fake_recipe = StringIO.StringIO(b'''
base_ami: ami-deadbeef
test_boolean: %s
''' % value)
        return Recipe(fake_recipe)

    assert boolean_recipe('yes').test_boolean is True
    assert boolean_recipe('Yes').test_boolean is True
    assert boolean_recipe('YES').test_boolean is True
    assert boolean_recipe('yeS').test_boolean == 'yeS'

    assert boolean_recipe('true').test_boolean is True
    assert boolean_recipe('True').test_boolean is True
    assert boolean_recipe('TRUE').test_boolean is True
    assert boolean_recipe('tRuE').test_boolean == 'tRuE'

    assert boolean_recipe('1').test_boolean == 1
    assert boolean_recipe('0').test_boolean == 0

    assert boolean_recipe('no').test_boolean is False
    assert boolean_recipe('No').test_boolean is False
    assert boolean_recipe('NO').test_boolean is False
    assert boolean_recipe('nO').test_boolean == 'nO'

    assert boolean_recipe('false').test_boolean is False
    assert boolean_recipe('False').test_boolean is False
    assert boolean_recipe('FALSE').test_boolean is False
    assert boolean_recipe('FaLSe').test_boolean == 'FaLSe'
