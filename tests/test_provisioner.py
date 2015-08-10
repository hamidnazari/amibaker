from mock import Mock
import pytest
from amibaker import provisioner


@pytest.fixture
def mock_provisioner(monkeypatch):
    monkeypatch.setattr(provisioner, 'put', Mock())
    monkeypatch.setattr(provisioner, 'sudo', lambda *args, **kwargs: True)

    m_ec2 = Mock()
    m_provisioner = provisioner.Provisioner(m_ec2, quiet=True)
    return m_provisioner


@pytest.mark.parametrize("times", [
    (0),
    (1),
    (4),
])
def test_copy(mock_provisioner, times):
    copy = []
    source = []
    target = []
    mode = []
    tasks = []

    for i in xrange(0, times):
        source.append("/path/to/source%d" % i)
        target.append("/path/to/target%d" % i)
        mode.append((i+1) * 222)  # 222, 444, 666

        copy.append({'src': source[i],
                     'dest': target[i],
                     'mode': mode[i]})

    tasks = [
        {'copy': copy}
    ]

    mock_provisioner.process_tasks(tasks)

    assert provisioner.put.call_count == times

    calls = [provisioner.put(source[i], target[i], mode=mode[i])
             for i in reversed(xrange(0, times))]

    assert provisioner.put.has_calls(calls)


@pytest.mark.parametrize("src,body,args", [
    (None, None, None),
    ("some src", "some body", None),
    (None, "some body", "some args"),
])
def test_exec_validates_input(mock_provisioner, src, body, args):
    """
    Test that _exec raises if invalid combination of input is given
    """
    with pytest.raises(Exception):
        mock_provisioner._exec(src=src, body=body, args=args)
