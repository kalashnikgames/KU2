"""Проверки самостоятельного чтения NuGet-метаданных."""

import unittest
from unittest.mock import patch

from src.manifest import parse_manifest
from src.models import Package, RepositoryError
from src.repository import NugetRepository, validate_test_graph
from src.versions import normalize_version, resolve_version, satisfies


MANIFEST = b'''<package xmlns="urn:nuget"><metadata><dependencies>
<group targetFramework=".NETStandard2.0">
<dependency id="Old" version="1.0"/></group>
<group targetFramework="net8.0">
<dependency id="B" version="[2.0,3.0)"/></group>
</dependencies></metadata></package>'''


class ManifestTests(unittest.TestCase):
    """Проверить XML, выбор группы и запрос конкретной версии."""

    def test_framework_selection(self):
        """Выбирается одна подходящая группа, а не объединение всех TFM."""
        dependencies = parse_manifest(MANIFEST, "net8.0")
        self.assertEqual([item.name for item in dependencies], ["B"])
        self.assertEqual(dependencies[0].constraint, "[2.0,3.0)")

    def test_exact_manifest_url(self):
        """Запрос идет к версии из конфигурации и кэшируется в памяти."""
        repository = NugetRepository("https://example.org/flat/", "net8.0")
        package = Package("Example.Package", "01.2.0+build")
        with patch("src.repository.fetch_bytes") as fetch:
            fetch.return_value = MANIFEST
            repository.direct(package)
            repository.direct(package)
        fetch.assert_called_once_with(
            "https://example.org/flat/"
            "example.package/1.2.0/example.package.nuspec"
        )

    def test_invalid_metadata(self):
        """Ошибочный XML и тестовый граф дают предметную ошибку."""
        with self.assertRaises(RepositoryError):
            parse_manifest(b"<broken", "net8.0")
        with self.assertRaises(RepositoryError):
            validate_test_graph({"A": ["B"]})


class VersionTests(unittest.TestCase):
    """Проверить минимумы, интервалы и предварительные версии NuGet."""

    def test_bounds_and_normalization(self):
        """Границы включаются только в соответствии со скобками."""
        self.assertTrue(satisfies("2.0.0", "[2.0,3.0)"))
        self.assertFalse(satisfies("3.0.0", "[2.0,3.0)"))
        self.assertFalse(satisfies("2.0.0-beta", "2.0.0"))
        self.assertEqual(normalize_version("01.2+meta"), "1.2.0")

    def test_lowest_applicable_version(self):
        """Выбирается минимальная подходящая версия, не последняя."""
        result = resolve_version(["3.0.0", "2.2.0", "2.1.0"], "[2.0,3.0)")
        self.assertEqual(result, "2.1.0")
        with self.assertRaises(RepositoryError):
            resolve_version(["1.0.0"], "[2.0,3.0)")


if __name__ == "__main__":
    unittest.main()
