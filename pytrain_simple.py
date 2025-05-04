# pytrain_simple.py
# v0.3
# https://github.com/zus2/PyTrain
#
# A simple Pybricks train motor controller - with a great controller handler 
# for extra precise playability. Easy to customise simple logic.
# Auto detects all hubs and up to 2 motors, DC or Technic
#
# Tested with Pybricks v3.6.1 (Pybricks Code v2.6.0)
#
# © 2025 Paul Walsh
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
# PARTICULAR PURPOSE AND NONINFRINGEMENT. See LICENCE in the official repository.
#

"""
Instructions:
Change the motor directions below to suit your train
Motor detection automatic ( 1 or 2 in port A and/or B)
Use left +/- and left center to control the train
Red light = stop , amber = ready , green = go and cyan = crawl 
You can change the crawl speed below (DCMIN) and max (DCMAX)
Center red button once: stop the program and train instantly
Center red button hold 1 second: shut down the hub and controller
Run the program from your computer, or the hub (switch remote on promptly)
"""

# ----------
# --- User defined values
# ----------

DCMIN = 20          # min dc power (%) to move the train - crawl speed
DCMAX = 80          # max dc power (%) to keep train upright
DIRMOTORA = -1      # Hub motor A Direction clockwise 1 or -1
DIRMOTORB = 1       # Hub motor B Direction clockwise 1 or -1
STOP_DELAY = 500    # short pause when braking to zero DC

# ----------
# --- Main programme
# ----Do not change anything below here unless you are a competent programmer
# ----------

from pybricks.hubs import ThisHub
from pybricks.pupdevices import DCMotor, Remote, Motor
from pybricks.parameters import Button, Color, Direction, Port
from pybricks.tools import wait, StopWatch, run_task
from pybricks.iodevices import PUPDevice

def getmotors(motor):
    """
    Check ports and auto add DC or Technic motors

    Args:
        motor(Motor()) - the motor object 
    """
    for x in (0,1):

        port = (Port.A,Port.B)[x]

        try:
            device = PUPDevice(port)
            id = device.info()["id"]
            print("device",id,"on",x)

            if device.info()["id"] < 3:
                print("DC motor on",port)
                motor.append(DCMotor(port,motordirection[x]))

            else:
                print("Motor on",port)
                motor.append(Motor(port,motordirection[x]))

        except OSError as err:
            print("no device on",port)
            motor.append("")

def controller():
    INITIAL_DELAY = 350
    REPEAT_DELAY = 100
    watch = StopWatch()
    dc = 0

    while True:
        
        #print(hub.battery.current())
        
        pressed = ()

        # Wait until a button is pressed.
        while not pressed:
            pressed = remote.buttons.pressed()
            
        print(pressed)
        dc = drive(pressed, dc)

        # Wait until all buttons are released
        # Or repeat if held down longer than INITIAL_DELAY
        watch.reset()
        while pressed:
            if watch.time() > INITIAL_DELAY:
                print(pressed)
                dc = drive(pressed, dc)
                wait(REPEAT_DELAY)
            pressed = remote.buttons.pressed()
                       
def drive(p, dc):
    pressed = p

    if Button.LEFT_PLUS in pressed:
            if dc == 0: dc = DCMIN
            elif dc < DCMAX: dc += 2
            if abs(dc) < DCMIN*0.7: dc = 0
    elif Button.LEFT_MINUS in pressed:
            if dc == 0: dc = -DCMIN
            elif dc > -DCMAX: dc -= 2
            if abs(dc) < DCMIN*0.7: dc = 0
    elif Button.LEFT in pressed:
            hub.light.on(Color.RED*0.5)
            """
            # hard stop
            for m in motor:
                if (m): m.stop()
            dc = 0
            """
            # gentle stop
            while abs(dc) > 10:
                dc = dc - 10 if dc > 0 else dc + 10
                for m in motor:
                    if (m): m.dc(dc)
                print(dc)
                wait(150)
            dc = 0
        
    elif Button.CENTER in pressed:
                # press once to stop the train AND the programme
                # hold 2 secs to shutdown hub
                print("remote center")
                for m in motor:
                    if (m): m.dc(0)
                count = 0
                while Button.CENTER in pressed:
                    pressed = remote.buttons.pressed()
                    count+=1
                    if (count == 10): # 1 seconds ( plus brake in stop() )
                        print("Shutting down hub ...")
                        wait(100)
                        hub.system.shutdown() 
                    wait(100)
                raise SystemExit("Closing program..")
    
    # send drive command to motors 1 and 2
    for m in motor:
        if (m): m.dc(dc)

    if dc == 0:
        hub.light.on(Color.RED*0.5)
        # hard coded delay for added UX
        wait(STOP_DELAY)
        # orange for ready to move
        hub.light.on(Color.ORANGE*0.4)
    elif abs(dc) == DCMIN:
        hub.light.on(Color.CYAN*0.5)
    else:
        hub.light.on(Color.GREEN*0.4)

    print(dc)
    return dc

# --- set up hub and remote
hub = ThisHub(broadcast_channel=None)

# --- clear terminal 
print("\x1b[H\x1b[2J", end="")
print("Pytrain Simple - Train Controller")
print(hub.system.name())
print("---\nCell voltage:",round(hub.battery.voltage()/6000,2))

# --- set up remote 
print ("Looking for remote ..")
try:
    remote = Remote(timeout=15000)
except OSError as ex:
    print ("Not found - shutting down ..")
    wait(1000)
    hub.system.shutdown() 

# --- define  motors - max 2 for CityHub
motor = []
motordirectionA = Direction.CLOCKWISE if DIRMOTORA == 1 else Direction.COUNTERCLOCKWISE
motordirectionB = Direction.CLOCKWISE if DIRMOTORB == 1 else Direction.COUNTERCLOCKWISE
motordirection = (motordirectionA , motordirectionB)
getmotors(motor)
###

# my new controller 
run_task(controller())
