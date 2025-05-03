# PyTrain - A Pybricks train controller with asynchronous MicroPython coroutines 
#
# Version 0.93 Beta
# https://github.com/zus2/PyTrain
#
# Developed with v3.6.1 (Pybricks Code v2.6.0)
#
# © 2025 Paul Walsh
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
# PARTICULAR PURPOSE AND NONINFRINGEMENT. See LICENCE in the official repository.

# ----------
# --- User defined values
# ----------

DCSTEPS = 12        # number of +/- button presses to reach full forward speed: -s to +s (range 5 - 100)
DCMIN = 25          # min dc power (%) to move the train - can be changed in program ! ( range 10 - 40 )
DCMAX = 80          # max forward dc power (%) to keep the train stay on the track ( range 41 - 90 (hard code limit) )
DCMAXR = 50         # max reverse dc power (%) ( range 0 - 90 (hard code limit)) - set to 0 for trams ?
DCACC = 20          # acceleration - 1 (aggressive) - 80 (gentle) - try 20
BRAKE = 600         # ms delay after stopping to prevent overruns ( range 1 - 2000 ms )
BROADCASTCHANNEL = None  # channel for 2nd hub ( 0 - 255 ) Use None if no other hub consumes power !
INACTIVITY = 5      # mins before shutdown if no button pressed and train stationary, try 5
dirmotorA = -1      # Hub motor A Direction clockwise 1 or -1
dirmotorB = 1       # Hub motor B Direction clockwise 1 or -1
OUTPUT = False      # set to true to show extra info for debugging - True or False

# ----------
# --- Main programme
# ----Do not change anything below here unless you are a competent programmer
# ----------

# --- modules
from pybricks.parameters import Color, Button, Direction, Port
from pybricks.pupdevices import DCMotor, Motor, Remote
from pybricks.tools import multitask, run_task, wait
from umath import copysign
from pybricks.iodevices import PUPDevice
from pybricks.hubs import ThisHub

# ----------
# --- functions
# ----------

async def drive(target):
    """
    Adjusts the motor speed to the target duty cycle with simulated inertia.

    Args:
        target (int): The target duty cycle.
    """    
    global dc , cc 
   
    await wait(0)

    # 2 deltas for accel and decel
    smooth1 = 3 #  1 - 10 , try 4 - this defines the agressiveness of accel - higher is smoother
    smooth2 = 2 #  1 - 10 , try 2 - this defines the agressiveness of decel - decrease for faster response

    delta1 = max(1,round(abs(target - dc)/smooth1)) 
    delta2 = max(1,round(abs(target - dc)/smooth2)) 

    dckickstart = round(DCMIN / 2) # kickstart in case delta very small 
    dckickstop = round(DCMIN / 2) # kickstop to prevent long tail slowdown blocking responsiveness

    # positive change
    if target > dc: 
        if dc >= 0: #forward accel
            newdc = max(dckickstart, dc + delta1) 
        elif dc < -dckickstop: #reverse decel
            newdc = dc + delta2
        else:
            newdc = 0
    # negative change
    else:
        if dc <= 0: #accel reverse
            newdc = min(-dckickstart,dc - delta1) 
        elif dc > dckickstop: #forward decel
            newdc = dc - delta2
        else:
            newdc = 0
    
    if (OUTPUT): print("dc target:",target,"actual dc",newdc,"controller",cc)
    
    # hard code dc safety limit during development ( and maybe permanent )
    newdc = copysign(min(90,abs(newdc)),newdc)

    # hard limit on reverse max dc - should be done via asymmetric dcprofiles
    if newdc < -DCMAXR: 
        newdc = -DCMAXR
        cc += 1 # prevent racing to un unreachable target dc ( from cc )
        if (OUTPUT): print("reverse speed limit reached:",DCMAXR)

    #update global
    dc = newdc

    # send drive command to motors 1 and 2
    for m in motor:
        #print (m)
        if (m): m.dc(dc)

async def broadcast():
    """
    BT commands cannot be simultaneous:
    Activate and update 100ms system broadcast of dc and light values
    Send light colour to remote 
    """
    await wait(0)
 
    thisdc = 0
    thislight = Color.BLUE

    while True:
        await wait(0)

        if thisdc != dc:

            bdata = (dc, 0)

            try:
                await hub.ble.broadcast(bdata)
                thisdc = dc
                if (OUTPUT): print("broadcast data updated",bdata)
            except OSError as ex:
                if (OUTPUT): print ("broadcast error 1",ex)

        if thislight != remotelight:

            try:
                await remote.light.on(remotelight)
                thislight = remotelight
            except OSError as ex:
                if (OUTPUT): print ("remote light error 1",ex)
                
        await wait(0)

