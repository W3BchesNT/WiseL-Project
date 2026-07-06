# Структура проекта WiseL-Project

```text
📁 WiseL-Project/
│
├── 📁 Compiler/                     # Компилятор
│
├── 📁 Docs/                         # Документация (в будущем)
│
├── 📁 Library/                      # Библиотеки
│   ├── 📁 Core/                     # Платформонезависимые парсеры
│   │   ├── 📄 Console.py            # Парсер консольного WiseL → AST
│   │   ├── 📄 Gui.py                # Парсер GUI WiseL (окна, виджеты, меню) → AST
│   │   ├── 📄 Values.py             # Парсер переменных (int, string, bool)
│   │   ├── 📄 Conditions.py         # Парсер if/else (заготовка)
│   │   └── 📄 Fluent.py             # Стили, темы, цветовые схемы (заготовка)
│   │
│   ├── 📁 Windows/                  # Генераторы ASM для Windows
│   │   ├── 📄 ConsoleGen64.py       # AST → ASM (консоль)
│   │   └── 📄 GuiGen64.py           # AST → ASM (GUI)
│   │
│   └── 📁 Linux/                    # Linux-реализация (в будущем)
│       └── 📄 Empty                 # Пусто
│
├── 📁 WiseL-Project/                # Вложенная папка проекта
│
├── 📁 res/                          # Ресурсы
│
├── 📄 LICENSE                       # Лицензия проекта
├── 📄 README.md                     # Описание репозитория (этот файл)
├── 📄 ie4uinit.exe -show.bat        # Скрипт очистки/обновления иконок
├── 📄 main.wise                     # Исходный код на языке WiseL
├── 📄 oniCompiler.bat               # Батник для запуска компиляции
├── 📄 oniOutBuild.bat               # Батник для сборки готового файла
├── 📄 out.asm                       # Выходной файл ассемблера
└── 📄 test.txt                      # Тестовый текстовый файл
```
