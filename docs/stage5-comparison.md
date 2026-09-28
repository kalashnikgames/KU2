# Этап 5: визуализация и сравнение трех пакетов

Проверено 28.09.2026. Целевая платформа `net8.0`, .NET SDK 8.0.425,
Mermaid CLI 12.0.0. PNG действительно отрисованы из сохраненного Mermaid,
а не созданы независимо от его текста. Их корень выделен синим.

| Пакет | Версия | Вершины | Ребра | Результат сравнения |
| --- | --- | --- | --- | --- |
| Newtonsoft.Json | 13.0.3 | 1 | 0 | Нет зависимостей для выбранной платформы. |
| Microsoft.Extensions.Configuration | 8.0.0 | 3 | 3 | Набор, версии и связи совпали. |
| Microsoft.Extensions.Logging | 8.0.0 | 6 | 7 | Набор, версии и связи совпали. |

## Как проводилось сравнение

Для каждого пакета создан отдельный временный проект с единственной
PackageReference и `TargetFramework=net8.0`. Выполнены реальный
`dotnet restore` и штатный `dotnet nuget why`. Наборы вершин и ребер
самостоятельно полученного графа также сверены с `project.assets.json`:
во всех трех случаях равенство обоих наборов подтверждено.

Примеры команд штатной визуализации после восстановления проекта:

```text
dotnet nuget why project.csproj Newtonsoft.Json
dotnet nuget why project.csproj Microsoft.Extensions.Primitives
dotnet nuget why project.csproj Microsoft.Extensions.DependencyInjection.Abstractions
```

Последняя команда для Logging показывает три пути к общей зависимости.
Дополнительно запрошен Primitives, чтобы проверить оставшуюся ветвь.
Это штатное текстовое представление графа NuGet, описанное в
[справке Microsoft](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-nuget-why).

## Полученные деревья dotnet nuget why

Ниже сохранены ветви фактического вывода, без имени временного проекта.

```text
Newtonsoft.Json (v13.0.3)

Microsoft.Extensions.Configuration (v8.0.0)
├─ Microsoft.Extensions.Configuration.Abstractions (v8.0.0)
│  └─ Microsoft.Extensions.Primitives (v8.0.0)
└─ Microsoft.Extensions.Primitives (v8.0.0)

Microsoft.Extensions.Logging (v8.0.0)
├─ Microsoft.Extensions.DependencyInjection (v8.0.0)
│  └─ Microsoft.Extensions.DependencyInjection.Abstractions (v8.0.0)
├─ Microsoft.Extensions.Logging.Abstractions (v8.0.0)
│  └─ Microsoft.Extensions.DependencyInjection.Abstractions (v8.0.0)
└─ Microsoft.Extensions.Options (v8.0.0)
   └─ Microsoft.Extensions.DependencyInjection.Abstractions (v8.0.0)

Microsoft.Extensions.Logging (v8.0.0)
└─ Microsoft.Extensions.Options (v8.0.0)
   └─ Microsoft.Extensions.Primitives (v8.0.0)
```

## Отличия изображения от штатного дерева

Mermaid показывает весь достижимый граф, а `why` — только пути к
запрошенному пакету. Общая зависимость в дереве повторяется на каждом
пути; в Mermaid это одна вершина с несколькими входящими стрелками.
Версии и логические ребра от этого не меняются. Прямое и транзитивное
ребра к Primitives у Configuration присутствуют в обоих представлениях.

При выборе другой платформы, фильтра или конфликтующих диапазонов
результат может отличаться: выбор TFM и версии влияет на `.nuspec`-группу,
а полный решатель конфликтов Restore выходит за рамки реализованного
независимого разрешения каждого ребра. Подробнее в отчете этапа 4.

## Воспроизведение

После установки Mermaid CLI выполните `examples\demo.bat`.
PNG и исходные диаграммы появятся в `output/newtonsoft.*`,
`output/configuration.*`, `output/logging.*`. PNG — бинарные результаты,
поэтому каталог `output` исключен из Git. Исходные конфигурации и код
генерации диаграмм хранятся в репозитории.
