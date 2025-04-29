
# PyTrain - A Pybricks train controller with asynchronous MicroPython coroutines 
#
# Version 0.71 Beta
# https://github.com/zus2/PyTrain
#
# requires https://code.pybricks.com/ , LEGO City hub, LEGO BLE remote control
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
# PARTICULAR PURPOSE AND NONINFRINGEMENT.
# 
# Features:
# Asynchronous speed change and stop commands for inertia effect 
# Customisable speed ramp max, min and granularity
# Crawl speed calibration adjustable in programme 
# Synced indicator led for Go, Crawl, Stop, Ready, Calibrate 
# v0.2 Added stop script or shutdown hub in programme using center button
# v0.3 Added support for 2nd motor and initial support for sensor motors
# v0.4 Cleaned up Motor direction logic 
# v0.5 Added heartbeat auto-shutdown and user input sanity checks
# v0.55 Added storage and reload for dcmin from calibrate()
# v0.6 Added support for Technic and City hubs 
# v0.7 Added separate reverse speed limit which can be 0
#
# To Do: 
#  
# add second hub broadcast and lights like @mpersand
# auto reconnect remote
# .. and much more
#
# Thanks to: 
# Lok24 https://www.eurobricks.com/forum/forums/topic/187081-control-your-trains-without-smart-device-with-pybricks/
# @mpersand https://github.com/and-ampersand-and/PyBricks-Train-Motor-Control-Script?files=1:
# and the Pybricks team of course .. 

# ----------
# --- User defined values
# ----------

dcsteps = 12 # number of duty cycle steps: -s to +s (range 5 - 100)
dcmin = 25 # min dc power (%) to move the train - can be changed in program ! ( range 10 - 40 )
dcmax = 75 # max dc power (%) to keep the train stay on the track ( range 41 - 90 (hard code limit) )
dcmaxr = 35 # max reverse dc power (%) ( range 0 - 90 (hard code limit))
dcacc = 20 # acceleration smoothness - 1 (aggressive) - 100 (gentle) 
brake = 600 # ms delay after stopping to prevent overruns ( range 1 - 2000 ms )
BROADCASTCHANNEL = 1  # broadcast channel for 2nd hub ( Use None or 0 - 255 ) - consumes power !
dirmotorA = -1       # A Direction clockwise 1 or -1
dirmotorB = 1       # B Direction clockwise 1 or -1

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


# ----------
# --- functions
# ----------

# --- function descriptions
# drive() - takes a dc target value from EMS and changes motor speed with simulated inertia
# dcprofile() - set up s discrete duty cycle drive steps from threshold (dcmin) to dcmax - does not have to be linear 
# getmotors() -  check ports for connected motors
# stop() - send out dc of 0 and sets a wait period before traction can recommence to prevent overruns
# calibrate() - set the crawl speed in programme using left stop button (hold,set,save)
# go() - sets status lights and briefly blocks further +/- presses for t ms
# ems() - energy management system monitors and changes the speed of loco 
# controller() - handles button presses and sets remote and hub status lights
# heartbeat() - shut down after a period of inactivity
# main() - the main loop

# --- drive() - send dc command to the motor(s)
async def drive(target):
    
    global dc , cc , dcmin , dcmaxr 
   
    # 2 deltas for accel and decel
    smooth1 = 5 #  1 - 10 , try 5 - this defines the agressiveness of accel - higher is steadier
    smooth2 = 3 #  1 - 10 , try 2 - this defines the agressiveness of decel - decrease for faster response

    delta1 = max(1,round(abs(target - dc)/smooth1)) 
    delta2 = max(1,round(abs(target - dc)/smooth2)) 

    dcstart = dcmin - delta2 # kickstart using delta1 or delta2
    dcstop = dcmin - delta2 # kickstop to prevent long tail slowdown blocking responsiveness

    # positive change
    if target > dc: 
        if dc >= 0: #forward accel
            dc = max(dcstart, dc + delta1) 
        elif dc < -dcstop: #reverse decel
            dc = dc + delta2
        else:
            dc = 0
    # negative change
    else:
        if dc <= 0: #accel reverse
            dc = min(-dcstart,dc - delta1) 
        elif dc > dcstop: #forward decel
            dc = dc - delta2
        else:
            dc = 0
    
    print("dc target:",target,"actual dc",dc,"controller",cc)
    #print (hub.battery.current())

    # hard code dc safety limit during development ( and maybe permanent )
    dc = copysign(min(90,abs(dc)),dc)

    # hard limit on reverse max dc - should be done via asymmetric dcprofiles
    if dc < -dcmaxr: 
        dc = -dcmaxr
        cc += 1 # prevent racing to un unreachable target dc ( from cc )
        print("reverse speed limit reached:",dcmaxr)

    if BROADCASTCHANNEL:
        # broadcast speed and light
        bdata = (dc , 0)
        await broadcast(bdata)

    # send drive command to motors 1 and 2
    for m in motor:
        #print (m)
        if (m): m.dc(dc)

