from mock import Mock, patch
import pytest
from amibaker import provisioner


@pytest.fixture
def mock_provisioner(monkeypatch):
    monkeypatch.setattr(provisioner, 'put', lambda *args, **kwargs: True)
    monkeypatch.setattr(provisioner, 'sudo', lambda *args, **kwargs: True)

    m_ec2 = Mock()
    m_provisioner = provisioner.Provisioner(m_ec2, quiet=True)
    return m_provisioner


@pytest.mark.parametrize("times", [
    # (0),
    (1),
    # (4),
])
def test_many_copys(mock_provisioner, times):
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

    mock_provisioner._Provisioner__copy(copy)

    assert put.call_count == times

    calls = [put(source[i], target[i], mode=mode[i])
             for i in reversed(xrange(0, times))]

    put.has_calls(calls)

