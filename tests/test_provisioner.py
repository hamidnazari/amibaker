from mock import Mock, call
import pytest
import os
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
    expected_calls = [call('whoami')]
    assert provisioner.run.mock_calls == expected_calls

def test_exec_inline_script_cwd(mock_provisioner):
    mock_provisioner._exec(body='whoami', cwd='/home/chris')
    expected_calls = [call('cd /home/chris; whoami')]
    assert provisioner.run.mock_calls == expected_calls


def test_exec_src_dest(monkeypatch, mock_provisioner):
    src = '/some/local/file'
    args = 'foo --bar=True --baz'
    dest = '/some/remote/file'

    monkeypatch.setattr(os.path, 'isfile', lambda x: True)

    mock_provisioner._exec(
        src=src,
        dest=dest,
        args=args
    )

    expected_run_calls = [
        call('{0} {1}'.format(dest, args)),
        call('rm {0}'.format(dest), warn_only=True),
    ]
    expected_put_calls = [
        call(src, dest, mode=0600, use_sudo=True)
    ]
    assert provisioner.put.mock_calls == expected_put_calls
    assert provisioner.run.mock_calls == expected_run_calls


def test_exec_src_dest_cwd(monkeypatch, mock_provisioner):
    src = '/some/local/file'
    args = 'foo --bar=True --baz'
    dest = '/some/remote/file'
    cwd = '/some/other/remote/folder'

    monkeypatch.setattr(os.path, 'isfile', lambda x: True)

    mock_provisioner._exec(
        src=src,
        dest=dest,
        cwd=cwd,
        args=args
    )

    expected_run_calls = [
        call('cd {0}; {1} {2}'.format(cwd, dest, args)),
        call('rm {0}'.format(dest), warn_only=True),
    ]
    expected_put_calls = [
        call(src, dest, mode=0600, use_sudo=True)
    ]
    assert provisioner.put.mock_calls == expected_put_calls
    assert provisioner.run.mock_calls == expected_run_calls
