import contextlib
from mock import Mock, patch
from amibaker.provisioner import Provisioner


class TestProvisioner():
    @classmethod
    def setup_class(cls):
        cls.ec2 = Mock()
        cls.provisioner = Provisioner(cls.ec2, quiet=True)

    def test_copy(self):
        self.copy(times=1)

    def test_no_copy(self):
        self.copy(times=0)

    def test_multiple_copies(self):
        self.copy(times=4)

    def copy(self, times=1):
        copy = []
        source = []
        target = []
        mode = []

        for i in xrange(0, times):
            source.append("/path/to/source%d" % i)
            target.append("/path/to/target%d" % i)
            mode.append((i+1) * 222)  # 222, 444, 666

            copy.append({'from': source[i],
                         'to': target[i],
                         'mode': mode[i]})

        with contextlib.nested(
                patch('amibaker.provisioner.put', return_value=True),  # NOQA
                patch('amibaker.provisioner.sudo', return_value=True)
            ) as (put, sudo):
            self.provisioner._Provisioner__copy(copy)

            assert put.call_count == times

            calls = [put(source[i], target[i], mode=mode[i])
                     for i in reversed(xrange(0, times))]

            put.has_calls(calls)
