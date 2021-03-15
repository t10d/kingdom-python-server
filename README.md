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


## Why?

Why not use django? Or flask? Or FastAPI? Even though these are great frameworks they're (mostly heavily) opiniated. At T10, we have a need to implement and deliver maintainable software that we really know what's happening under the (at least conceptual Pythonic-layer) hood.
As a software house, we've also come to find that by using such frameworks programmers are more likely to be inhibited from practicing and improving their software design skills.

## Philosophy

We are committed to these non-negotiables principle:

1. Modularity, high cohesion and low coupling
1. Transparency, ensuring readable, debugabble, maintainable software 
1. Orthogonality, which makes us sane by dilligently avoiding code that emmits side-effects
1. Testability, we need code that can be (as easily as possibly) tested

## Inspiration

We don't claim to have created everything from scratch. Quite the opposite, all of these are inspirations from elsewhere.

Specifically:

1. Architecture Patterns with Python from Bob Gregory & Harry Percival,
1. Functional Core, Imperative Shell from Destroy All Software,
1. Hexagonal Architecture aka Ports & Adapters
