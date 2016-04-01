import sys
import os
import termios
import signal
import threading
REAL_SIGINT = signal.getsignal(signal.SIGINT)

class AsyncIO:
    def __init__(self):
        self.input_buffer = []
        self.lock = threading.Lock()
        self.output_access = False
        self.fd = sys.stdin.fileno()
        self.orgingal_config = termios.tcgetattr(self.fd)
        self.modified_config = termios.tcgetattr(self.fd)
        self.modified_config[3] &= ~termios.ECHO
        self.modified_config[3] &= ~termios.ICANON
    def __enter__(self):
        self.lock.acquire(True) # blocking
        if self.input_buffer:
            sys.stdout.write("\b \b"*len(self.input_buffer))
            sys.stdout.flush()
        self.output_access = True
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.output_access = False
        self.lock.release()
    def puts(self, string):
        assert self.output_access, "Not locked"
        sys.stdout.write(string)
        sys.stdout.flush()
    def println(self, string):
        assert self.output_access, "Not locked"
        self.puts(string+"\n")
        self.puts("".join(self.input_buffer))
    def _getc(self):
        # TODO: non-blocking
        return os.read(self.fd,7)
    def readln(self):
        try:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.modified_config)
            while True:
                char = self._getc()
                if len(char) != 1: # ascii only
                    continue
                if ord(char) == 127: # backspace
                    if self.input_buffer:
                        self.input_buffer.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                    continue
                else:
                    sys.stdout.write(char)
                    sys.stdout.flush()
                if char == "\n":    # enter, done
                    result = "".join(self.input_buffer)
                    self.input_buffer = []
                    return result
                else:
                    self.input_buffer.append(char)
        finally:
            # restore terminal settings
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.orgingal_config)

class ProcessHandler:
    def __init__(self, exit_callback=None):
        self.running = True
        self.callback = exit_callback
        signal.signal(signal.SIGINT, self.handle_exit_interrupt)
    def stop(self):
        self.running = False
        if self.callback:
            self.callback()
    def handle_exit_interrupt(self, signum, frame):
        signal.signal(signal.SIGINT, REAL_SIGINT)
        self.stop()
        sys.exit(1)

def start(print_thread_function, readline_callback, exit_callback=None):
    asyncio = AsyncIO()
    process = ProcessHandler(exit_callback)

    thread = threading.Thread(target=print_thread_function, args=(asyncio,process,))
    thread.start()

    while process.running:
        line = asyncio.readln()
        readline_callback(line, asyncio, process)

    thread.join()
