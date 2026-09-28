"""Проверки всех параметров конфигурации."""

import tempfile
import unittest
from pathlib import Path

from src.config import ConfigError, load_settings, validate_values


def valid_values():
    """Вернуть минимальную конфигурацию настоящего NuGet-репозитория."""
    return {
        "package": "Newtonsoft.Json",
        "repository": "https://api.nuget.org/v3/index.json",
        "test_mode": False, "version": "13.0.3", "output": "graph.png",
        "filter": "",
    }


class ConfigTests(unittest.TestCase):
    """Проверить корректные и ошибочные значения каждого поля."""

    def test_all_parameter_errors(self):
        """Каждый обязательный параметр проверяется отдельно."""
        invalid = {
            "package": "bad name", "repository": "not a URL",
            "test_mode": "yes", "version": "latest", "output": "x.txt",
            "filter": False,
        }
        for key, value in invalid.items():
            with self.subTest(key=key):
                values = valid_values()
                values[key] = value
                with self.assertRaises(ConfigError):
                    validate_values(values, Path.cwd())

    def test_missing_or_bad_toml(self):
        """Ошибки чтения и синтаксиса не приводят к traceback."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.toml"
            with self.assertRaises(ConfigError):
                load_settings(path)
            path.write_text("package = [", encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_settings(path)

    def test_relative_paths(self):
        """Пути тестового режима разрешаются от каталога конфигурации."""
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / "repo.json").write_text('{"A": []}', encoding="utf-8")
            values = valid_values()
            values.update(package="A", repository="repo.json", test_mode=True)
            settings = validate_values(values, base)
            self.assertEqual(settings.repository, str(base / "repo.json"))
            self.assertEqual(settings.output, base / "graph.png")


if __name__ == "__main__":
    unittest.main()
