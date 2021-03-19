from contextvars import ContextVar
from queue import LifoQueue
from threading import get_ident
from typing import Callable, Optional

from opentelemetry import trace
from opentelemetry.exporter.jaeger.proto.grpc import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider, Tracer, Span
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation import SPAN_KEY

from src.observability.tracer import AbstractTracer, AbstractTracerDelegate

jaeger_collector_endpoint = "localhost:14250"
application_name = "default-name"


class JaegerTracerDelegate(AbstractTracerDelegate):
    tracer: Tracer
    span: Optional[Span]
    name: str

    def __init__(self, name: str, tracer: Tracer, parent: Optional['JaegerTracerDelegate']):
        self.name = name
        self.tracer = tracer
        self.span = None if parent is None else parent.span

    def add_property(self, key: str, value: str):
        if self.span is not None:
            self.span.set_attribute(key, value)

    def trace(self, name: str, block: Callable, *args, **kwargs):
        def execute(instance):
            try:
                return block(*args, **kwargs)
            except Exception as ex:
                instance.span_failure(ex, False)

        if self.span is None:
            with self.tracer.start_as_current_span(name) as span:
                self.span = span
                return execute(self)

        ctx = ContextVar(SPAN_KEY)
        ctx.set(self.span)
        with self.tracer.start_span(name, context=ctx) as span:
            self.span = span
            return execute(self)

    def span_failure(self, ex: Exception, expected: bool):
        if self.span is not None:
            self.span.record_exception(ex)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span.is_recording():
            self.span.end()


class JaegerTracer(AbstractTracer):
    """
    The trace itself is tree, and each node is a single span inside the tree. Each delegate can access
    its own span, while the JaegarTracer manage the whole span.

    For concurrent accesses, each jaeger instance will hold its own context. This context will keep
    each span sub-tree isolation, where a sub-tree does not interfere with other sub-trees. If sub-trees
    are spawned concurrently, they will have a common span as parent as will the context.

    If a thread pool is used, this context approach could lead to stranger behaviours?
    """
    tracer: Tracer
    context: dict[str, LifoQueue[AbstractTracerDelegate]]
    root: ContextVar

    def __init__(self):
        trace.set_tracer_provider(
            TracerProvider(
                resource=Resource.create({SERVICE_NAME: application_name})
            )
        )
        self.tracer = trace.get_tracer(application_name)
        self.context = {}
        self.root = ContextVar('parent-root', default=None)
        jaeger_exporter = JaegerExporter(collector_endpoint=jaeger_collector_endpoint, insecure=True)
        trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(jaeger_exporter))

    def _current_name(self) -> str:
        value = self.root.get()
        if value is None:
            return str(get_ident())
        return value

    def for_context(self, context: ContextVar):
        """
        Used for context propagation, this must be handle careful when spawning
        multiple threads and for coroutines, otherwise the spans for a trace could
        be wrong.
        """
        self.root = context
        return self

    def _current_delegates(self) -> LifoQueue[AbstractTracerDelegate]:
        key = self._current_name()
        if key in self.context:
            return self.context[key]
        return LifoQueue()

    def operation_name(self, name: str) -> AbstractTracerDelegate:
        delegates = self._current_delegates()
        last = None if delegates.empty() else delegates.queue[0]
        t = JaegerTracerDelegate(name, self.tracer, last)
        delegates.put_nowait(t)
        self.context[self._current_name()] = delegates
        return t

    def add_property(self, key: str, value: str):
        delegates = self._current_delegates()
        if not delegates.empty():
            last = delegates.queue[delegates.qsize()-1]
            last.add_property(key, value)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        delegates = self._current_delegates()
        if not delegates.empty():
            delegates.get_nowait()
            self.context[self._current_name()] = delegates
        else:
            del self.context[self._current_name()]
