import abc
from typing import Callable, Dict, List, Union, Optional


class AbstractDigestoService(abc.ABC):
    client: Callable
    base_url: str

    @abc.abstractmethod
    def registry_process_monitoring(self, process_number: str) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def get_pub_source(self, source_id: int) -> Optional[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_subjects(self, ids: List[int]) -> List[Dict]:
        raise NotImplementedError
