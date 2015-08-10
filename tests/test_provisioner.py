from mock import Mock, call
import pytest
from amibaker import provisioner


@pytest.fixture
def mock_provisioner(monkeypatch):
    monkeypatch.setattr(provisioner, 'put', Mock())
    monkeypatch.setattr(provisioner, 'run', Mock())
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

    calls = [call(source[i], target[i], mode=mode[i], use_sudo=True)
             for i in reversed(xrange(0, times))]
    # print(calls)

    assert sorted(provisioner.put.mock_calls) == sorted(calls)


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


def test_exec_inline_script(mock_provisioner):
    mock_provisioner._exec(body='whoami')
    calls = [call('whoami')]
    assert provisioner.run.mock_calls == calls

    mock_provisioner._exec(body='whoami', cwd='/home/chris')
    calls.append(call('cd /home/chris; whoami'))
    assert provisioner.run.mock_calls == calls
