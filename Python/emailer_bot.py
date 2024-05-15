import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate


emailerObj	= smtplib.SMTP("10.7.209.18:25") #Intel's private SMTP IP.
sender 		= 'papai@intel.com'
receivers	= ['arkaprabho.adhikary@intel.com']


files 		= ['/nfs/site/disks/w.aadhika1.673/isoperf_Results/maia_idecode_PDK005_160CH_0.49v_SUL_normSynth_noZ1hvtsvt_WW08.1_Results/*']


# Message Setup

SUBJECT			= "Test Code"
MSG_BODY		= "Hi! This is a test message from Python."


msg 			= MIMEMultipart()
msg['From']		= sender
msg['To']		= COMMASPACE.join(receivers)
msg['Date']		= formatdate(localtime = True)
msg['Subject']	= SUBJECT

msg.attach(MIMEText(MSG_BODY))

# File Attachment

for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)


# Transmission

				
emailerObj.sendmail(sender, receivers, msg.as_string())
emailerObj.close()
