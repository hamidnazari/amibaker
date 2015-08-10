from fabric.api import env, settings, hide
from fabric.operations import run, put, sudo
from os import path


class Provisioner(object):
    PERMITTED_OPERATIONS = ['exec', 'copy']

    def __init__(self, ec2, **kwargs):
        self.__ec2 = ec2
        self.__quiet = kwargs.get('quiet', False)

    def provision(self, tasks):
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
        env.disable_known_hosts = True

        # TODO: Make this configurable through recipe YAML
        # number of ssh attempts
        env.connection_attempts = 10

        # TODO: Make this configurable through recipe YAML
        # how many seconds until considered failed attempt
        env.timeout = 30

        env.colorize_errors = True
        self.process_tasks(tasks)

    def process_tasks(self, tasks):
        for task in tasks:
            for operation, jobs in task.iteritems():
                assert operation in self.PERMITTED_OPERATIONS
                assert isinstance(jobs, list)  # TODO: support listifying attributes found at same level as operation

                for job in jobs:
                    getattr(self, '_{0}'.format(operation))(**job)


    def _exec(self, *args, **kwargs):
        # run(script, warn_only=True)
        print args
        print kwargs
        pass

    def _copy(self, src, dest, mode=0600):
        opts = {'use_sudo': True}

        dest_dir = path.dirname(dest)
        sudo("mkdir -p %s" % dest_dir)

        if mode:
            opts['mode'] = mode

        put(src, dest, **opts)
