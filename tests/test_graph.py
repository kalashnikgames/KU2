"""Проверки BFS, фильтра, общих вершин и циклов."""

import unittest

from src.graph import GraphBuilder, cycle_paths
from src.models import Dependency, Package, RepositoryError


class MemoryRepository:
    """Простой источник для проверки порядка запросов BFS."""

    def __init__(self, graph):
        """Сохранить граф и журнал обращений."""
        self.graph = graph
        self.calls = []

    def direct(self, package):
        """Записать обращение и вернуть соседей."""
        self.calls.append(package.name)
        return [Dependency(name, "1.0.0") for name in
                self.graph[package.name]]

    def resolve(self, name, constraint):
        """Всем тестовым вершинам назначить одинаковую версию."""
        return Package(name, "1.0.0")


class GraphTests(unittest.TestCase):
    """Проверить все требуемые формы тестового репозитория."""

    def test_bfs_and_shared_dependency(self):
        """Сначала посещается весь уровень; общая вершина запрашивается раз."""
        repository = MemoryRepository({
            "A": ["B", "C"], "B": ["D"], "C": ["D"], "D": [],
        })
        graph = GraphBuilder(repository, "").build(Package("A", "1.0.0"))
        self.assertEqual(repository.calls, ["A", "B", "C", "D"])
        names = [item.name for item in graph.discovery]
        self.assertEqual(names, repository.calls)

    def test_filter_before_requests(self):
        """Исключенная вершина и ее поддерево не запрашиваются."""
        repository = MemoryRepository({"A": ["B", "C"], "B": ["D"], "C": []})
        graph = GraphBuilder(repository, "b").build(Package("A", "1.0.0"))
        self.assertEqual(repository.calls, ["A", "C"])
        self.assertEqual([item.name for item in graph.discovery], ["A", "C"])

    def test_cycle_and_self_loop(self):
        """Циклы сохраняют ребра, но не приводят к повторным запросам."""
        for data in ({"A": ["B"], "B": ["A"]}, {"A": ["A"]}):
            repository = MemoryRepository(data)
            graph = GraphBuilder(repository, "").build(Package("A", "1.0.0"))
            self.assertTrue(cycle_paths(graph))
            self.assertEqual(len(repository.calls), len(data))

    def test_isolated_and_excluded_root(self):
        """Одиночный пакет допустим; исключенный корень дает ошибку."""
        repository = MemoryRepository({"A": []})
        graph = GraphBuilder(repository, "").build(Package("A", "1.0.0"))
        self.assertEqual(graph.edges[graph.root], [])
        with self.assertRaises(RepositoryError):
            GraphBuilder(repository, "A").build(Package("A", "1.0.0"))


if __name__ == "__main__":
    unittest.main()
