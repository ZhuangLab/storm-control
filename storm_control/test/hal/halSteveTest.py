#!/usr/bin/env python
"""
Run HAL for testing Steve.

Hazen 11/18
"""
import os
import subprocess
import sys
import threading
import time
import traceback


from PyQt5 import QtWidgets

import storm_control.hal4000.hal4000 as hal4000
import storm_control.sc_library.hdebug as hdebug
import storm_control.sc_library.parameters as params
import storm_control.test as test


class HalSteveTest(object):

    def __init__(self, config_xml = None):
        self.config_xml = config_xml
        self.error_msg = ""
        self.process = None
        self.thread = None

    def run(self):
        cmd_line = ["python",
                    "hal/halSteveTest.py",
                    self.config_xml]
        def target():
            try:
                self.process = subprocess.Popen(cmd_line)
            except:
                self.error_msg = traceback.format_exc()
                
        self.thread = threading.Thread(target = target)
        self.thread.start()
        time.sleep(1.0)

    def stop(self):
        self.process.terminate()
        print(self.error_msg)


if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)
    config = params.config(test.halXmlFilePathAndName(sys.argv[1]))
    hdebug.startLogging(test.logDirectory(), "hal4000")
    hal = hal4000.HalCore(config = config,
                          show_gui = True)
    app.exec_()
    app = None

    