# --- broadcast() - keep trying to send the data until succesful
async def broadcast(bdata):
    global ble

    while True:
        try:
            await hub.ble.broadcast(bdata)
            print("sent ..")
            ble = True
            break
            
        except OSError as ex:
            print ("broadcast error",ex)
            await wait(10)


# --- dcprofile() - build speed ramp
def dcprofile(mode): 
    # map the loco power curve - for now threshold and then linear - the drive function can tweak
    # this is called if threshold dcmin is changed live
    global dcramp, dcsteps , dcmin , dcmax

    dcramp={} #reset

    if mode =="calibrate":
        for x in range(0,50):
            dcramp[x] = x
    
    else:
        dcramp[0] = 0
        dcramp[1] = dcmin
        for x in range(1,dcsteps+1):
            dcramp[x+1] = round( dcmin + (dcmax-dcmin)*x/dcsteps, 1 )

    print("dcsteps",dcsteps,dcramp)    


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

# --- stop()
async def stop():
    global brake

    # avoid overruns
    await remote.light.on(LED_STOP)
    hub.light.on(LED_STOP)

    print("brake .. (",brake,"ms )")
    await wait(brake)

    await remote.light.on(LED_READY)
    hub.light.on(LED_READY)

    # stop button also used for crawl speed calibration
    count = 0 
    while Button.LEFT in remote.buttons.pressed():
        count += 1
        if count == 5:
            print("calibrate dcmin")
            await calibrate()
        await wait(100)

# --- calibrate() - set the crawl speed using contoller
async def calibrate():
    # set dcmin ( crawl speed )
    global dcmin , cc

    dcmin = 0 # reset
    vc = 0

    dcprofile("calibrate")
    
    await remote.light.on(LED_CALIBRATE)
    hub.light.on(LED_CALIBRATE)

    print("Adjust dcmin (crawl speed) using Left +/- then save with Left Center")

    while True and dcmin == 0:
        pressed = remote.buttons.pressed()
        if Button.LEFT_PLUS in pressed:
            vc += 1
            cc = vc
            await drive(vc)

        if Button.LEFT_MINUS in pressed:
            vc = vc - 1 if vc > 0 else 0 # we don't want negative dcmin
            cc = vc
            await drive(vc)

        if Button.LEFT in pressed and vc > 0:
            # set new dcmin
            dcmin = cc
            print("new dcmin is",dcmin)

            # store user dcmin:
            hub.system.storage(offset=0, write=b"dc" + f"{dcmin:02}")
            print("and saved to hub")

            dcprofile("run")
            cc = 1
            await go(cc)
            await drive(dcmin) # not strictly necessary but displays values

        await wait(100)


# --- go(cc) - set status lights and disable button briefly
async def go(cc):

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
    
    try:
        await remote.light.on(led)
    except OSError as ex:
        print("** failed to set the LED in go() **",ex)

        hub.light.on(led)
    await wait(BUTTONDELAY)                 

# --- ems() - convert controller presses to motor commands
async def ems():
    global dc , cc , dcramp , dcacc , ble
    
    while True:
        # check current dc (dc) versus target dc from controller (cc)
        
        direction = copysign(1,cc)
        target = round(direction*dcramp[abs(cc)])

        if dc != target:
            #print ("drive",target)
            await drive(target)
        else:
            if BROADCASTCHANNEL and ble == True:
                await wait(200) # let the broadcast be observed
                try:
                    await hub.ble.broadcast(None)
                    print("closing broadcast")
                    ble = False
                except:
                    print("BLE clash in ems()")

        # dcacc controls accel / decel response
        # try 20 (200ms) for s=12 , less if s higher 
        await wait(dcacc * 10)

# --- controller() - monitor the remote presses
async def controller():
    global cc , dcsteps , beat , remote
    
    while True:
        try:
            pressed = remote.buttons.pressed()
        except OSError as ex:
            print (" remote not connected: ",ex)
            await wait(1000)
            pressed = {}

            '''
            # reconnect is not working within multitasking ..
            try:
                remote = Remote(timeout=1000)
                await wait(100)
                print (" remote reconnected ")
            except OSError as ex:
                print (" remote still not connected ")
            '''

        if (len(pressed)):

            beat = 1 # reset heartbeat()
    
            if Button.LEFT_PLUS in pressed:
                cc = cc + 1 if cc < dcsteps+1 else dcsteps+1
                print('remote',cc)
                if cc == 0: await stop()
                else: await go(cc)
                
            elif Button.LEFT_MINUS in pressed:
                cc = cc - 1 if cc > -(dcsteps+1) else -(dcsteps+1)
                print('remote',cc)
                if cc == 0: await stop()
                else: await go(cc)
                   
            elif Button.LEFT in pressed:
                cc = 0
                print('remote',cc)
                await stop()
                
            elif Button.CENTER in pressed:
                # press once to stop the train AND the programme
                # hold 2 secs to shutdown hub
                cc = 0
                print('remote center',cc)
                await stop()
                count = 0
                while Button.CENTER in pressed:
                    pressed = remote.buttons.pressed()
                    count+=1
                    if (count == 10): # 1 seconds ( plus brake in stop() )
                        print("Shutting down hub ...")
                        await remote.light.on(LED_STOP)
                        await wait(100)
                        hub.system.shutdown() 
                    await wait(100)
                
                raise SystemExit("Closing program..")
    
        # print(len(pressed) or "listening...")
        # important - controls sensitivity to repeated and held down button presses
        # also see go()
        await wait(50)

