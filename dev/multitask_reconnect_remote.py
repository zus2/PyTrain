# ---
#
# Reconnect remote if out of range ( or batteries changed .. ) 
# Runs main() multitask inside a reinitialisation loop
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
            print('remote connected')
            await wait(100)
        except OSError as ex:
            print("disconnected")
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
    print ("instance",count,": connected and running main()")
    run_task(main())
wait(1000)
