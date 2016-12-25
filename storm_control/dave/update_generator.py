#!/usr/bin/python
#
## @file
#
# Generate HTML for Dave web update & upload it to
# a webserver using the the DAV protocol and the
# tinydav library, available here:
#
# http://code.google.com/p/tinydav/
#
# This is not used.
#
# Hazen 08/11
#

import time
import tinydav

class HTMLUpdate(object):
    def __init__(self, parameters):
        self.directory = parameters.directory
        self.password = parameters.password
        self.port = parameters.server_port
        self.setup_name = parameters.setup_name
        self.server_name = parameters.server_name
        self.username = parameters.username

        self.update_file = parameters.setup_name + ".txt"

    def getTime(self):
        return time.asctime(time.localtime(time.time()))

    def newMovie(self, movie):
        fp = open(self.update_file, "a")
        fp.write("Started movie " + movie.name + " on " + self.getTime() + "\n")
        fp.close()
        #self.updateFileOnServer()

    def start(self):
        fp = open(self.update_file, "w")
        fp.write("Run started on: " + self.getTime() + "\n")
        fp.close()
        #self.updateFileOnServer()

    def stop(self):
        fp = open(self.update_file, "a")
        fp.write("Run stopped on: " + self.getTime() + "\n")
        fp.close()
        #self.updateFileOnServer()

    def updateFileOnServer(self):
        client = tinydav.WebDAVClient(self.server_name, self.port)
        client.setbasicauth(self.username, self.password)

        local = self.update_file
        remote = self.directory + local
        with open(local) as fd:
            print client.put(remote, fd, "text/plain")

