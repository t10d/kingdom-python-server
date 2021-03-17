# kingdom-python-server 🐍

Modular, transparent, batteries (half) included, lightning fast web server. Features a functional, isolated business layer with an imperative decoupled shell.

## Goal

This is intendend as both to serve as a scaffold for our internal projects as to improve and give back to our community as an efficient bullet-proof backend design, leveraging Python's expressability.

## Features

-  Lightning fast ASGI server via `uvicorn`.
-  GraphQL support via `ariadne`.
-  Full GraphQL compliant query pagination support.
-  JWT authentication.
-  Resource-based authorization integrated using GraphQL directives.
-  Efficient dependency management via `poetry` 
-  Database migration systems using `alembic`.
-  Event-driven architecture:
   -  Internal message bus that injects adapters dependencies into service-handlers functions.
   -  External message bus for background workers integrated w/ AWS Lambda.
-  Sober test pyramid: units, integrations and e2e tests.
-  Decoupled service layer that responds only to commands and events.
-  Aggregate's atomic services consistency guaranteed using `postgres` isolation levels locks.
-  Isolated and pure domain layer that has no dependencies (no, not even with ORM).

## Roadmap 

This is project's in its early stages, and should receive a big WIP tag. We should track progress using GitHub features:

1. [Discussions](https://github.com/t10d/kingdom-python-server/discussions) for brainstorming & prioritizing
1. [Milestones](https://github.com/t10d/kingdom-python-server/milestones) for planned features
1. [Issues](https://github.com/t10d/kingdom-python-server/issues/) for ongoing tasks

## Instructions

As it is disclaimed the project current status, running *for now* means making sure tests pass.
We are shortly improving the entire installation experience and usage. Hold tight.

### Step 1: Dependencies & environment

This projects uses `poetry` to manage dependencies.
Having said that, how you instantiate your virtual environment is up to you. You can do that now.

Inside your blank python virtual environment:

```shell
pip install poetry & poetry install
```

### Step 2: Prepare your database

As there aren't any containerization being done for now, you'd need `postgres` up and running in your local machine.

```shell
psql -c "create database template"
```

### Step 3: Test it

Right now you should be able to run the entire test-suite properly.

```shell
make test
```


## Why?

Why not use django? Or flask? Or FastAPI? Even though these are great frameworks they're (mostly heavily) opiniated. At T10, we have a need to implement and deliver maintainable software that we really know what's happening under the (at least conceptual Pythonic-layer) hood.
As a software house, we've also come to find that by using such frameworks programmers are more likely to be inhibited from practicing and improving their software design skills.

We're (obviously) not alone here. [`pca`](https://github.com/pcah/python-clean-architecture) have touched base a few years ago.

## Philosophy

We are committed to these non-negotiables principle:

1. Modularity, high cohesion and low coupling
1. Transparency, ensuring readable, debugabble, maintainable software 
1. Orthogonality, which makes us sane by dilligently avoiding code that emmits side-effects
1. Testability, we need code that can be (as easily as possibly) tested

## Inspiration

We don't claim to have created everything from scratch. Quite the opposite, the work here is a direct fork
from ideas we really identify with that were hard earned throughout the past two decades.

Specifically:

1. Architecture Patterns with Python from Bob Gregory & Harry Percival,
1. Python Clean Architecture, from [`pcah`](https://github.com/pcah)
1. Functional Core, Imperative Shell from Destroy All Software,
1. Hexagonal Architecture aka Ports & Adapters by Alistair Cockburn
1. Domain-Driven-Design by Eric Evans & Martin Fowler
