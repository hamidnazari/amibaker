from fabric.api import run, env, settings, hide


class Provisioner:
    def __init__(self, ec2, **kwargs):
        self.__ec2 = ec2
        self.__quiet = kwargs.get('quiet', False)

    def provision(self, script):
        # host to connect to
        env.host_string = self.__ec2.get_hostname()

        # ssh user to be used for this session
        env.user = self.__ec2.get_username()

        # no passwords available, use private key
        env.password = None

        # use ~/.ssh/config if avaialble
        env.use_ssh_config = True

        # disconnect right after work is done
        env.eagerly_disconnect = True

        # no need to check fingerprint
        env.skip_bad_hosts = True

        # number of ssh attemps
        env.connection_attempts = 6

        # how many seconds until considered failed attempt
        env.timeout = 15

        env.colorize_errors = True

        if self.__quiet:
            settings(hide('warnings', 'running', 'stdout', 'stderr'))

        run(script)
