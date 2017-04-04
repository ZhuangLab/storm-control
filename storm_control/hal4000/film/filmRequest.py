#!/usr/bin/env python
"""
The filmRequest object.

Hazen 04/17
"""

class FilmRequest(object):

    def __init__(self,
                 basename = None,
                 frames = 0,
                 overwrite = False,
                 tcp_request = False,
                 **kwds):
        super().__init__(**kwds)

        assert(isinstance(frames, int))
        assert(isinstance(overwrite, bool))
        assert(isinstance(tcp_request, bool))

        # The basename to use, if this is None then film.film will figure
        # out what basename to use.
        self.basename = basename
        
        # Length of the film in frames. This is only relevant for TCP
        # requested movies.
        self.frames = frames

        # Whether or not to prompt the user if the filename already exists.
        self.overwrite = overwrite

        # Whether the request came from the record button of via TCP.
        self.tcp_request = tcp_request

    def getBasename(self):
        return self.basename

    def getFiletype(self):
        return self.filetype
        
    def getFrames(self):
        return self.frames

    def hasFilename(self):
        return self.filename is not None

    def isTCPRequest(self):
        return self.tcp_request
        
    def overwriteOk(self):
        return self.overwrite