def dcprofile(mode):
    """
    # Set up s discrete duty cycle steps from threshold (DCMIN) to DCMAX 
    # Map the loco power curve - for now threshold and then linear 
    # This is also called if threshold DCMIN is changed live

    Args:
        mode (string):  Build normal dcramp or granular for calibration
    """
    global dcramp

    dcramp={} #reset

    if mode =="calibrate":
        for x in range(0,50):
            dcramp[x] = x
    
    else:
        dcramp[0] = 0
        dcramp[1] = DCMIN
        for x in range(1,DCSTEPS+1):
            dcramp[x+1] = round( DCMIN + (DCMAX-DCMIN)*x/DCSTEPS, 1 )

    print("DCSTEPS",DCSTEPS,dcramp)    

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

        #print(motor)

async def stop():
    """
    Sets the stop LED and a wait period before traction can recommence to prevent overruns
    """
    global remotelight

    await wait(0)

    remotelight = LED_STOP # remote light handled in broadcast()
    hub.light.on(LED_STOP)

    if(OUTPUT): print("brake .. (",BRAKE,"ms )")
    await wait(BRAKE)

    remotelight = LED_READY # remote light handled in broadcast()
    hub.light.on(LED_READY)

    # stop button also used for crawl speed calibration
    count = 0 
    while Button.LEFT in remote.buttons.pressed():
        count += 1
        if count == 5:
            print("calibrate DCMIN")
            await calibrate()
        await wait(100)

async def calibrate():
    """
    Set the crawl speed DCMIN in programme using left buttons (hold,set,save)
    """
    global DCMIN , cc, remotelight

    await wait(0)

    DCMIN = 0 # reset
    vc = 0

    dcprofile("calibrate")
    
    remotelight = LED_CALIBRATE # remote light handled in broadcast()
    hub.light.on(LED_CALIBRATE)

    print("Adjust DCMIN (crawl speed) using Left +/- then save with Left Center")

    while True and DCMIN == 0:
        pressed = remote.buttons.pressed()
        if Button.LEFT_PLUS in pressed:
            vc += 1
            cc = vc
            await drive(vc)

        if Button.LEFT_MINUS in pressed:
            vc = vc - 1 if vc > 0 else 0 # we don't want negative DCMIN
            cc = vc
            await drive(vc)

        if Button.LEFT in pressed and vc > 0:
            # set new DCMIN
            DCMIN = cc
            print("new DCMIN is",DCMIN)

            # store user DCMIN:
            hub.system.storage(offset=0, write=b"dc" + f"{DCMIN:02}")
            print("and saved to hub")

            dcprofile("run")
            cc = 1
            await go(cc)
            await drive(DCMIN) # not strictly necessary but displays values

        await wait(100)

async def go(cc):
    """
    Sets status lights and briefly blocks further +/- presses for t ms

    Args:
        cc(int): Controller click count
    """
    global remotelight

    lowcc = abs(cc)
    if lowcc == 1:
        led = LED_CRAWL
    elif lowcc == 2:
        led = LED_GO1
    elif lowcc == 3:
        led = LED_GO2
    elif lowcc == 4:
        led = LED_GO3
    else:
        led = LED_GO4
    
    remotelight = led # remote light handled in broadcast()
    hub.light.on(led)

    if led == LED_CRAWL:
        if(OUTPUT): print("crawl .. (",BRAKE/2,"ms )")
        # pause briefly on Crawl 
        await wait(BRAKE/2) 
    
    await wait(BUTTONDELAY)                 

async def ems(): 
    """
    Check current dc (dc) versus target dc from controller (cc)
    Energy management system monitors and changes the speed of loco 
    """
    await wait(0)

    while True:
        await wait(0)

        direction = copysign(1,cc)
        target = round(direction*dcramp[abs(cc)])

        # x is for system shutdown
        if not dc in (target, "x"):
            #print ("drive",target)
            await drive(target)
        
        # DCACC controls accel / decel response
        # try 20 (200ms) for s=12 , less if s higher 
        await wait(DCACC * 10)

async def controller():
    """
    Handles button presses and sets remote and hub status lights
    """
    global cc , beat, dc

    await wait(0)    
    
    while True:
        try:
            pressed = remote.buttons.pressed()
        except OSError as ex:
            print (" remote not connected: ",ex)
            await wait(1000)
            pressed = {}

        if (len(pressed)):

            beat = 1 # reset heartbeat()
    
            if Button.LEFT_PLUS in pressed:
                cc = cc + 1 if cc < DCSTEPS+1 else DCSTEPS+1
                if (OUTPUT):print("remote",cc)
                if cc == 0: await stop()
                else: await go(cc)
                
            elif Button.LEFT_MINUS in pressed:
                cc = cc - 1 if cc > -(DCSTEPS+1) else -(DCSTEPS+1)
                if (OUTPUT):print("remote",cc)
                if cc == 0: await stop()
                else: await go(cc)
                   
            elif Button.LEFT in pressed:
                cc = 0
                if (OUTPUT):print("remote",cc)
                await stop()
                
            elif Button.CENTER in pressed:
                # press once to stop the train AND the programme
                # hold 2 secs to shutdown hub
                cc = 0
                if (OUTPUT):print("remote center",cc)
                await stop()
                count = 0
                while Button.CENTER in pressed:
                    pressed = remote.buttons.pressed()
                    count+=1
                    if (count == 10): # 1 seconds ( plus brake in stop() )
                        print("Shutting down hub ...")
                        await remote.light.on(LED_STOP)
                        if BROADCASTCHANNEL: 
                            dc = "x" #shut down the second hub
                            await wait(1000)
                        hub.system.shutdown() 
                    await wait(100)
                
                raise SystemExit("Closing program..")
    
        # print(len(pressed) or "listening...")
        # important - controls sensitivity to repeated and held down button presses
        # also see go()
        await wait(50)

