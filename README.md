📁 WiseL/
│
├── 📄 main.wise                    # Исходный код на языке WiseL
├── 📄 oniCompiler.bat              # Батник для запуска компиляции
│
├── 📁 res/                         # Ресурсы
│   └── 📄 note.ico
│
├── 📁 Compiler/                    # Компилятор
│   ├── 📄 oniLink.py               # Главный движок: парсинг, генерация, FASM
│   ├── 📁 Fasm						# Flat Assembler
│   └── 📁 Macros/WinX64/           # Макросы для FASM
│       ├── 📄 hooks.inc            # Хуки клавиш, таймеры, мышь
│       ├── 📄 vector.inc           # Графические примитивы GDI
│       └── 📄 win64.inc            # Окна, буферизация, WindowProc
│
├── 📁 Library/                     # Библиотеки
│   ├── 📁 Core/                    # Платформонезависимые парсеры
│   │   ├── 📄 Console.py           # Парсер консольного WiseL → AST
│   │   ├── 📄 Gui.py               # Парсер GUI WiseL (окна, виджеты, меню) → AST
│   │   ├── 📄 Values.py            # Парсер переменных (int, string, bool)
│   │   ├── 📄 Conditions.py        # Парсер if/else (заготовка)
│   │   └── 📄 Fluent.py            # Стили, темы, цветовые схемы (заготовка)
│   │
│   ├── 📁 Windows/                 # Генераторы ASM для Windows
│   │   ├── 📄 ConsoleGen64.py      # AST → ASM (консоль)
│   │   └── 📄 GuiGen64.py          # AST → ASM (GUI)
│   │
│   └── 📁 Linux/                   # Linux-реализация (в будущем)
│       └── 📄 Empty
│
└── 📁 Docs/                        # Документация (в будущем)