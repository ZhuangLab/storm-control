#!/usr/bin/python
#
## @file
#
# Handles notifications (by e-mail) about the system status.
#
# Hazen 06/13
#

from email.mime.text import MIMEText
import smtplib
import traceback

## Notifier
#
# The notification class.
#
class Notifier:

    ## __init__
    #
    # @param smtp_server The SMTP server name.
    # @param from_address The from address to use.
    # @param from_password The password for this e-mail account.
    # @param to_address The address to send notification e-mails to.
    #
    def __init__(self, smtp_server, from_address, from_password, to_address):
        self.from_address = str(from_address)
        self.from_password = str(from_password)
        self.smtp_server = str(smtp_server)
        self.to_address = str(to_address)
        self.email_port = 587 # Port for gmail

        # Trim whitespace from email addresses
        self.to_address_list = self.to_address.split(',')
        for [index, address] in enumerate(self.to_address_list):
            self.to_address_list[index] = address.strip()

    ## checkNoEmptyField
    #
    # @return True/False all the necessary fields to send e-mail have been filled in.
    #
    def checkNoEmptyField(self):
        if (self.from_address == ""):
            return False
        if (self.from_password == ""):
            return False
        if (self.smtp_server == ""):
            return False
        if (self.to_address == ""):
            return False
        return True

    ## sendMessage
    #
    # Sends a e-mail message.
    #
    # @param subject_text The subject of the e-mail.
    # @param message_text The message of the e-mail.
    #
    def sendMessage(self, subject_text, message_text):
        if (self.checkNoEmptyField()):
            try:
                msg = MIMEText(str(message_text))
                msg['Subject'] = str(subject_text)
                msg['From'] = self.from_address
                msg['To'] = self.to_address
            
                server = smtplib.SMTP(self.smtp_server, self.email_port)
                server.starttls()
                server.login(self.from_address, self.from_password)
                server.sendmail(self.from_address, self.to_address_list, msg.as_string())
                server.quit()
                
            except:
                print "Failed to send e-mail."
                print traceback.format_exc()
        else:
            print "One or more notification fields are empty."

    ## setFields
    #
    # Sets the fields of the notifier.
    #
    # @param smtp_server The SMTP server name.
    # @param from_address The from address to use.
    # @param from_password The password for this e-mail account.
    # @param to_address The address to send notification e-mails to.
    #
    def setFields(self, smtp_server, from_address, from_password, to_address):
        self.from_address = str(from_address)
        self.from_password = str(from_password)
        self.smtp_server = str(smtp_server)
        self.to_address = str(to_address)

        # Trim whitespace from email addresses
        self.to_address_list = self.to_address.split(',')
        for [index, address] in enumerate(self.to_address_list):
            self.to_address_list[index] = address.strip()
            


#
# Testing
# 

if __name__ == "__main__":
    import sys

    if (len(sys.argv) != 5):
        print "usage: <smtp_server> <from_address> <from_password> <to_address>"
        exit()

    noti = Notifier(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    noti.sendMessage("Hello World", "Hello World")

#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
