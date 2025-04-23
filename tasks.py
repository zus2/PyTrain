# -----------------------------------------------
# PyTrain - asynchronous Pybricks train controller 
#
# requires https://code.pybricks.com/ , LEGO City hub, LEGO BLE remote control
# 
# Version 0.1 Beta
#
# Published without Warranty - use at your own risk
#
# Thanks to: 
# Lok24 https://www.eurobricks.com/forum/forums/topic/187081-control-your-trains-without-smart-device-with-pybricks/
# @mpersand https://github.com/and-ampersand-and/PyBricks-Train-Motor-Control-Script?files=1:
#
# Features:
# Asynchronous speed change for inertia effect
# Crawl speed calibration adjustable in programme: 
#    Hold down left Stop button until violet light, set speed then press again to register
# Indicator lights for Go, Stop, Ready, Calibrate 
#
# To Do: 
# add multiple profiles like Lok24
# add auto-detect for other hubs, motors like Lok24 
# add second hub broadcast and lights like @mpersand
# add auto shutdown after no activity
# .. and much more
# -----------------------------------------------

# -----------------------------------------------
#  Set user defined values
# -----------------------------------------------

s = 12 # duty cycle control granularity - # (s)teps -s to +s
dcmin = 24 # min dc power (%) to make your train move - can be changed in program ! 
dcmax = 75 # max dc power (%) to make your train stay on the track .. 
brake = 700 # ms delay after stopping to prevent overruns

# --- modules
from pybricks.hubs import CityHub
from pybricks.parameters import Color, Button, Direction, Port
from pybricks.pupdevices import DCMotor, Motor, Remote
from pybricks.tools import multitask, run_task, wait
from umath import copysign

# --- set up all devices
hub = CityHub()
motor = DCMotor(Port.A, Direction.CLOCKWISE)
remote = Remote(timeout=None)
# clear terminal
print("\x1b[H\x1b[2J", end="")
print(hub.system.name())

# --- init vars and constants
t = 100 # ms delay between button presses if +/- held down used in function go()
cc = 0 # (c)ontroller +/- (c)lick count -s -> 0 -> s
dc = 0 # active (d)uty (c)ycle load
dcsteps = {}
LED_GO1 = Color.GREEN*0.2  
LED_GO2 = Color.GREEN*0.3  
LED_GO3 = Color.GREEN*0.4  
LED_GO4 = Color.GREEN*0.5  
LED_CRAWL = Color.CYAN*0.3  # crawl ( dcmin )
LED_STOP = Color.RED*0.5  # brake 
LED_READY = Color.ORANGE*1.0  # loco ready and idling
LED_CALIBRATE = Color.VIOLET # calibrate crawl speed in programme

# --- functions
# controller() - handles button presses and sets remote and hub status lights
# ems() - energy management system monitors and changes the speed of loco 
# drive() - takes a dc target value from EMS and changes motor speed with simulated inertia
# dcprofile() - set up s discrete duty cycle drive steps from threshold (dcmin) to dcmax - does not have to be linear 
# stop() - send out dc of 0 and sets a wait period before traction can recommence to prevent overruns
# go() - sets status lights and briefly blocks further +/- presses for t ms
# calibrate() - set the crawl speed in programme using left stop button (hold,set,save)
# main() - the main loop

async def drive(target):
    
    global dc , cc , dcmin
   
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

    # hard code upper safety limit during development ( and maybe permanent )
    dc = copysign(min(90,abs(dc)),dc)
    motor.dc(dc) 
    
def dcprofile(mode): 
    # map the loco power curve - for now theshold and then linear - the drive function can tweak
    # this is called if threshold dcmin is changed live
    global dcsteps, s , dcmin , dcmax

    dcsteps={} #reset

    if mode =="calibrate":
        for x in range(0,50):
            dcsteps[x] = x
    
    else:
        dcsteps[0] = 0
        dcsteps[1] = dcmin
        for x in range(1,s+1):
            dcsteps[x+1] = dcmin + (dcmax-dcmin)*x/s

    print("dcsteps",dcsteps)    

async def stop():
    global brake

    # avoid overruns
    await remote.light.on(LED_STOP)
    hub.light.on(LED_STOP)

    print("wait a second (",brake,"ms) !")
    await wait(brake)

    await remote.light.on(LED_READY)
    hub.light.on(LED_READY)

    # stop button also used for crawl speed calibration 
    if Button.LEFT in remote.buttons.pressed(): 
        print("calibrate dcmin")
        await calibrate()

async def calibrate():
    # set dcmin ( crawl speed )
    global dcmin , cc

    dcmin = 0 # reset
    vc = 0

    dcprofile("calibrate")
    
    await remote.light.on(LED_CALIBRATE)
    hub.light.on(LED_CALIBRATE)

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
            dcprofile("run")
            cc = 1
            await go()
            await drive(dcmin) # not strictly necessary but displays values

        await wait(100)


async def go():
    global t , cc

    # set status lights and disable button briefly
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
    

    await remote.light.on(led)
    hub.light.on(led)
    await wait(t)                 
    
async def ems():
    global dc , cc , dcsteps
    #target = 0 # local target dc
    
    while True:
        direction = copysign(1,cc)
        target = round(direction*dcsteps[abs(cc)])

        if dc != target:
            #print ("drive",target)
            await drive(target)
        
        await wait(200)

async def controller():
    global cc , s 
    
    while True:
        pressed = remote.buttons.pressed()
        if (len(pressed)):
    
            if Button.LEFT_PLUS in pressed:
                cc = cc + 1 if cc < s+1 else s+1
                print('remote',cc)
                if cc == 0: await stop()
                else: await go()
                
            elif Button.LEFT_MINUS in pressed:
                cc = cc - 1 if cc > -(s+1) else -(s+1)
                print('remote',cc)
                if cc == 0: await stop()
                else: await go()
                   
            elif Button.LEFT in pressed:
                cc = 0
                print('remote',cc)
                await stop()
                
            elif Button.CENTER in pressed:
                # press once to stop the programme
                # hold 2 secs to shutdown hub
                count = 0
                while Button.CENTER in pressed:
                    button = remote.buttons.pressed()
                    count+=1
                    if (count == 20): # 2 seconds
                        await stop()
                        print("Shutting down hub ...")
                        hub.system.shutdown() 
                    await wait(100)
                raise SystemExit("Closing program..")
    
        # print(len(pressed) or "listening...")
        # important - controls sensitivity to repeated and held down button presses
        # also see go()
        await wait(100)

async def main():
    await multitask(
        controller(),
        ems()
    )

dcprofile("run")

remote.light.on(LED_READY)
hub.light.on(LED_READY)

run_task(main())