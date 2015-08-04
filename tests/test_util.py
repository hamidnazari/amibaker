import time
import datetime
import unittest
import StringIO

from amibaker.util import EpochDateTime

from amibaker.ami_baker import AmiBaker


class TestEpochDateTime(unittest.TestCase):

    def test_str_is_like_a_epoch_timestamp(self):
        mark = int(time.time())
        edt = EpochDateTime.now()
        result = edt.__str__()
        assert result >= mark
        assert '.' not in result

    def test_strftime_still_works(self):
        assert datetime.datetime.now().strftime('%Y-%m-%d') == \
            EpochDateTime.now().strftime('%Y-%m-%d')

    def test_rendertags_timestamp_default(self):
        mark = int(time.time())
        fake_recipe = StringIO.StringIO(b'''
base_ami: whatever
ami_tags:
  Name: ROFL {{ timestamp }} LOL
        ''')
        a = AmiBaker(fake_recipe)
        result = a._AmiBaker__recipe['ami_tags']['Name'].split()
        assert result[0] == 'ROFL'
        assert '.' not in result[1]
        assert int(result[1]) >= mark
        assert result[2] == 'LOL'

    def test_rendertags_timestamp_strftime(self):
        mark = datetime.datetime.now()
        fake_recipe = StringIO.StringIO(b'''
base_ami: whatever
ami_tags:
  Name: ROFL {{ timestamp.strftime('%Y-%m-%d %H:%M:%S') }} LOL
        ''')
        a = AmiBaker(fake_recipe)
        result = a._AmiBaker__recipe['ami_tags']['Name'].split()
        assert result[0] == 'ROFL'
        assert int(result[1].split('-')[0]) == mark.year
        assert int(result[1].split('-')[1]) == mark.month
        assert int(result[1].split('-')[2]) == mark.day
        assert result[3] == 'LOL'
