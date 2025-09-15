import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXTS = {'.py', '.js', '.css', '.html'}

def strip_py(text: str) -> str:
    out = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if i == 0 and line.startswith('#!'):
            out.append(line)
            continue
        if re.match(r"^\s*#", line):
            continue
        out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")

def strip_js(text: str) -> str:
    def repl_block(m):
        blk = m.group(0)
        if 'INLINE_CSS' in blk or 'INLINE_JS' in blk:
            return blk
        return ''
    text = re.sub(r"/\*[\s\S]*?\*/", repl_block, text)
    lines = text.splitlines()
    out = []
    for line in lines:
        if re.match(r"^\s*//", line):
            continue
        out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")

def strip_css(text: str) -> str:
    return re.sub(r"/\*[\s\S]*?\*/", "", text)

def strip_html(text: str) -> str:
    return re.sub(r"<!--[\s\S]*?-->", "", text)

def process(path: Path):
    text = path.read_text(encoding='utf-8', errors='ignore')
    orig = text
    if path.suffix == '.py':
        text = strip_py(text)
    elif path.suffix == '.js':
        text = strip_js(text)
    elif path.suffix == '.css':
        text = strip_css(text)
    elif path.suffix == '.html':
        text = strip_html(text)
    if text != orig:
        path.write_text(text, encoding='utf-8')
        return True
    return False

def main():
    changed = 0
    for p in ROOT.rglob('*'):
        if not p.is_file():
            continue
        if p.suffix.lower() in EXTS:
            if process(p):
                changed += 1
    print(f"Stripped comments in {changed} files.")

if __name__ == '__main__':
    main()

