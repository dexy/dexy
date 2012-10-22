import dexy.doc
import dexy.exceptions
import dexy.task
import os
import time

try:
    import boto
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class EC2Launch(dexy.task.Task):
    ALIASES = ['ec2']
    AMI = 'ami-3d4ff254' # alestic ubuntu 12.04 EBS ami
    EC2_KEY_DIR = '~/.ec2'
    INSTANCE_TYPE = 't1.micro'
    OUTPUT_EXTENSIONS = ['.json']
    SHUTDOWN_BEHAVIOR = 'terminate'
    VALID_SHUTDOWN_BEHAVIORS = ['stop', 'terminate']

    @classmethod
    def is_active(klass):
        return AVAILABLE

    def setup(self):
        self.set_log()

    def ami(self):
        return self.args.get('ami', self.AMI)

    def instance_type(self):
        return self.args.get('instance_type', self.INSTANCE_TYPE)

    def shutdown_behavior(self):
        behavior = self.args.get('shutdown_behavior', self.SHUTDOWN_BEHAVIOR)
        if not behavior in self.VALID_SHUTDOWN_BEHAVIORS:
            msg = "Specified shutdown behavior '%s' not available, choose from %s"
            args = (behavior, ", ".join(self.VALID_SHUTDOWN_BEHAVIORS))
            raise dexy.exceptions.UserFeedback(msg % args)
        return behavior

    def ec2_keypair_name(self):
        if self.args.get('ec2_keypair'):
            self.log.debug("Reading ec2 keypair name from args")
            ec2_keypair_name = self.args.get('ec2_keypair')
        else:
            self.log.debug("Reading ec2 keypair name from EC2_KEYPAIR_NAME environment variable")
            ec2_keypair_name = os.getenv('EC2_KEYPAIR_NAME')

        if not ec2_keypair_name:
            raise dexy.exceptions.UserFeedback("no ec2 keypair name defined")

        return ec2_keypair_name

    def ec2_keypair_filepath(self):
        return os.path.expanduser("~/.ec2/%s.pem" % self.ec2_keypair_name())

    def pre(self, *args, **kwargs):
        try:
            conn = boto.connect_ec2()
        except Exception as e:
            if e.__class__.__name__.startswith("boto"):
                raise dexy.exceptions.UserFeedback(e.message)

        ami = self.ami()

        args = {
                'instance_initiated_shutdown_behavior' : self.shutdown_behavior(),
                'key_name' : self.ec2_keypair_name(),
                'instance_type' : self.instance_type()
                }

        self.log.debug("Creating instance of %s with args %s" % (ami, args))

        reservation = conn.run_instances(ami, **args)
        instance = reservation.instances[0]

        self.log.debug("Created new EC2 instance %s" % instance)

        time.sleep(5)

        while True:
            instance.update()

            if instance.state == 'pending':
                self.log.debug("instance pending")
                # Wait longer for instance to boot up.
                time.sleep(5)

            elif instance.state == 'running':
                self.log.debug("instance running")
                break

            elif instance.state == 'shutting-down':
                raise dexy.exceptions.UserFeedback("Oops! instance shutting down already.")

            elif instance.state == 'terminated':
                raise dexy.exceptions.UserFeedback("Oops! instance terminated already.")

            else:
                raise dexy.exceptions.InternalDexyProblem("unexpected instance state '%s'" % instance.state)

        self.log.debug("Instance running with IP address %s" % instance.ip_address)

        self._instance = instance

        # TODO merge with existing pre attrs? Restore old when finished?
        self.wrapper.pre_attrs = {
                'ip-address' : instance.ip_address,
                'key-filepath' : self.ec2_keypair_filepath()
                }

    def post(self, *args, **kwargs):
        self.log.debug("About to terminate instance %s" % self._instance)
        self._instance.terminate()
