from fabric.api import env, settings, hide
from fabric.operations import run, put, sudo
from os import path

class Provisioner:
    def __init__(self, ec2, **kwargs):
        self.__ec2 = ec2
        self.__quiet = kwargs.get('quiet', False)

    def provision(self, copy=None, script=None):
        if not (copy or script):
            return False

        if self.__quiet:
            settings(hide('warnings', 'running', 'stdout', 'stderr'))

        # host to connect to
        env.host_string = self.__ec2.get_hostname()

        # ssh user to be used for this session
        env.user = self.__ec2.get_username()

        # no passwords available, use private key
        env.password = None

        # use ~/.ssh/config if available
        env.use_ssh_config = True

        # disconnect right after work is done
        env.eagerly_disconnect = True

        # no need to check fingerprint
        env.skip_bad_hosts = True

        # number of ssh attempts
        env.connection_attempts = 6

        # how many seconds until considered failed attempt
        env.timeout = 15

        env.colorize_errors = True

        if isinstance(copy, list):
            self.__copy(copy)

        if script:
            self.__run(script)

    def __run(self, script):
        run(script)

    def __copy(self, copy):
        for f in copy:
            opts = {
                'use_sudo': True
            }

            to_dir = path.dirname(f['to'])
            sudo("mkdir -p %s" % to_dir)

            mode = f.get('mode')
            if mode:
                opts['mode'] = mode

            put(f['from'], f['to'], **opts)
