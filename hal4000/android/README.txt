
This an Android application that can interact with HAL via 
Bluetooth. To get this to work you will need to install
pyBluez and either side load the TMA03.apk app onto your 
Android device, or import the project into the Eclipse IDE 
with built-in ADT (Android Developer Tools) and then use
Eclipse to install and run the application on your device.

Requires:
Android SDK Version 19 (Android 4.4, KitKat).

Dependencies:
pyBluez - https://code.google.com/p/pybluez/
ADT - https://developer.android.com/sdk/index.html?hl=sk

Notes:
1. As of 03/14/2014 this has only been tested with a Nexus 4
   phone and Bluetooth protocol v2 and above.

2. Images are sent to the device as 256x256 compressed JPEGs
   at about 10Hz (depending on device speed). You may need 
   a reasonably powerful device to handle decompressing and 
   re-scaling the images to display them on the device 
   screen.

3. Controls:
   a. Tap the "O" to start/stop recording.
   b. Tap the "+" or "-" to move the Z stage up/down.
   c. Tap on the image display to move the XY stage a single
      step.
   d. Drag on the image display to move the XY stage 
      continuously (this is similar to the screen drag mode).
   e. Tap in the center of the image to change the drag
      multiplier.
   f. Tap on the focus lock sum/offset display to get images
      from the focus lock instead of the camera.

