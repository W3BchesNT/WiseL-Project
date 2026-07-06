# Compiler/oniLink.py
import subprocess, os, sys, importlib, shutil, glob

# ─── Пути ────────────────────────────────────
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LIBRARY_PATH = os.path.join(CURRENT_DIR, "..", "Library")
CORE_PATH = os.path.join(LIBRARY_PATH, "Core")
WIN_PATH = os.path.join(LIBRARY_PATH, "Windows")
LINUX_PATH = os.path.join(LIBRARY_PATH, "Linux")

for p in [CORE_PATH, WIN_PATH, LINUX_PATH]:
    if p not in sys.path:
        sys.path.insert(0, p)

for p in [LIBRARY_PATH, CORE_PATH, WIN_PATH, LINUX_PATH, CURRENT_DIR]:
    pycache = os.path.join(p, "__pycache__")
    if os.path.exists(pycache):
        shutil.rmtree(pycache, ignore_errors=True)

for mod in ['Console', 'ConsoleGen64', 'Gui', 'GuiGen64']:
    sys.modules.pop(mod, None)

import Console
import ConsoleGen64
import Gui
import GuiGen64

USER_PROFILE = os.environ.get("USERPROFILE", "")
if os.path.exists(os.path.join(USER_PROFILE, "Desktop", "FASM", "fasm.exe")):
    FASM_PATH = os.path.join(USER_PROFILE, "Desktop", "FASM", "fasm.exe")
else:
    FASM_PATH = r"C:\fasm\fasm.exe"

INPUT_FILE = os.path.join("..", "main.wise") if os.path.exists(os.path.join("..", "main.wise")) else "main.wise"
ASM_FILE = "out.asm"
EXE_FILE = "main.exe"


def cleanup_temp_files():
    for pattern in ["img_*.png", "img_*.jpg", "img_*.bmp", "img_*.gif"]:
        for f in glob.glob(pattern):
            try: os.remove(f)
            except: pass


def clean_pycache():
    for p in [LIBRARY_PATH, CORE_PATH, WIN_PATH, LINUX_PATH, CURRENT_DIR]:
        pycache = os.path.join(p, "__pycache__")
        if os.path.exists(pycache):
            shutil.rmtree(pycache, ignore_errors=True)


def build():
    print("=" * 42)
    print("      COMPILING WISEL PROJECT...")
    print("=" * 42)
    
    clean_pycache()
    
    if not os.path.exists(INPUT_FILE):
        print(f" [ERROR] Input file not found: {INPUT_FILE}")
        return
    
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        code = f.read()
    
    print(f" [INFO] Input: {INPUT_FILE}")
    
    asm = ""
    
    if "Use WinX64" in code:
        print(" [INFO] Mode: GUI (WinX64)")
        ast = Gui.parse(code)
        print(f" [INFO] AST nodes: {len(ast)}")
        asm = GuiGen64.generate(ast)
        
    elif "Use ConsoleX64" in code:
        print(" [INFO] Mode: Console (ConsoleX64)")
        ast = Console.parse(code)
        print(f" [INFO] AST nodes: {len(ast)}")
        asm = ConsoleGen64.generate(ast)
        
    else:
        print(" [ERROR] No 'Use WinX64' or 'Use ConsoleX64' found")
        return
    
    if not asm:
        print(" [ERROR] ASM generation failed")
        return
    
    with open(ASM_FILE, "w", encoding="utf-8") as f:
        f.write(asm)
    print(f" [ASM] Generated: {ASM_FILE} ({len(asm)} bytes)")
    
    if os.path.exists(EXE_FILE):
        try: os.remove(EXE_FILE)
        except: pass
    
    subprocess.run(["taskkill", "/f", "/im", EXE_FILE], capture_output=True)
    result = subprocess.run([FASM_PATH, ASM_FILE, EXE_FILE], capture_output=True)
    
    if result.returncode == 0:
        print(f" [SUCCESS] Compiled to {EXE_FILE}")
        cleanup_temp_files()
        return True
    else:
        print(f" [FASM ERROR]\n{result.stderr.decode('cp866', errors='ignore')}")
        print("-" * 42)
        return False


def run():
    if build():
        print(f"\n [RUN] Starting {EXE_FILE}...")
        print("=" * 42)
        subprocess.run([EXE_FILE])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run()
    else:
        build()