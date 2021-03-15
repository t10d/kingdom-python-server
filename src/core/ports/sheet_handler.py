import abc
from typing import Dict, List


class AbstractSheetHandler(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def read(
        self,
        content: bytes,
        keys_map: Dict,
    ) -> List:
        raise NotImplementedError
