"""Значения пакетов и зависимостей."""

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Package:
    """Пакет конкретной версии, вершина будущего графа."""

    name: str
    version: str

    @property
    def label(self):
        """Вернуть читаемую подпись вершины."""
        return f"{self.name}@{self.version}"


@dataclass(frozen=True)
class Dependency:
    """Имя зависимости и диапазон из манифеста NuGet."""

    name: str
    constraint: str


class RepositoryError(Exception):
    """Ошибка сети, метаданных или разрешения версии."""
