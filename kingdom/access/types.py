from typing import Dict, List, Optional, Tuple

ResourceAlias = str
Selector = str
PermissionInt = int
SelectorPermissionMap = Dict[Selector, PermissionInt]
PolicyContext = Dict[ResourceAlias, SelectorPermissionMap]

Scope = List[Selector]
Payload = Dict
JWT = bytes
