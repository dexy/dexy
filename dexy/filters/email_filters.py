from dexy.filters.api_filters import ApiFilter
from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes
import smtplib

class SendEmailFilter(ApiFilter):
    ALIASES = ['email']
    API_KEY_NAME = 'email'
    API_KEY_KEYS = ["email", "password", "server", "port"]
    INPUT_EXTENSIONS = [".html"]
    OUTPUT_EXTENSIONS = [".txt"]

    def process_text(self, input_text):
        sender = self.read_param('email')
        password = self.read_param('password')
        server = self.read_param('server')
        port = self.read_param('port')

        subject = "Hello from Dexy"
        recipient = "dexyit@gmail.com"

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient


        # TODO convert html to plain text also MIMEText(input_text, 'plain')
        body = MIMEText(input_text, 'html')
        msg.attach(body)

        already_attached = []
        for k, a in self.artifact.inputs().iteritems():
            if (a.final or a.additional) and not (a.key in already_attached):
                path = a.filepath()
                ctype, encoding = mimetypes.guess_type(path)

                if ctype is None or encoding is not None:
                    # No guess could be made, or the file is encoded (compressed), so
                    # use a generic bag-of-bits type.
                    ctype = 'application/octet-stream'

                maintype, subtype = ctype.split('/', 1)

                if maintype == 'text':
                    with open(path) as f:
                       attachment = MIMEText(f.read(), _subtype=subtype)

                elif maintype == 'image':
                    with open(path) as f:
                        attachment = MIMEImage(f.read(), _subtype=subtype)
                        attachment.add_header('Content-ID', "<%s>" % a.canonical_basename())

                elif maintype == 'audio':
                    with open(path) as f:
                        attachment = MIMEAudio(f.read(), _subtype=subtype)

                else:
                    with open(path) as f:
                        attachment = MIMEBase(maintype, subtype)
                        attachment.set_payload(f.read())
                    # Encode the payload using Base64
                    encoders.encode_base64(attachment)

                attachment.add_header('Content-Disposition', 'attachment', filename=a.canonical_basename())
                msg.attach(attachment)
                already_attached.append(a.key)

        if not port:
            if "gmail" in server:
                port = 587
            else:
                port = 25

        msg_string = msg.as_string()

        # send email
        s = smtplib.SMTP(server, port)
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(sender, password)
        s.sendmail(sender, recipient, msg_string)
        s.quit()

        return msg_string
