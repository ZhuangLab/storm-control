#!/usr/bin/env python
"""
The filmSettings object.

Hazen 04/17
"""

class FilmSettings(object):

    def __init__(self,
                 acq_mode = "fixed_length",
                 basename = "",
                 filetype = "",
                 film_length = 0,
                 overwrite = True,
                 pixel_size = 1.0,
                 run_shutters = False,
                 save_film = True,
                 tcp_request = False,
                 **kwds):
    
        super().__init__(**kwds)

        assert(acq_mode in ["run_till_abort", "fixed_length"])
        assert(isinstance(basename, str))
        assert(isinstance(filetype, str))
        assert(isinstance(film_length, int))
        assert(isinstance(overwrite, bool))
        assert(isinstance(run_shutters, bool))
        assert(isinstance(save_film, bool))
        assert(isinstance(tcp_request, bool))

        # Either "run_till_abort" or "fixed_length"
        self.acq_mode = acq_mode

        # The base filename. Each movie request will generate several files.
        self.basename = basename

        # The movie file type, i.e. '.dax', '.tif', etc.
        self.filetype = filetype

        # The number of frames in the movie (only relevant for fixed length).
        self.film_length = film_length

        # Whether or not to overwrite an existing file. If this is not True
        # and the file already exists HAL is expected to crash.
        self.overwrite = overwrite
        
        # Whether or not to run the shutters.
        self.run_shutters = run_shutters

        # Whether or not the film is actually being saved.
        self.save_film = save_film

        # Whether the film request came from the record button or TCP.
        self.tcp_request = tcp_request

    def getBasename(self):
        return self.basename

    def getFiletype(self):
        return self.filetype

    def getFilmLength(self):
        return self.film_length

    def getPixelSize(self):
        return self.pixel_size
    
    def isFixedLength(self):
        return (self.acq_mode == "fixed_length")

    def isSaved(self):
        return self.save_film
    
    def isTCPRequest(self):
        return self.tcp_request

    def overwriteOk(self):
        return self.overwrite
    
    def runShutters(self):
        return self.run_shutters

    def saveFilm(self):
        return self.save_film
        
    def setPixelSize(self, new_size):
        self.pixel_size = new_size

