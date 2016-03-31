import time
import asyncstdio

def output_thread(asyncio, process):
    a = 0
    while process.running:
        with asyncio as io:
            io.println("["+str(a).zfill(4)+"]")
            a += 1
            if a == 10000:
                a = 0
        time.sleep(1)

def process_line(line, asyncio, process):
    line = line.strip()
    if line in ["quit", "exit"]:
        process.stop()
    else:
        with asyncio as aio:
            aio.println(line[::-1])

def on_exit():
    print("Quitting!")

asyncstdio.start(output_thread, process_line, on_exit)
