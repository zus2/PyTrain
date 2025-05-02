# PytrainFollow - observer to Pytrain
#
# Version 0.92 Beta
# https://github.com/zus2/PyTrain

# ----------
# --- User defined values
# ----------

OBSERVECHANNEL = 1 #  Observer channel must match Broadcast channel in pytrain.py ( Use None or 0 - 255 )
dirmotorA = -1       # A Direction clockwise 1 or -1
dirmotorB = 1       # B Direction clockwise 1 or -1
INACTIVITY = 5 # shut down the hub after this many minutes
OUTPUT = False      # set to true to show extra info for debugging

# ----------
# --- Main programme
# ----Do not change anything below here unless you are a competent programmer
# ----------

# --- modules
from pybricks.parameters import Color, Direction, Port
from pybricks.pupdevices import DCMotor, Motor
from pybricks.iodevices import PUPDevice
from pybricks.tools import multitask, run_task, wait
from pybricks.hubs import ThisHub

# ----------
# --- functions
# ----------

# --- heartbeat() - shutdown after specified period of inactivity
async def heartbeat():
    global beat

    await wait(0)

    while True:
        # if train is running reset heartbeat 
        if dc != 0: 
            beat = 0 

        # shutdown after 5 minutes if not running and no remote buttons pressed
        elif beat >= INACTIVITY: 
            print ("no activity for",INACTIVITY,"minutes - shutting down ..")
            wait(100)
            hub.system.shutdown()
            
        beat += 1

        print ("heartbeat:",beat,"of",INACTIVITY)

        await wait(60000) # 1 minute

# --- getmotors() - auto detect DC and technic motors
def getmotors(motor):

    for x in (0,1):

        port = (Port.A,Port.B)[x]

        try:
            device = PUPDevice(port)
            id = device.info()['id']
            print("device",id,"on",x)

            if device.info()['id'] < 3:
                print("DC motor on",port)
                motor.append(DCMotor(port,motordirection[x]))

            else:
                print("Motor on",port)
                motor.append(Motor(port,motordirection[x]))

        except OSError as err:
            print("no device on",port)
            motor.append("")

        #print(motor)

# --- drive()
async def drive():
    global dc , beat

    await wait(0)
    
    currentdc = 0

    while True:
        # send drive command to motors 1 and 2
        if currentdc != dc:

            for m in motor:
                if (m): m.dc(dc)
 
            if dc: 
                hub.light.on(LED_GO4)
            else:
                hub.light.on(LED_READY)

            if (OUTPUT): print (dc)

            currentdc = dc
            beat = 0
                
        await wait(10)

# --- listen()
async def listen():
    global dc, light

    await wait(0)

    while True:

        try:
            data = hub.ble.observe(OBSERVECHANNEL)
        except Exception as ex:
            print("Unknown problem observing:",ex)

        if data is None:
            #hub.light.on(LEDnotreceiving)
            #print('received nothing')
            pass
        else:
            dc, light = data

            if dc == "x":
                hub.system.shutdown()

            elif dc not in range (-100,101):
                dc = 0

            if light not in range (0,101):
                light = 0

        await wait(10)

# --- main() 
async def main():
    await multitask(
        listen(),
        drive(),
        heartbeat(),
        #broadcast()
    )

# --------------
# --- initialise 
# --------------

# --- sanity check on user defined values

# error messages tuple
sm = ("*** sanity check ***","value","invalid - has been reset to","- check your values")

if not dirmotorA in (1,-1): 
    _bad = dirmotorA
    dirmotorA = 1
    print (sm[0],"dirmotorA",sm[1],_bad,sm[2],"integer",dirmotorA,sm[3])
if not dirmotorB in (1,-1): 
    _bad = dirmotorB
    dirmotorB = -1
    print (sm[0],"dirmotorB",sm[1],_bad,sm[2],"integer",dirmotorB,sm[3])

# --- define  motors - max 2 for CityHub
motor = []
motordirectionA = Direction.CLOCKWISE if dirmotorA == 1 else Direction.COUNTERCLOCKWISE
motordirectionB = Direction.CLOCKWISE if dirmotorB == 1 else Direction.COUNTERCLOCKWISE
motordirection = (motordirectionA , motordirectionB)

# --- init vars and constants
dc = 0 # active (d)uty (c)ycle load
light = 0 # not used yet 
beat = 0 # heartbeat counter
LED_GO1 = Color.GREEN*0.2  
LED_GO2 = Color.GREEN*0.3  
LED_GO3 = Color.GREEN*0.4  
LED_GO4 = Color.GREEN*0.5  
LED_CRAWL = Color.CYAN*0.3  # crawl ( dcmin )
LED_STOP = Color.RED*0.5  # brake 
LED_READY = Color.ORANGE*1.0  # loco ready and idling
LED_CALIBRATE = Color.VIOLET # calibrate crawl speed in programme

# --- find and set up hub - City or Technic
hub = ThisHub(broadcast_channel=None, observe_channels=[OBSERVECHANNEL])

# --- clear terminal 
print("\x1b[H\x1b[2J", end="")
print("Pytrain (Follow) - Asynchronous Train Controller")
print(hub.system.name())
print("---\nCell voltage:",round(hub.battery.voltage()/6000,2))

# some of these set up functions have to be run before main()
getmotors(motor)
hub.light.on(LED_READY)

run_task(main())

