from mock import Mock, call
import pytest
import os
from amibaker import provisioner
import fabric.operations
from ostruct import OpenStruct


@pytest.fixture
def mock_provisioner(monkeypatch):
    monkeypatch.setattr(fabric.operations, 'put', Mock())
    monkeypatch.setattr(fabric.operations, 'run', Mock())
    monkeypatch.setattr(fabric.operations, 'sudo', Mock())

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
    sudo = []

    for i in xrange(0, times):
        source.append("/path/to/source%d" % i)
        target.append("/path/to/target%d" % i)
        mode.append((i+1) * 222)  # 222, 444, 666
        sudo.append(i % 2 == 0)

        copy.append({
            'src': source[i],
            'dest': target[i],
            'mode': mode[i],
            'sudo': sudo[i]
        })

    for task in copy:
        mock_provisioner._copy(**task)

    assert fabric.operations.put.call_count == times

    expected_run_calls = []
    expected_put_calls = []
    expected_sudo_calls = []

    for i in xrange(0, times):
        expected_put_calls.append(
            call(source[i], target[i], mode=mode[i], use_sudo=sudo[i]))
        mkdir_call = call('mkdir -p {0}'.format('/path/to'))

        if i % 2 == 0:
            expected_sudo_calls.append(mkdir_call)
        else:
            expected_run_calls.append(mkdir_call)

    assert fabric.operations.put.mock_calls == expected_put_calls
    assert fabric.operations.run.mock_calls == expected_run_calls
    assert fabric.operations.sudo.mock_calls == expected_sudo_calls


@pytest.mark.parametrize("src,body,args", [
    (None, None, None),
    ("some src", "some body", None),
    (None, "some body", "some args"),
])
def test_run_validates_input(mock_provisioner, src, body, args):
    """
    Test that _run raises if invalid combination of input is given
    """
    with pytest.raises(Exception):
        mock_provisioner._run(src=src, body=body, args=args)


def test_run_inline_script(mock_provisioner):
    mock_provisioner._run(body='whoami')
    expected_calls = [call('whoami')]
    assert fabric.operations.run.mock_calls == expected_calls


def test_run_inline_sudo_script(mock_provisioner):
    mock_provisioner._run(body='whoami', sudo=True)
    expected_calls = [call('whoami')]
    assert fabric.operations.sudo.mock_calls == expected_calls


def test_run_inline_no_sudo_script(mock_provisioner):
    mock_provisioner._run(body='whoami', sudo=False)
    expected_calls = [call('whoami')]
    assert fabric.operations.run.mock_calls == expected_calls


def test_run_inline_script_cwd(mock_provisioner):
    mock_provisioner._run(body='whoami', cwd='/home/chris')
    expected_calls = [call('cd /home/chris; whoami')]
    assert fabric.operations.run.mock_calls == expected_calls


def test_run_src_dest(monkeypatch, mock_provisioner):
    src = '/some/local/file'
    args = 'foo --bar=True --baz'
    dest = '/some/remote/file'

    monkeypatch.setattr(os.path, 'isfile', lambda x: True)

    mock_provisioner._run(
        src=src,
        dest=dest,
        args=args
    )

    expected_run_calls = [
        call('mkdir -p {0}'.format('/some/remote')),
        call('{0} {1}'.format(dest, args)),
    ]
    expected_put_calls = [
        call(src, dest, mode=0500, use_sudo=False)
    ]
    expected_sudo_calls = [
        call('rm {0}'.format(dest), warn_only=True),
    ]
    assert fabric.operations.put.mock_calls == expected_put_calls
    assert fabric.operations.run.mock_calls == expected_run_calls
    assert fabric.operations.sudo.mock_calls == expected_sudo_calls


def test_run_src_dest_cwd(monkeypatch, mock_provisioner):
    src = '/some/local/file'
    args = 'foo --bar=True --baz'
    dest = '/some/remote/file'
    cwd = '/some/other/remote/folder'

    monkeypatch.setattr(os.path, 'isfile', lambda x: True)

    mock_provisioner._run(
        src=src,
        dest=dest,
        cwd=cwd,
        args=args
    )

    expected_run_calls = [
        call('mkdir -p {0}'.format('/some/remote')),
        call('cd {0}; {1} {2}'.format(cwd, dest, args)),
    ]
    expected_put_calls = [
        call(src, dest, mode=0500, use_sudo=False)
    ]
    expected_sudo_calls = [
        call('rm {0}'.format(dest), warn_only=True),
    ]
    assert fabric.operations.put.mock_calls == expected_put_calls
    assert fabric.operations.run.mock_calls == expected_run_calls
    assert fabric.operations.sudo.mock_calls == expected_sudo_calls


