"""Порядок загрузки: зависимости предшествуют потребителю."""

import heapq

from src.graph import cycle_paths
from src.models import RepositoryError


class OrderError(RepositoryError):
    """Для циклического графа строгий порядок не существует."""


def reverse_edges(graph):
    """Подготовить число зависимостей и список потребителей каждой вершины."""
    pending = {package: len(children)
               for package, children in graph.edges.items()}
    consumers = {package: [] for package in graph.edges}
    for package, children in graph.edges.items():
        for child in children:
            consumers[child].append(package)
    return pending, consumers


def load_order(graph):
    """Вычислить устойчивый порядок алгоритмом Кана с обратными ребрами."""
    pending, consumers = reverse_edges(graph)
    ready = [package for package, count in pending.items() if not count]
    heapq.heapify(ready)
    ordered = []
    while ready:
        package = heapq.heappop(ready)
        ordered.append(package)
        for consumer in consumers[package]:
            pending[consumer] -= 1
            if not pending[consumer]:
                heapq.heappush(ready, consumer)
    if len(ordered) != len(graph.edges):
        cycles = cycle_paths(graph)
        names = " -> ".join(item.label for item in cycles[0])
        raise OrderError(f"порядок загрузки невозможен: цикл {names}")
    return ordered


def print_load_order(graph):
    """Показать последовательность, включая корневой пакет последним."""
    for position, package in enumerate(load_order(graph), start=1):
        print(f"{position}. {package.label}")
