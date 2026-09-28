# Этап 4: сравнение порядка с NuGet

Проверено 28.09.2026 на Windows, .NET SDK 8.0.425, NuGet из этого SDK,
проект `net8.0`, пакет `Microsoft.Extensions.Logging` версии `8.0.0`.
Менеджер использован только для сравнения. Код инструмента получает
граф самостоятельно из HTTP JSON и XML, не читая результаты Restore.

## Команды

```text
python -B -m src.cli examples/logging.toml --load-order
dotnet restore project.csproj --configfile NuGet.Config --verbosity normal
```

Во временном проекте была одна PackageReference на Logging 8.0.0.
Источник NuGet.Config: https://api.nuget.org/v3/index.json.
При сравнении использовался отдельный пустой каталог пакетов.

## Полученный результат инструмента

Все версии ниже — `8.0.0`. Порядок включает сам корневой пакет:

1. Microsoft.Extensions.DependencyInjection.Abstractions
2. Microsoft.Extensions.DependencyInjection
3. Microsoft.Extensions.Logging.Abstractions
4. Microsoft.Extensions.Primitives
5. Microsoft.Extensions.Options
6. Microsoft.Extensions.Logging

Все зависимости предшествуют пакетам, которые их используют.
Независимые готовые вершины упорядочены по имени.

## Фактический вывод Restore

События `Installed` в журнале штатного менеджера пришли в порядке:

1. Microsoft.Extensions.Primitives
2. Microsoft.Extensions.Logging
3. Microsoft.Extensions.DependencyInjection.Abstractions
4. Microsoft.Extensions.DependencyInjection
5. Microsoft.Extensions.Options
6. Microsoft.Extensions.Logging.Abstractions

Первым запросом `.nupkg` был Logging, затем его прямые зависимости.
Файл `project.assets.json` содержал те же шесть пакетов версии 8.0.0
и те же связи для `net8.0`. Восстановление завершилось без ошибок.

## Объяснение различий

Наш порядок — топологический план использования пакетов: сначала
зависимости, потом потребители. Restore сначала загружает корневой
архив, чтобы узнать зависимости, и выполняет сетевые запросы и запись
пакетов параллельно. Поэтому последовательность событий `Installed`
не является таким планом и может меняться между запусками.

На этом примере набор пакетов и версии совпали. Для конфликтующих
диапазонов инструмент хранит разные версии как разные вершины и
разрешает каждое ребро независимо. NuGet Restore применяет правила
разрешения конфликтов ко всему проекту; такие случаи могут дать другой
итоговый набор. Исключающие фильтры также намеренно меняют граф.

Для `test.toml`, `filter.toml`, `isolated.toml` порядок получен.
Для `cycle.toml` и `self.toml` показана ошибка: строгий порядок загрузки
при циклических зависимостях не существует.

Справка: [правила NuGet](https://learn.microsoft.com/en-us/nuget/concepts/dependency-resolution).