async def heartbeat():
    """
    Shut down after a INACTIVITY minutes of inactivity
    """
    global beat, dc

    await wait(0)
    
    while True:
        # if train is running reset heartbeat 
        if cc != 0: 
            beat = 0 

        # shutdown after 5 minutes if not running and no remote buttons pressed
        elif beat >= INACTIVITY: 
            print ("no activity for",INACTIVITY,"minutes - shutting down ..")
            if BROADCASTCHANNEL: dc = "x" #shut down the second hub
            wait(100)
            hub.system.shutdown()
            
        beat += 1

        print ("heartbeat:",beat,"of",INACTIVITY)

        await wait(60000) # 1 minute

"""
Set up multitasking with conditional broadcasting
"""

tasks = [controller(),
                ems(),
                heartbeat(),
        ]

if BROADCASTCHANNEL:
    tasks.append(broadcast())

async def main():
            await multitask(
                *tasks)

# --------------
# --- initialise 
# --------------

# --- sanity check on user defined values

# error messages tuple
sm = ("*** sanity check ***","value","invalid - has been reset to","- check your values")

if not DCSTEPS in range(5,101):
    _bad = DCSTEPS 
    DCSTEPS = 10
    print (sm[0],"s",sm[1],_bad,sm[2],DCSTEPS,sm[3])
if not DCMIN in range(10,41): 
    _bad = DCMIN
    DCMIN = 25
    print (sm[0],"DCMIN",sm[1],_bad,sm[2],DCMIN,sm[3])
if not DCMAX in range(41,91): 
    _bad = DCMAX
    DCMAX = 80
    print (sm[0],"DCMAX",sm[1],_bad,sm[2],DCMAX,sm[3])
if not DCMAXR in range(0,91): 
    _bad = DCMAXR
    DCMAXR = 70
    print (sm[0],"DCMAXR",sm[1],_bad,sm[2],DCMAXR,sm[3])
if not DCACC in range(1,81): 
    _bad = DCACC
    DCACC = 20
    print (sm[0],"DCACC",sm[1],_bad,sm[2],DCACC,sm[3])
if not BRAKE in range(1,2001): 
    _bad = BRAKE
    BRAKE = 600
    print (sm[0],"brake",sm[1],_bad,sm[2],BRAKE,sm[3])
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
BUTTONDELAY = 100 # ms delay between button presses if +/- held down used in function go()
cc = 0 # (c)ontroller +/- (c)lick count -s -> 0 -> s
dc = 0 # active (d)uty (c)ycle load
dcramp = {}
beat = 0 # heartbeat counter
LED_GO1 = Color.GREEN*0.2  
LED_GO2 = Color.GREEN*0.3  
LED_GO3 = Color.GREEN*0.4  
LED_GO4 = Color.GREEN*0.5  
LED_CRAWL = Color.CYAN*0.3  # crawl ( DCMIN )
LED_STOP = Color.RED*0.5  # brake 
LED_READY = Color.ORANGE*1.0  # loco ready and idling
LED_CALIBRATE = Color.VIOLET # calibrate crawl speed in programme

# --- set up hub
hub = ThisHub(broadcast_channel=BROADCASTCHANNEL)

# --- clear terminal 
print("\x1b[H\x1b[2J", end="")
print("Pytrain - Asynchronous Train Controller")
print(hub.system.name())
print("---\nCell voltage:",round(hub.battery.voltage()/6000,2))

# --- set up remote 
print ("Looking for remote ..")
try:
    remote = Remote(timeout=20000)
    remotelight = LED_READY # remote light handled in broadcast()
except OSError as ex:
    print ("Not found - shutting down ..")
    wait(1000)
    hub.system.shutdown()

# check for storage DCMIN
# read user data:
data = hub.system.storage(offset=0, read=4)
data = str(data,"utf-8") 

if data[:2] == "dc" and int(data[2:4]) in range (0,30): 
    DCMIN = int(data[2:4])
    print("Using stored DCMIN",DCMIN," - recalibrate to override",) 
else:
    print("Stored DCMIN not found:",data," ( only stored with calibration )")
    print("Using DCMIN=",DCMIN)

# some of these set up functions have to be run before main()
dcprofile("run")
getmotors(motor)
hub.light.on(LED_READY)

run_task(main())