# pytrain_simple
# v0.1


# ----------
# --- User defined values
# ----------

# most of these for future use only
dcsteps = 12        # number of +/- button presses to reach full forward speed: -s to +s (range 5 - 100)
dcmin = 20          # min dc power (%) to move the train - can be changed in program ! ( range 10 - 40 )
dcmax = 80          # max forward dc power (%) to keep the train stay on the track ( range 41 - 90 (hard code limit) )
dcmaxr = 50         # max reverse dc power (%) ( range 0 - 90 (hard code limit)) - set to 0 for trams ?
dcacc = 20          # acceleration - 1 (aggressive) - 80 (gentle) - try 20
BRAKE = 600         # ms delay after stopping to prevent overruns ( range 1 - 2000 ms )
BROADCASTCHANNEL = None  # channel for 2nd hub ( 0 - 255 ) Use None if no other hub consumes power !
INACTIVITY = 5      # mins before shutdown if no button pressed and train stationary
dirmotorA = -1      # Hub motor A Direction clockwise 1 or -1
dirmotorB = 1       # Hub motor B Direction clockwise 1 or -1
OUTPUT = False      # set to true to show extra info for debugging

from pybricks.hubs import ThisHub
from pybricks.pupdevices import DCMotor, Light, Remote, Motor
from pybricks.parameters import Button, Color, Direction, Port, Side, Stop
from pybricks.robotics import DriveBase
from pybricks.tools import wait, StopWatch, run_task, multitask
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

def connect_remote():
    try:
        # Search for a remote for 5 seconds.
        my_remote = Remote(timeout=15000)

        print("Connected!")

        return my_remote
        
    except OSError:
        print("Could not find the remote.")

def controller():
    INITIAL_DELAY = 350
    REPEAT_DELAY = 100
    watch = StopWatch()
    dc = 0

    while True:
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

    if (Button.LEFT_PLUS) in pressed:
            if dc == 0: dc = dcmin
            if dc < 100: dc += 2
            if abs(dc) < dcmin*0.7: dc = 0
    elif (Button.LEFT_MINUS) in pressed:
            if dc == 0: dc = -dcmin
            if dc > -100: dc -= 2
            if abs(dc) < dcmin*0.7: dc = 0
    elif (Button.LEFT) in pressed:
            hub.light.on(Color.RED)
            while abs(dc) > 10:
                dc = dc - 10 if dc > 0 else dc + 10
                motor[0].dc(dc)
                print(dc)
                wait(100)
            dc = 0
    
    if dc == 0:
        hub.light.on(Color.RED)
    else:
        hub.light.on(Color.CYAN)

    motor[0].dc(dc)
    print(dc)
    return dc

### Set Up
remote = connect_remote()
hub = ThisHub() 

# --- define  motors - max 2 for CityHub
motor = []
motordirectionA = Direction.CLOCKWISE if dirmotorA == 1 else Direction.COUNTERCLOCKWISE
motordirectionB = Direction.CLOCKWISE if dirmotorB == 1 else Direction.COUNTERCLOCKWISE
motordirection = (motordirectionA , motordirectionB)
getmotors(motor)
###

# my version 
run_task(controller())
