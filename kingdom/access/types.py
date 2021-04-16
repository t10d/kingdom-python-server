from typing import Dict, List, Optional, Tuple

# Pure.
ResourceAlias = str
Selector = str
PermissionInt = int
UserKey = str
JWT = bytes

# Derived.
SelectorPermissionMap = Dict[Selector, PermissionInt]
PolicyContext = Dict[ResourceAlias, SelectorPermissionMap]
Scope = List[Selector]
AuthResponse = Tuple[Scope, UserKey]
Payload = Dict