# --- heartbeat() - shutdown after specified period of inactivity
async def heartbeat():
    global beat
    _death = 5

    while True:
        # if train is running reset heartbeat 
        if cc != 0: 
            beat = 0 

        # shutdown after 5 minutes if not running and no remote buttons pressed
        elif beat >= _death: 
            print ("no activity for 5 minutes - shutting down ..")
            await wait(100)
            hub.system.shutdown()

        beat += 1

        print ("heartbeat:",beat,"of",_death)

        await wait(60000) # 1 minute

# --- main() 
async def main():
    await multitask(
        controller(),
        ems(),
        heartbeat(),
    )

# --------------
# --- initialise 
# --------------

# --- sanity check on user defined values

# error messages tuple
sm = ("*** sanity check ***","value","invalid - has been reset to","- check your values")

if not dcsteps in range(5,101):
    _bad = dcsteps 
    dcsteps = 10
    print (sm[0],"s",sm[1],_bad,sm[2],dcsteps,sm[3])
if not dcmin in range(10,41): 
    _bad = dcmin
    dcmin = 25
    print (sm[0],"dcmin",sm[1],_bad,sm[2],dcmin,sm[3])
if not dcmax in range(41,91): 
    _bad = dcmax
    dcmax = 75
    print (sm[0],"dcmax",sm[1],_bad,sm[2],dcmax,sm[3])
if not dcmaxr in range(0,91): 
    _bad = dcmaxr
    dcmaxr = 70
    print (sm[0],"dcmaxr",sm[1],_bad,sm[2],dcmaxr,sm[3])
if not dcacc in range(1,101): 
    _bad = dcacc
    dcacc = 20
    print (sm[0],"dcacc",sm[1],_bad,sm[2],dcacc,sm[3])
if not brake in range(1,2001): 
    _bad = brake
    brake = 700
    print (sm[0],"brake",sm[1],_bad,sm[2],brake,sm[3])
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
ble = False # broadcasting is active
beat = 0 # heartbeat counter
LED_GO1 = Color.GREEN*0.2  
LED_GO2 = Color.GREEN*0.3  
LED_GO3 = Color.GREEN*0.4  
LED_GO4 = Color.GREEN*0.5  
LED_CRAWL = Color.CYAN*0.3  # crawl ( dcmin )
LED_STOP = Color.RED*0.5  # brake 
LED_READY = Color.ORANGE*1.0  # loco ready and idling
LED_CALIBRATE = Color.VIOLET # calibrate crawl speed in programme

# --- clear terminal 
print("\x1b[H\x1b[2J", end="")

# --- find and set up hub - City or Technic
try: 
    from pybricks.hubs import CityHub
    hub = CityHub(broadcast_channel=BROADCASTCHANNEL)
except: 
    try: 
        from pybricks.hubs import TechnicHub
        hub = TechnicHub(broadcast_channel=BROADCASTCHANNEL)
    except: print("no suitable hubs found")
print(hub.system.name())
print("---\nCell voltage:",round(hub.battery.voltage()/6000,2))

# --- set up remote
print ("Looking for remote ..")
try:
    remote = Remote(timeout=10000)
    remote.light.on(LED_READY)
except OSError as ex:
    print ("Not found - shutting down ..")
    wait(100)
    hub.system.shutdown()

# check for storage dcmin
# read user data:
data = hub.system.storage(offset=0, read=4)
data = str(data,"utf-8") 

if data[:2] == "dc" and int(data[2:4]) in range (0,30): 
    dcmin = int(data[2:4])
    print("Using stored dcmin",dcmin," - recalibrate to override",) 
else:
    print("Stored dcmin not found:",data," ( only stored with calibration )")
    print("Using dcmin=",dcmin)

# some of these set up functions have to be run before main()
dcprofile("run")
getmotors(motor)

remote.light.on(LED_READY)
hub.light.on(LED_READY)

run_task(main())