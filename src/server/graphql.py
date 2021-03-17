from ariadne import (
    asgi,
    load_schema_from_path,
    make_executable_schema,
    snake_case_fallback_resolvers,
)

import src.auth.config

import src.auth.entrypoint.graphql.resolvers

import src.auth.entrypoint.graphql.directives
import src.auth.entrypoint.graphql.middlewares

from ariadne.types import (  # type: ignore
    GraphQLError,
    GraphQLResolveInfo,
    Resolver,
    Extension,
    ContextValue,
)

bindings = (
    *src.auth.entrypoint.graphql.resolvers.bindings,
)
schemas = (
    *src.auth.config.SCHEMA_PATHS,
)
directives = {**src.auth.entrypoint.graphql.directives.directives}
middlewares = [*src.auth.entrypoint.graphql.middlewares.middlewares]


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
