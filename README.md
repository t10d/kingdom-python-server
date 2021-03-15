# Kingdom Python Webserver

Modular, batteries included, transparent and fast web server. Functional, isolated business layer with an imperative decoupled shell.

## Goal

This is intendend as both to serve as a scaffold for our internal projects as to improve and give back to our community as an efficient bullet-proof backend design, leveraging Python's expressability.

## Features

-  Lightning ASGI server via `uvicorn`.
-  GraphQL support via `ariadne`.
-  Full GraphQL compliant query pagination support.
-  JWT authentication.
-  Resource-based authorization integrated using GraphQL directives.
-  Efficient dependency management via `poetry` 
-  Migration systems using `alembic`.
-  Internal message bus that centers independency injection adapters.
-  External message bus for background workers integrated w/ AWS Lambda.
-  Sober test pyramid: units, integrations and e2e tests.
-  Decoupled service layer that responds only to commands and events.
-  Aggregate's atomic services consistency guaranteed using `postgres` locks.
-  Isolated and pure domain layer that has no dependencies (no, not even ORM).


## Why?

Why not use django? Or flask? Or FastAPI? Because these are great but heavily opiniated frameworks. We have a need to implement and deliver maintainable software we really know what's happening under the hood. 
As a software house, we've come to find that by using such frameworks tends to inhibit programmers from practicing and improving their design skills.

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
