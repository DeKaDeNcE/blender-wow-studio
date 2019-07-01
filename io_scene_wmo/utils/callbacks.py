import bpy
from functools import partial
from time import time

from ..third_party.boltons.funcutils import wraps

def parametrized(dec):
    def layer(*args, **kwargs):
        def repl(f):
            return dec(f, *args, **kwargs)
        return repl
    return layer

@parametrized
def delay_execution(func, delay_sec=1.0):

    lock = False
    def timer(*args, **kwargs):
        nonlocal lock
        lock = False

        func(*args, **kwargs)

    @wraps(func)
    def wrapped(*args, **kwargs):

        nonlocal lock

        if not lock:
            lock = True
            bpy.app.timers.register(partial(timer, *args, **kwargs), first_interval=delay_sec)

    return wrapped

@parametrized
def on_release(func, delay_sec=1.5):

    exec_time = time()

    def timer(*args, **kwargs):
        nonlocal exec_time
        if not abs(exec_time - time()) < delay_sec:
            func(*args, **kwargs)

    @wraps(func)
    def wrapped(*args, **kwargs):
        nonlocal exec_time
        exec_time = time()

        bpy.app.timers.register(partial(timer, *args, **kwargs), first_interval=max(1.0, delay_sec))

    return wrapped
