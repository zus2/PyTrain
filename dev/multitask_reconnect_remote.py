# ---
# multitask_reconnect_remote.py v0.1
#
# Reconnect remote if out of range ( or batteries changed .. ) 
# Runs main() multitask inside a reinitialisation loop
# Uses race to stop the multitasking if connection lost
# You may have to store coroutine local data in globals 
# Or export if the race condition of deconnection is triggered
# Motor keeps running
#
# ---


from pybricks.hubs import TechnicHub
from pybricks.pupdevices import Remote, Motor
from pybricks.tools import wait, run_task, multitask
from pybricks.parameters import Port, Button

hub = TechnicHub()
motor = Motor(Port.A)

remoteconnected = False
instancecount = 0

async def my_task_3():
    while True:
        print('def')
        await wait(3000)

async def my_task_2():
    while True:
        print('abc')
        await wait(5000)

async def my_task_1():
    global remoteconnected 
 
    while True:
        try:
            remote.name()   
            print("remote still connected")
            # test if buttons work OK and motor keeps running if disconnected
            if Button.LEFT_PLUS in remote.buttons.pressed(): motor.run(200)
            elif Button.LEFT in remote.buttons.pressed(): motor.stop()
            elif Button.CENTER in remote.buttons.pressed(): hub.system.shutdown()
        except OSError as ex:
            print("*** remote disconnected ***")
            remoteconnected = False
            break
        await wait(200)

async def main():
    await multitask(
        my_task_1(),
        my_task_2(),
        my_task_3(),
        race=True,
    )

while remoteconnected == False:
    remote = Remote(timeout=None)
    remoteconnected = True
    instancecount += 1
    print ("instance",instancecount,": remote connected and running main()")
    run_task(main())
wait(1000)