def test_run_src_nodest(monkeypatch, mock_provisioner):
    """
    In this scenario _run has to call mktemp on remote system to come up with a
    suitable temporary file to use
    """
    src = '/some/local/file'
    args = 'foo --bar=True --baz'

    monkeypatch.setattr(os.path, 'isfile', lambda x: True)

    def side_effect(x, warn_only=None):
        if x == 'mktemp':
            return '/tmp/whatever'

        return True

    monkeypatch.setattr(fabric.operations, 'run', Mock(side_effect=side_effect))

    mock_provisioner._run(
        src=src,
        args=args
    )

    expected_run_calls = [
        call('mktemp'),
        call('mkdir -p {0}'.format('/tmp')),
        call('{0} {1}'.format('/tmp/whatever', args)),
    ]
    expected_put_calls = [
        call(src, '/tmp/whatever', mode=0500, use_sudo=False),
    ]
    expected_sudo_calls = [
        call('rm {0}'.format('/tmp/whatever'), warn_only=True),
    ]
    assert fabric.operations.put.mock_calls == expected_put_calls
    assert fabric.operations.run.mock_calls == expected_run_calls
    assert fabric.operations.sudo.mock_calls == expected_sudo_calls


def test_process_tasks_single_inline(mock_provisioner):
    job1 = OpenStruct(body='whoami')
    task1 = OpenStruct(run=[job1])
    list_of_tasks = [task1]

    mock_provisioner.process_tasks(list_of_tasks)
    expected_calls = [call('whoami')]
    assert fabric.operations.run.mock_calls == expected_calls


def test_process_tasks_single_sudo_inline(mock_provisioner):
    job1 = OpenStruct(body='whoami', sudo=True)
    task1 = OpenStruct(run=[job1])
    list_of_tasks = [task1]

    mock_provisioner.process_tasks(list_of_tasks)
    expected_calls = [call('whoami')]
    assert fabric.operations.sudo.mock_calls == expected_calls


def test_process_tasks_single_no_sudo_inline(mock_provisioner):
    job1 = OpenStruct(body='whoami', sudo=False)
    task1 = OpenStruct(run=[job1])
    list_of_tasks = [task1]

    mock_provisioner.process_tasks(list_of_tasks)
    expected_calls = [call('whoami')]
    assert fabric.operations.run.mock_calls == expected_calls


def test_process_tasks_src_dest_cwd(monkeypatch, mock_provisioner):
    src = '/some/local/file'
    args = 'foo --bar=True --baz'
    dest = '/some/remote/file'
    cwd = '/some/other/remote/folder'

    monkeypatch.setattr(os.path, 'isfile', lambda x: True)

    job1 = OpenStruct(src=src, args=args, dest=dest, cwd=cwd)
    task1 = OpenStruct(run=[job1.__dict__])
    list_of_tasks = [task1]

    mock_provisioner.process_tasks(list_of_tasks)

    expected_run_calls = [
        call('mkdir -p {0}'.format('/some/remote')),
        call('cd {0}; {1} {2}'.format(cwd, dest, args)),
    ]
    expected_put_calls = [
        call(src, dest, mode=0500, use_sudo=False)
    ]
    expected_sudo_calls = [
        call('rm {0}'.format(dest), warn_only=True),
    ]
    assert fabric.operations.put.mock_calls == expected_put_calls
    assert fabric.operations.run.mock_calls == expected_run_calls
    assert fabric.operations.sudo.mock_calls == expected_sudo_calls


def test_process_tasks_src_only(monkeypatch, mock_provisioner):
    """
    In this scenario _run has to call mktemp on remote system to come up with a
    suitable temporary file to use
    """
    src = '/some/local/file'

    monkeypatch.setattr(os.path, 'isfile', lambda x: True)

    def side_effect(x, warn_only=None):
        if x == 'mktemp':
            return '/tmp/whatever'

        return True

    monkeypatch.setattr(fabric.operations, 'run', Mock(side_effect=side_effect))

    job1 = OpenStruct(src=src)
    task1 = OpenStruct(run=[job1.__dict__])
    list_of_tasks = [task1]

    mock_provisioner.process_tasks(list_of_tasks)

    expected_run_calls = [
        call('mktemp'),
        call('mkdir -p {0}'.format('/tmp')),
        call('{0}'.format('/tmp/whatever')),
    ]
    expected_put_calls = [
        call(src, '/tmp/whatever', mode=0500, use_sudo=False),
    ]
    expected_sudo_calls = [
        call('rm {0}'.format('/tmp/whatever'), warn_only=True),
    ]

    assert fabric.operations.put.mock_calls == expected_put_calls
    assert fabric.operations.run.mock_calls == expected_run_calls
    assert fabric.operations.sudo.mock_calls == expected_sudo_calls
