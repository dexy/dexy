from dexy.filter import Filter
import dexy.exceptions
import select
import socket
import time

try:
    import ssh
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class SshBatch(Filter):
    ALIASES = ['ssh']
    OUTPUT_EXTENSIONS = ['.txt', '.sh-session']

    @classmethod
    def is_active(klass):
        return AVAILABLE

    def setup_client(self):
        client = ssh.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(ssh.WarningPolicy())

        # fix ssh.transport logging so users don't see it
        import logging
        ssh_logger = logging.getLogger('ssh.transport')
        ssh_logger.addHandler(logging.getLogger('dexy').handlers[0])

        return client

    def ssh_key_filepath(self):
        if self.args().get('key-filepath'):
            return self.args().get('key-filepath')
        elif self.pre_attrs().get('key-filepath'):
            return self.pre_attrs()['key-filepath']
        else:
            raise dexy.exceptions.UserFeedback("No ssh key filepath!")

    def username(self):
        """
        Return the username to be used to ssh into the instance.
        """
        if self.args().get('username'):
            return self.args()['username']
        else:
            # what is best default? user's own name?
            return 'ubuntu'

    def pre_attrs(self):
        return self.artifact.wrapper.pre_attrs

    def hostname(self):
        hostname = self.pre_attrs().get('ip-address', '127.0.0.1')
        self.log.debug("hostname is %s" % hostname)
        return hostname

    def ssh_args(self):
        ssh_args = {
                'username' : self.username(),
                'key_filename' : self.ssh_key_filepath()
                }

        self.log.debug("ssh args are %s" % ssh_args)
        return ssh_args

    def connect(self):
        client = self.setup_client()

        hostname = self.hostname()
        ssh_args = self.ssh_args()

        while True:
            try:
                client.connect(hostname, **ssh_args)
                self.log.debug("Connected via ssh!")
                break
            except socket.error:
                self.log.debug("Can't connect over ssh yet")
                time.sleep(5)

        transport = client.get_transport()
        return (client, transport)

    def read_until_empty(self, channel):
        output = []
        while True:
            r, w, e = select.select([channel], [], [channel], 10)
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
        client, transport = self.connect()

        # Upload script via SFTP
        sftp = ssh.SFTPClient.from_transport(transport)
        local = self.input().storage.data_file()
        remote = "script"
        self.log.debug("Uploading file %s" % local)
        sftp.put(local, remote)

        # Run script and retrieve output
        channel = transport.open_session()
        channel.set_combine_stderr(True)
        channel.exec_command("chmod +x script && ./script")

        output = []
        while True:
            if channel.exit_status_ready():
                break

            output.append(self.read_until_empty(channel))
            time.sleep(2)

        # Get any remaining output
        output.append(self.read_until_empty(channel))

        # Store output
        self.output().set_data("".join(output))

        # Check and log exit status
        status = channel.recv_exit_status()
        self.log.debug("Exit status %s" % status)

#class SshInteractive(SshBatch):
#    ALIASES = ['sshint']
#    OUTPUT_EXTENSIONS = ['.sh-session']
#
#    def process(self):
#        with launch_ec2(self) as (instance, client):
#            script = self.input().as_text().splitlines()
#
#            output = []
#
##            pty = client.get_pty(self, term='vt100', width=80, height=24)
#            chan = client.invoke_shell()
#            chan.settimeout(0.0)
#
#            while True:
#                r, w, e = select.select([chan], [], [], 10)
#                if chan in r:
#                    # There is something to read from our ssh session's chan
#                    try:
#                        x = chan.recv(1024)
#                        if len(x) == 0:
#                            self.log.debug("Said there was stuff to read but got length 0!")
#                        output.append(x)
#                        self.log.debug("Received output %s" % x)
#                    except socket.timeout:
#                        pass
#
#                else:
#                    if "$" in x:
#                        # Send more script lines
#                        if len(script) > 0:
#                            line = script.pop(0)
#                            self.log.debug("Sending %s" % line)
#                            chan.send("%s\n" % line)
#                        else:
#                            self.log.debug("No more script to send.")
#                            break
#
#            chan.close()
#
#        self.output().set_data("".join(output))
