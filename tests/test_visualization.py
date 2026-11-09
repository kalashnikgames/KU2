"""Проверки Mermaid и настоящей PNG-отрисовки."""

import tempfile
import unittest
from pathlib import Path

from src.graph import GraphBuilder
from src.models import Dependency, Package
from src.visualization import (
    RenderError, png_size, renderer_command, save_visualization, to_mermaid,
)
from tests.test_graph import MemoryRepository
from src.versions import constraint_predicate


class ConstraintRepository:
    """Вернуть несколько условий для одной и той же вершины."""

    def direct(self, package):
        """Задать более строгое требование на втором пути к B."""
        dependencies = {
            "A": [Dependency("B", "8.0"), Dependency("C", "1.0")],
            "B": [],
            "C": [Dependency("B", "8.1")],
        }
        return dependencies[package.name]

    def resolve(self, name, constraint):
        """Имитировать доступную версию выше обеих нижних границ."""
        return Package(name, "8.2" if name == "B" else "1.0")


def rendering_available():
    """Проверить наличие внешнего рендерера для интеграционного теста."""
    try:
        renderer_command()
    except RenderError:
        return False
    return True


class VisualizationTests(unittest.TestCase):
    """Проверить полноту текста и PNG, а не только успешный запуск."""

    def test_mermaid_preserves_cycles(self):
        """В Mermaid присутствуют обе вершины и все циклические ребра."""
        repository = MemoryRepository({"A": ["B"], "B": ["A"]})
        graph = GraphBuilder(repository, "").build(Package("A", "1.0.0"))
        source = to_mermaid(graph)
        self.assertIn('N0["A<br/>=1.0.0"]', source)
        self.assertIn("N0 --> N1", source)
        self.assertIn("N1 --> N0", source)

    def test_mermaid_uses_strongest_requirement(self):
        """На итоговом графе видна граница, а не выбранная версия."""
        graph = GraphBuilder(ConstraintRepository(), "").build(
            Package("A", "1.0")
        )
        source = to_mermaid(graph)
        self.assertIn('N0["A<br/>=1.0.0"]', source)
        self.assertIn('N1["B<br/>&gt;=8.1"]', source)
        self.assertNotIn("8.2", source)
        self.assertIn("N0 --> N1", source)
        self.assertIn("N2 --> N1", source)

    def test_predicate_intersects_both_bounds(self):
        """Строгость учитывает верхнюю границу и открытый конец."""
        self.assertEqual(
            constraint_predicate(["[8.0,9.0)", "(8.1,8.8]"]),
            ">8.1, <=8.8",
        )
        self.assertEqual(constraint_predicate(["[8.1]"]), "=8.1")
        self.assertEqual(constraint_predicate(["*"]), "*")

    def test_reject_invalid_png(self):
        """Файл другого формата не считается готовым изображением."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.png"
            path.write_bytes(b"not PNG")
            with self.assertRaises(RenderError):
                png_size(path)

    @unittest.skipUnless(rendering_available(), "выполните npm install")
    def test_actual_png_render(self):
        """Настоящий Mermaid CLI создает PNG с ненулевыми размерами."""
        repository = MemoryRepository({"A": ["B"], "B": []})
        graph = GraphBuilder(repository, "").build(Package("A", "1.0.0"))
        with tempfile.TemporaryDirectory() as directory:
            source, output = save_visualization(
                graph, Path(directory) / "actual.png"
            )
            width, height = png_size(output)
            self.assertTrue(width and height)
            self.assertTrue(source.is_file())


if __name__ == "__main__":
    unittest.main()
