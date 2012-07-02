from dexy.dexy_filter import DexyFilter
import pexpect
import time

class PJSUACallFilter(DexyFilter):
    """
    Pass scripts like:

        call sip:asdf@10.3.2.100
        send 1
        sleep 6
        send 3
        hangup

    to this filter and pjsua will initiate and record the call.

    Step values may be one of

    call <uri> - Place a call to a SIP URI (call sip:example@192.168.0.1:5060)
    send <digits> - Send a DTMF digit or digits to the call (send 1), (send 1234)
    sleep <seconds> - Wait the requested number of seconds (sleep 5)
    hangup - Hang up the call (hangup)

    TBD - framework-specific log capturing and sync'd playback of logs and audio
    """

    ALIASES = ['pjsua']
    INPUT_EXTENSIONS = [".txt", ".pjsua"]
    OUTPUT_EXTENSIONS = [".wav", ".mp3"]
    BINARY = True
    FINAL = True

    def process_step(self, step):
        """
        Send the given command to the call described in "step"
        """
        if step == 'hangup':
            self.child.sendline('ha')
            self.child.expect("\nBYE [^\n]+ SIP/2.0")
            self.log.debug(self.child.before)
            self.log.debug(self.child.after)
        else:
            cmd, arg = step.split(' ')
            if cmd == 'call':
                self.child.sendline('m')
                self.child.expect("\nMake call: ")
                self.log.debug(self.child.before)
                self.log.debug(self.child.after)
                self.child.sendline(arg)
                # The next 3 lines ensure that the call is established successfully.
                # FIXME: Error handling?
                self.child.expect("\nSIP/2.0 200 OK")
                self.log.debug(self.child.before)
                self.log.debug(self.child.after)
                self.child.expect("\nACK")
                self.log.debug(self.child.before)
                self.log.debug(self.child.after)
                self.child.expect("\n--end msg--")
                self.log.debug(self.child.before)
                self.log.debug(self.child.after)
            elif cmd == 'send':
                self.child.sendline('#')
                self.child.expect("\nDTMF strings to send")
                self.log.debug(self.child.before)
                self.log.debug(self.child.after)
                self.child.sendline(arg)
                self.child.expect("\nDTMF digits enqueued for transmission")
                self.log.debug(self.child.before)
                self.log.debug(self.child.after)
            elif cmd == 'sleep':
                time.sleep(int(arg))
            else:
                raise Exception("Unknown step: %s" % cmd)

    def process(self):
        self.child = None

        pjsua_config_artifact = None
        for key, input_artifact in self.artifact.inputs().iteritems():
            if "pjsua.config" in key:
                pjsua_config_artifact = input_artifact

        try:
            if pjsua_config_artifact:
                cmd = "pjsua --rec-file %s --auto-rec --null-audio --config-file=%s" % (self.artifact.filepath(), pjsua_config_artifact.canonical_filename())
            else:
                cmd = "pjsua --rec-file %s --auto-rec --null-audio" % self.artifact.filepath()

            self.log.debug(cmd)
            self.child = pexpect.spawn(cmd)

            # The initial prompt
            self.child.expect("\n>>> ")
            self.log.debug(self.child.before)
            self.log.debug(self.child.after)

            for step in self.artifact.input_text().splitlines():
                self.log.debug("Sending command '%s'" % step)
                self.process_step(step)

            # Terminate the session
            self.child.sendline('q')
            self.child.expect(pexpect.EOF)
        except Exception as e:
            print "Exception!"
            print str(self.child)
            raise e
