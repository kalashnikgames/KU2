"""Проверки зависимостей перед потребителем и невозможности циклов."""

import unittest

from src.graph import GraphBuilder
from src.models import Package
from src.ordering import OrderError, load_order
from tests.test_graph import MemoryRepository


class OrderTests(unittest.TestCase):
    """Проверить общий потомок, независимые ветви и циклы."""

    def test_dependencies_before_consumers(self):
        """Каждое ребро направлено от более позднего пакета к раннему."""
        repository = MemoryRepository({
            "A": ["B", "C"], "B": ["D"], "C": ["D", "E"],
            "D": [], "E": [],
        })
        graph = GraphBuilder(repository, "").build(Package("A", "1.0.0"))
        order = load_order(graph)
        positions = dict((package, position)
                         for position, package in enumerate(order))
        for package, children in graph.edges.items():
            for child in children:
                self.assertLess(positions[child], positions[package])
        self.assertEqual(order[-1], graph.root)

    def test_isolated_and_cycle(self):
        """Одиночная вершина допустима, цикл не выдает ложного порядка."""
        root = Package("A", "1.0.0")
        repository = MemoryRepository({"A": []})
        graph = GraphBuilder(repository, "").build(root)
        self.assertEqual(load_order(graph), [root])
        cyclic = MemoryRepository({"A": ["B"], "B": ["A"]})
        with self.assertRaises(OrderError):
            load_order(GraphBuilder(cyclic, "").build(root))


if __name__ == "__main__":
    unittest.main()
