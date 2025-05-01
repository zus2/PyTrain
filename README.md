# Pybricks Train Controller 

## Overview

The Pybricks Train Controller is a Python-based script designed to enhance train control using asynchronous multitasking. It offers smoother and more lifelike inertia effects, making it ideal for train enthusiasts and LEGO builders.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Instructions](#instructions)
- [Crawl Speed](#setting-crawl-speed)
- [Contribution](#contribution)
- [Acknowledgements](#acknowledgments)

## Features
* Asynchronous speed change and stop commands for inertia effect.
* Customizable speed ramp, including crawl, max, min, acceleration, and granularity (steps).
* Crawl speed calibration adjustable within the program.
* Synced indicator LED for Crawl, Go, Stop, Ready, and Calibrate states.
* Added stop script or hub shutdown using the center button.
* Support for 2 motors and initial compatibility with sensor motors.
* Heartbeat auto-shutdown and user input sanity checks.
* Memorizes crawl speed setting after shutdown.
* Compatible with Technic and City hubs.
* Separate reverse speed limit, which can be set to 0 (e.g., for trams).
* Supports a second hub with the slave hub program.
* Upcoming Feature: Headlights control.
 
## Installation
1. Ensure that your computer supports Bluetooth LE.
2. Open [Pybricks Code](https://code.pybricks.com) in Chrome, Edge (Mac, PC, or Android; not iOS or Safari).
3. Install Pybricks firmware on your LEGO City or Technic hub.
4. You can reinstall the LEGO firmware using the Power Functions app if needed.
5. Connect your motors or lights.
6. Download pytrain.py from this repository.
7. Open the file in Pybricks Code.
8. Connect to your hub using the Bluetooth browser in Pybricks Code.
9. Run pytrain.py in the Pybricks Code editor to load the program onto your hub.
10. To use a second hub install pytrainfollower.py on it 

## Instructions
1. Run pytrain.py from Pybricks Code or turn on your hub and press the start button a second time to start the program.
2. Turn on your LEGO remote control; orange LEDs should light up on the hub and controller.
3. Use the left buttons for motors and the right buttons for lights.
4. Adjust user settings as needed in Pybricks Code including setting the motor directions.
5. Stopping the program: Quickly press the center button.
6. Shutting down the hub: Hold the center button for 2 seconds.

## Setting Crawl Speed
1. Press and hold the left red button until you see a purple light.
2. Adjust speed with the left '+' and '-' buttons until the desired crawl speed is reached.
3. Press the left center button to store the setting.
4. The crawl speed is saved and will load automatically until reset.

## Contribution
We welcome contributions! To contribute:
1. Fork the repository and create a new branch for your changes.
2. Submit a pull request with a clear description of the changes.
3. Feel free to open issues for bugs or feature requests.

## Acknowledgments
Special thanks to:
* Lok24: [Control Your Trains with Pybricks](https://www.eurobricks.com/forum/index.php?/forums/topic/187081-control-your-trains-without-smart-device-with-pybricks/)
* @mpersand: [PyBricks Train Motor Control Script](https://github.com/and-ampersand-and/PyBricks-Train-Motor-Control-Script)


