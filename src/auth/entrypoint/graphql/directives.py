from typing import Union
from enum import Enum
from ariadne import (
    SchemaDirectiveVisitor,
)
from graphql import (
    GraphQLField,
    GraphQLObjectType,
    GraphQLInterfaceType,
    default_field_resolver,
    GraphQLError,
)


from craftship.auth.entrypoint import uow
from craftship.auth.services import handlers


class NeedsPermissionDirective(SchemaDirectiveVisitor):
    def visit_field_definition(
        self,
        field: GraphQLField,
        object_type: Union[GraphQLObjectType, GraphQLInterfaceType],
    ) -> GraphQLField:
        resource: str = self.args.get("resource")
        action: str = self.args.get("action")
        original_resolve = field.resolve or default_field_resolver

        async def resolve_permission(obj, info, **kwargs):
            access_key = info.context["access_key"]
            try:
                permission = handlers.verify_user_permission(
                    access_key=access_key,
                    action=action,
                    resource=resource,
                    uow=uow,
                )
            except (handlers.NotAllowed, handlers.UnknownUser) as ex:
                return GraphQLError(ex.message)
            info.context["permission"] = permission
            return await original_resolve(obj, info, **kwargs)

        field.resolve = resolve_permission
        return field


directives = {"needsPermission": NeedsPermissionDirective}
