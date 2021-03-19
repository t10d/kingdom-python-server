from typing import Optional

from prometheus_client import Counter, Gauge, Summary, Histogram, CollectorRegistry
from prometheus_client.exposition import choose_encoder

from src.observability.measurer import AbstractMeasurer, AbstractMeasurerDelegate


class PrometheusTracerDelegate(AbstractMeasurerDelegate):
    name: str
    description: str
    counter: Optional[Counter]
    gauge: Optional[Gauge]
    summary: Optional[Summary]
    histogram: Optional[Histogram]
    registry: CollectorRegistry

    def __init__(self, name: str, description: str, registry: CollectorRegistry):
        self.name = name
        self.description = description
        self.registry = registry
        self.counter = None
        self.gauge = None
        self.summary = None
        self.histogram = None

    def count(self):
        if self.counter is None:
            self.counter = Counter(self.name, self.description)
            self.registry.register(self.counter)
        self.counter.inc()

    def inc(self):
        if self.gauge is None:
            self.gauge = Gauge(self.name, self.description)
            self.registry.register(self.gauge)
        self.gauge.inc()

    def dec(self):
        if self.gauge is None:
            self.gauge = Gauge(self.name, self.description)
            self.registry.register(self.gauge)
        self.gauge.dec()

    def observe(self):
        if self.summary is None:
            self.summary = Summary(self.name, self.description)
            self.registry.register(self.summary)
        return self.summary.time()

    def observe_bucket(self):
        if self.histogram is None:
            self.histogram = Histogram(self.name, self.description)
            self.registry.register(self.histogram)
        return self.histogram.time()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class PrometheusMeasurer(AbstractMeasurer):
    context: dict
    registry: CollectorRegistry

    def __init__(self):
        self.context = {}
        self.registry = CollectorRegistry()

    def track_call(self, name: str, description: str) -> AbstractMeasurerDelegate:
        self.context[name] = self.context.get(name, PrometheusTracerDelegate(name, description, self.registry))
        return self.context[name]

    def export(self) -> bytes:
        generate, _ = choose_encoder("")
        return generate(self.registry)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
