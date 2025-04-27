# ---
# multitask_reconnect_remote.py v0.1
#
# Reconnect remote if out of range ( or batteries changed .. ) 
# Runs main() multitask inside a reinitialisation loop
# Uses race to stop the multitasking if connection lost
# You may have to store coroutine local data in globals 
# Or export if the race condition of deconnection is triggered
#
# ---


from pybricks.hubs import TechnicHub
from pybricks.pupdevices import Remote
from pybricks.tools import wait, run_task, multitask

hub = TechnicHub()

connected = False
count = 0

async def my_task_3():
    while True:
        print('def')
        await wait(3000)

async def my_task_2():
    while True:
        print('abc')
        await wait(5000)

async def my_task_1():
    global connected 

    while True:
        try: 
            remote.name()
            print('remote still connected')
            await wait(100)
        except:
            print("*** remote disconnected ***")
            connected = False
            break
        await wait(1000)

async def main():
    await multitask(
        my_task_1(),
        my_task_2(),
        my_task_3(),
        race=True,
    )

while connected == False:
    remote = Remote(timeout=None)
    connected = True
    count += 1
    print ("instance",count,": remote connected and running main()")
    run_task(main())
wait(1000)
