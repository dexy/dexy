from dexy.filter import Filter
import boto
import dexy.exceptions
import os
import select
import socket
import ssh
import time

class Ec2Batch(Filter):
    ALIASES = ['ec2']
    AMI = 'ami-137bcf7a' # alestic ubuntu ami
    EC2_KEY_DIR = '~/.ec2'
    INPUT_EXTENSIONS = ['.sh']
    INSTANCE_TYPE = 't1.micro'
    OUTPUT_EXTENSIONS = ['.txt']
    SHUTDOWN_BEHAVIOR = 'terminate'
    VALID_SHUTDOWN_BEHAVIORS = ['stop', 'terminate']

    def ami(self):
        return self.args().get('ami', self.AMI)

    def instance_type(self):
        return self.args().get('instance-type', self.INSTANCE_TYPE)

    def shutdown_behavior(self):
        behavior = self.args().get('shutdown-behavior', self.SHUTDOWN_BEHAVIOR)
        if not behavior in self.VALID_SHUTDOWN_BEHAVIORS:
            msg = "Specified shutdown behavior '%s' not available, choose from %s"
            args = (behavior, ", ".join(self.VALID_SHUTDOWN_BEHAVIORS))
            raise dexy.exceptions.UserFeedback(msg % args)
        return behavior

    def ec2_keypair_name(self):
        # TODO specify in the other normal ways
        keypair_name = os.getenv('EC2_KEYPAIR_NAME')
        if not keypair_name:
            raise Exception("no EC2_KEYPAIR_NAME defined")
        return keypair_name

    def ssh_key_filepath(self):
        # TODO allow specifying manually also
        return os.path.expanduser("~/.ec2/%s.pem" % self.ec2_keypair_name())

    def username(self):
        """
        Return the username to be used to ssh into the instance.
        """
        return 'ubuntu'

    def read_until_empty(self, channel):
        output = []
        while True:
            r, w, e = select.select([channel], [], [], 10)
            if channel in r:
                x = channel.recv(1024)
                if len(x) == 0:
                    self.log.debug("No content to read! breaking out")
                    break
                else:
                    output.append(x)

                    # log the output so we know what's happening
                    try:
                        u = ("read\n%s" % x).encode("UTF-8")
                        self.log.debug(u)
                    except UnicodeDecodeError:
                        pass
            else:
                self.log.debug("done reading")
                break

        self.log.debug("returning")
        return "".join(output)

    def process(self):
        with launch_ec2(self) as (instance, client):
            script = self.input().as_text().splitlines()

            output = []

            transport = client.get_transport()
            sftp = ssh.SFTPClient.from_transport(transport)

            local = self.input().storage.data_file()
            remote = "script"
            self.log.debug("Uploading file %s" % local)
            sftp.put(local, remote)

            channel = transport.open_session()

            channel.exec_command("chmod +x script && ./script")

            while True:
                output.append(self.read_until_empty(channel))

                if channel.exit_status_ready():
                    break

                self.log.debug("pausing to wait for more")
                time.sleep(2)

            output.append(self.read_until_empty(channel))

            status = channel.recv_exit_status()
            self.log.debug("Exit status %s" % status)

        self.output().set_data("".join(output))

class Ec2Interactive(Ec2Batch):
    ALIASES = ['ec2int']
    OUTPUT_EXTENSIONS = ['.sh-session']

    def process(self):
        with launch_ec2(self) as (instance, client):
            script = self.input().as_text().splitlines()

            output = []

#            pty = client.get_pty(self, term='vt100', width=80, height=24)
            chan = client.invoke_shell()
            chan.settimeout(0.0)

            while True:
                r, w, e = select.select([chan], [], [], 10)
                if chan in r:
                    # There is something to read from our ssh session's chan
                    try:
                        x = chan.recv(1024)
                        if len(x) == 0:
                            self.log.debug("Said there was stuff to read but got length 0!")
                        output.append(x)
                        self.log.debug("Received output %s" % x)
                    except socket.timeout:
                        pass

                else:
                    if "$" in x:
                        # Send more script lines
                        if len(script) > 0:
                            line = script.pop(0)
                            self.log.debug("Sending %s" % line)
                            chan.send("%s\n" % line)
                        else:
                            self.log.debug("No more script to send.")
                            break

            chan.close()

        self.output().set_data("".join(output))

class launch_ec2():
    """
    Launch an ec2 instance and connect to it via ssh
    """
    def __init__(self, filter_instance):
        self.fi = filter_instance

    def fix_ssh_transport_logging(self):
        import logging
        ssh_logger = logging.getLogger('ssh.transport')
        ssh_logger.addHandler(logging.getLogger('dexy').handlers[0])

    def __enter__(self):
        self.conn = boto.connect_ec2()

        ami = self.fi.ami()

        args = {
                'instance_initiated_shutdown_behavior' : self.fi.shutdown_behavior(),
                'key_name' : self.fi.ec2_keypair_name(),
                'instance_type' : self.fi.instance_type()
                }

        self.fi.log.debug("Creating instance of %s with args %s" % (ami, args))

        reservation = self.conn.run_instances(ami, **args)
        instance = reservation.instances[0]

        self.fi.log.debug("Created new EC2 instance %s" % instance)

        time.sleep(5)

        while True:
            instance.update()

            if instance.state == 'pending':
                self.fi.log.debug("instance pending")
                # Wait longer for instance to boot up.
                time.sleep(5)

            elif instance.state == 'running':
                self.fi.log.debug("instance running")
                break

            elif instance.state == 'shutting-down':
                raise dexy.exceptions.UserFeedback("Oops! instance shutting down already.")

            elif instance.state == 'terminated':
                raise dexy.exceptions.UserFeedback("Oops! instance terminating already.")

            else:
                raise dexy.exceptions.InternalDexyProblem("unexpected instance state '%s'" % instance.state)

        self.fi.log.debug("Instance running with IP address %s" % instance.ip_address)

        client = ssh.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(ssh.WarningPolicy())

        self.fix_ssh_transport_logging()

        ssh_args = {
                'username' : self.fi.username(),
                'key_filename' : self.fi.ssh_key_filepath()
                }

        self.fi.log.debug("Attempting to connect via ssh using %s" % ssh_args)

        while True:
            try:
                client.connect(instance.ip_address, **ssh_args)
                self.fi.log.debug("Connected via ssh!")
                break
            except socket.error:
                self.fi.log.debug("Can't connect over ssh yet")
                time.sleep(5)

        self._instance = instance
        self._client = client

        return (instance, client)

    def __exit__(self, type, value, traceback):
        self._client.close()
        self._instance.terminate()
