import threading

from src.observability.decorator import default_tracer, trace, count, default_measurer, observe


@count(name="fibonacci", description="Count how many times Fibonacci was called")
def fib(n):
    if n < 2:
        return n
    return fib(n-1) + fib(n-2)


@trace("fibo")
def middleware(n):
    default_tracer.add_property("nth", str(n))
    return fib(n)


@trace("base")
@observe(name="fibonacci_caller", description="Time took by the caller to execute 10 fibonacci calls")
def traced_function(n):
    for i in range(10):
        multiplier = i + 1
        default_tracer.add_property("idx-" + str(multiplier), str(middleware(n * multiplier)))


if __name__ == '__main__':
    threads = [threading.Thread(target=traced_function, args=(3,)) for _ in range(2)]
    [t.start() for t in threads]
    [t.join() for t in threads]

    print(default_measurer.export().decode('utf-8'))
