import starlette.middleware  # type: ignore
import starlette.middleware.cors  # type: ignore
import starlette.routing  # type: ignore
from starlette.applications import Starlette  # type: ignore
from typing import Dict
from logging import getLogger

from apolo import config
from craftship.federation import federation

from tests.fakes import management


def create_app() -> starlette.applications.Starlette:
    """
    Imports all resolvers and schema-bindings and mounts
    it into a Starlette app
    """
    from server.graphql import create_graphql_asgi_wrapper

    origins = [
        "http://localhost:3000",
        "https://localhost:3000",
        "http://apolo-sandbox.nplbrasil.com.br",
        "https://apolo-sandbox.nplbrasil.com.br",
        "http://apolo-staging.nplbrasil.com.br",
        "https://apolo-staging.nplbrasil.com.br",
    ]

    GraphQLApp = create_graphql_asgi_wrapper(debug=False)
    return Starlette(
        middleware=[
            starlette.middleware.Middleware(
                starlette.middleware.cors.CORSMiddleware,
                allow_origins=origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        ],
        routes=[starlette.routing.Mount("/", GraphQLApp)],
    )


params: Dict[str, Dict] = {
    "local": dict(start_orm=True, digesto=management.FakeDigestoService),
    "sandbox": dict(start_orm=True, digesto=management.FakeDigestoService),
    "staging": dict(start_orm=True),
    "prod": dict(start_orm=True),
}

ENVIRONMENT = config.current_environment()
logger = getLogger(__name__)
logger.info(f"Apolo Server @ {ENVIRONMENT}")
federation(**params[ENVIRONMENT])

app = create_app()
