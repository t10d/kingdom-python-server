from ariadne import (
    asgi,
    load_schema_from_path,
    make_executable_schema,
    snake_case_fallback_resolvers,
)

import craftship.auth.config
import craftship.management.config

import craftship.auth.entrypoint.graphql.resolvers
import craftship.management.entrypoint.graphql.resolvers

import craftship.auth.entrypoint.graphql.directives
import craftship.auth.entrypoint.graphql.middlewares

from ariadne.types import (  # type: ignore
    GraphQLError,
    GraphQLResolveInfo,
    Resolver,
    Extension,
    ContextValue,
)

bindings = (
    *craftship.auth.entrypoint.graphql.resolvers.bindings,
    *craftship.management.entrypoint.graphql.resolvers.bindings,
)
schemas = (
    *craftship.auth.config.SCHEMA_PATHS,
    *craftship.management.config.SCHEMA_PATHS,
)
directives = {**craftship.auth.entrypoint.graphql.directives.directives}
middlewares = [*craftship.auth.entrypoint.graphql.middlewares.middlewares]


def create_graphql_asgi_wrapper(debug: bool = False) -> asgi.GraphQL:
    """Loads all schemas files and binds all resolvers to an ariadne ASGI's
    wrapper that is be binded to Starlette's ASGI implementation"""
    type_defs = [load_schema_from_path(schema) for schema in schemas]
    schema = make_executable_schema(
        type_defs,
        snake_case_fallback_resolvers,
        *bindings,
        directives=directives
    )
    return asgi.GraphQL(
        schema,
        debug=debug,
        middleware=middlewares,
    )
