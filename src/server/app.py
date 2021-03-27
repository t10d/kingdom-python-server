import starlette.middleware  # type: ignore
import starlette.middleware.cors  # type: ignore
import starlette.routing  # type: ignore
from starlette.applications import Starlette  # type: ignore
from typing import Dict
from logging import getLogger

from src import config
from src.federation import init



def create_app() -> starlette.applications.Starlette:
    """
    Imports all resolvers and schema-bindings and mounts
    it into a Starlette app
    """
    from src.server.graphql import create_graphql_asgi_wrapper

    origins = [
        "http://localhost:3000",
        "https://localhost:3000",
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
    "local": dict(start_orm=True,),
    "sandbox": dict(start_orm=True,),
    "staging": dict(start_orm=True),
    "prod": dict(start_orm=True),
}

ENVIRONMENT = config.current_environment()
logger = getLogger(__name__)
logger.info(f"Kingdom Server @ {ENVIRONMENT}")
init(**params[ENVIRONMENT])

app = create_app()
