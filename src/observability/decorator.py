from contextvars import ContextVar
from functools import wraps
from threading import get_ident
from typing import Callable

from src.observability.measure.prometheus import PrometheusMeasurer
from src.observability.trace.jaeger import JaegerTracer

default_tracer = JaegerTracer()
default_measurer = PrometheusMeasurer()
ctx = ContextVar('parent-trace', default=str(get_ident()))


def trace(name: str = ""):
    def block(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            ctx.set(str(get_ident()))
            operation = name if name.strip() else fn.__name__
            with default_tracer.for_context(ctx) as t:
                with t.operation_name(operation) as tracer:
                    return tracer.trace(operation, fn, *args, **kwargs)

        return wrapper
    return block


def _measuring(name: str, description: str, measure: Callable):
    def block(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            operation = name if name.strip() else fn.__name__
            with default_measurer.track_call(operation, description) as delegate:
                measure(delegate)
                return fn(*args, **kwargs)
        return wrapper
    return block


def _collecting(name: str, description: str, collect: Callable):
    def block(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            operation = name if name.strip() else fn.__name__
            with default_measurer.track_call(operation, description) as delegate:
                with collect(delegate):
                    return fn(*args, **kwargs)
        return wrapper
    return block


def count(name: str = "", description: str = ""):
    return _measuring(name, description, lambda d: d.count())


def inc(name: str = "", description: str = ""):
    return _measuring(name, description, lambda d: d.inc())


def dec(name: str = "", description: str = ""):
    return _measuring(name, description, lambda d: d.dec())


def observe(name: str = "", description: str = ""):
    return _collecting(name, description, lambda d: d.observe())


def observe_bucket(name: str = "", description: str = ""):
    return _collecting(name, description, lambda d: d.observe_bucket())
