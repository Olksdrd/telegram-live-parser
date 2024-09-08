"""
1. Connect
2. Check connection
3. Create table (in init?)
4. Put one/many
5. Get all
6. Close connection
"""
from abc import ABC, abstractmethod


class Repository[T](ABC):
    """Repository of objects of generic type T"""
    @abstractmethod
    def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def _is_connected(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def put_one(self, object: T) -> str:
        raise NotImplementedError

    # @abstractmethod
    # def put_many(self, objects: list[T]) -> str:
    #     raise NotImplementedError

    # @abstractmethod
    # def get(self, id: str) -> T:
    #     raise NotImplementedError

    # @abstractmethod
    # def get_all(self) -> list[T]:
    #     raise NotImplementedError
