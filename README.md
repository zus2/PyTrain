## Pybricks Train Controller script using asynchronous multitasking for smoother more lifelike inertia effects

### Features:

Asynchronous speed change and stop commands for inertia effect 

Customisable speed ramp crawl, max, min, accel and granularity (steps)

Crawl speed calibration adjustable in programme 

Synced indicator led for Crawl, Go, Stop, Ready, Calibrate 

Added stop script or shutdown hub in programme using center button

Support for 2 motors and initial support for sensor motors

Heartbeat auto-shutdown and user input sanity checks

Memorises crawl speed setting after shutdown

Support for Technic and City hubs 

Separate reverse speed limit which can be 0 for eg. trams

To add: broadcast to second hub , headlights control

Comments welcome, particularly the asynchronous logic and functionality. I am a new to Python, Pybricks and Multitasking !

### Instructions

Your computer needs to support Bluetooth LE

Go to code.pybricks.com ("code") using Chrome or Android ( not iOS or Safari )

Install Pybricks on your City or Technic hub

( You can reinstall the Lego firmware using the Power Functions app )

Connect your motors or lights

Download pytrain.py in code

Connect to your hub in the bluetooth browser in code

Run pytrain.py in code - this loads the program onto your hub

Turn on your Lego remote control - you should see orange leds on the hub and controller

Use the left buttons for motors and the right buttons for lights

Change the user settings if you wish or if your motors are turning the wrong way

Press the center button:
* Quickly to stop the program
* For 2 seconds to shutdown the hub

To set the crawl speed:
*Press and hold left red button until you see a purple light
* Press left plus until you have the minimum speed to move
* Press the left centre button again to store
* The setting is stored on the hub and will be loaded each time until you reset it

### Thanks to: 

Lok24 https://www.eurobricks.com/forum/forums/topic/187081-control-your-trains-without-smart-device-with-pybricks/

@mpersand https://github.com/and-ampersand-and/PyBricks-Train-Motor-Control-Script?files=1


