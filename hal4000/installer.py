#
# Installs all the necessary files (that might get
# changed as development proceeds) for the HAL-9000
# executable into the target directory.
#
# Hazen 4/09
#

import os
import shutil
import sys
import types

hal_files = ["hal-4000.py",
             "hal-4000.bat",
             "illuminationControl.py",
             "focusLock.py",
             "spotCounter.py",
             "stageControl.py",
#             "settings_default.xml",
#             "shutters_default.xml",
             "splash.png",
             "tcpControl.py",
             "andor/__init__.py",
             "andor/andorcontroller.py",
             "andor/format_converters.dll",
             "andor/format_converters.c",
             "andor/formatconverters.py",
             "camera/__init__.py",
             "camera/andorCameraControl.py",
             "camera/andorCameraWidget.py",
             "camera/cameraControl.py",
             "camera/cameraDisplay.py",
             "camera/cameraParams.py",
             "camera/noneCameraControl.py",
             "camera/noneCameraWidget.py",
             "coherent/__init__.py",
             "coherent/cube.py",
             "coherent/cube405.py",
             "coherent/cube445.py",
             "coherent/compass315M.py",
             "coherent/innova70C.py",
             "colorTables/__init__.py",
             "colorTables/colorTables.py",
             "crystalTechnologies/__init__.py",
             "crystalTechnologies/AOTF.py",
             "halLib/__init__.py",
             "halLib/hdebug.py",
             "halLib/imagewriters.py",
             "halLib/parameters.py",
             "halLib/RS232.py",
             "halLib/tiffwriter.py",
             "halLib/uspp/__init__.py",
             "halLib/uspp/SerialPort_darwin.py",
             "halLib/uspp/SerialPort_linux.py",
             "halLib/uspp/SerialPort_win.py",
             "halLib/uspp/uspp.py",
             "focuslock/__init__.py",
             "focuslock/focusLockZ.py",
             "focuslock/focusQuality.py",
             "focuslock/focus_quality.c",
             "focuslock/focus_quality.dll",
             "focuslock/lockDisplayWidgets.py",
             "focuslock/lockModes.py",
             "focuslock/motorStageQPDControl.py",
             "focuslock/noneWidgets.py",
             "focuslock/prism2FocusLockZ.py",
             "focuslock/storm4piFocusLockZ.py",
             "focuslock/stageOffsetControl.py",
             "focuslock/storm3FocusLockZ.py",
             "focuslock/storm4piFocusLockZ.py",
             "illumination/__init__.py",
             "illumination/channelWidgets.py",
             "illumination/commandQueues.py",
             "illumination/illuminationControl.py",
             "illumination/prism2_illumination_control_settings.xml",
             "illumination/prism2IlluminationControl.py",
             "illumination/prism2ShutterControl.py",
             "illumination/shutterControl.py",
             "illumination/storm3_illumination_control_settings.xml",
             "illumination/storm3IlluminationControl.py",
             "illumination/storm3ShutterControl.py",
             "illumination/storm4pi_illumination_control_settings.xml",
             "illumination/storm4piIlluminationControl.py",
             "illumination/storm4piShutterControl.py",
             "joystick/__init__.py",
             "joystick/joystick.py",
             "joystick/prism2JoystickControl.py",
             "joystick/storm3JoystickControl.py",
             "logitech/__init__.py",
             "logitech/gamepad310.py",
             "madCityLabs/__init__.py",
             "madCityLabs/mclController.py",
             "marzhauser/__init__.py",
             "marzhauser/marzhauser.py",
             "miscControl/__init__.py",
             "miscControl/miscControl.py",
             "miscControl/storm3MiscControl.py",
             "nationalInstruments/__init__.py",
             "nationalInstruments/nicontrol.py",
             "newport/__init__.py",
             "newport/SMC100.py",
             "objectFinder/__init__.py",
             "objectFinder/fastObjectFinder.py",
             "objectFinder/MedianCounter.c",
             "objectFinder/MedianCounter.dll",
             "phreshPhotonics/__init__.py",
             "phreshPhotonics/averager.c",
             "phreshPhotonics/averager.dll",
             "phreshPhotonics/phreshQPD.py",             
             "prior/__init__.py",
             "prior/prior.py",
             "progressionControl.py",
             "qtdesigner/__init__.py",
             "qtdesigner/camera-v1.ui",
             "qtdesigner/camera_ui.py",
             "qtdesigner/camera-params-v1.ui",
             "qtdesigner/camera_params_v1.py",
             "qtdesigner/focuslock-v1.ui",
             "qtdesigner/focuslock_ui.py",
             "qtdesigner/hal-4000-v1.ui",
             "qtdesigner/hal4000_ui.py",
             "qtdesigner/illumination-v1.ui",
             "qtdesigner/illumination_v1.py",
             "qtdesigner/storm2-misc.ui",
             "qtdesigner/storm2_misc_ui.py",
             "qtdesigner/storm3-misc.ui",
             "qtdesigner/storm3_misc_ui.py",
             "qtdesigner/progression-v1.ui",
             "qtdesigner/progressionui_v1.py",
             "qtdesigner/spotcounter-v2.ui",
             "qtdesigner/spotcounterui_v1.py",
             "qtdesigner/stage-v1.ui",
             "qtdesigner/stageui_v1.py",
             "qtWidgets/__init__.py",
             "qtWidgets/qtCameraWidget.py",
             "qtWidgets/qtColorGradient.py",
             "qtWidgets/qtParametersBox.py",
             "qtWidgets/qtPowerControlWidget.py",
             "qtWidgets/qtSpotCounter.py",
             "qtWidgets/qtRangeSlider.py",
             "stagecontrol/__init__.py",
             "stagecontrol/prism2StageControl.py",
             "stagecontrol/stageControl.py",
             "stagecontrol/stageThread.py",
             "stagecontrol/storm3StageControl.py",
             "thorlabs/__init__.py",
             "thorlabs/LDC210.py",
             "thorlabs/PDQ80S1.py",
             "thorlabs/TPZ001.py",
             "THUM/__init__.py",
             "THUM/thum.py"]
    

# set target directory.
target = "c:/users/HAL9000/Executable/"
if len(sys.argv) > 1:
    target = sys.argv[1]

print "Installing to :", target


# copy files to target directory.
for file in hal_files:
    orig_file = file
    dest_file = orig_file
    if isinstance(file, types.ListType):
        [orig_file, dest_file] = file
    dest_file = target + dest_file
    if not(os.path.exists(orig_file)):
        print "Can't find:", orig_file
    else:
        print "Copying:", orig_file
        dirname = os.path.dirname(dest_file)
        if (len(dirname) > 0) and not(os.path.exists(dirname)):
            print " Creating:", dirname
            os.mkdir(dirname + "/")
        shutil.copyfile(orig_file, dest_file)

