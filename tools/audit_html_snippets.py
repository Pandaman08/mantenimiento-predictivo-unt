import re
import os

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

pattern = re.compile(r"st\.markdown\((?P<arg>.*)\)", re.S)
html_open = re.compile(r"<(?P<tag>div|span|section|footer|header|article)[\s>].*", re.I | re.S)
html_close = re.compile(r"</(?P<tag>div|span|section|footer|header|article)>", re.I)

issues = []

for dirpath, dirnames, filenames in os.walk(repo_root):
    for fn in filenames:
        if not fn.endswith('.py'):
            continue
        path = os.path.join(dirpath, fn)
        with open(path, 'r', encoding='utf-8') as f:
            src = f.read()
        for m in re.finditer(r"st\.markdown\((?P<args>.*?)\)", src, re.S):
            args = m.group('args')
            # extract first string literal in args
            s = None
            str_match = re.search(r"([ruRU]?\"\"\".*?\"\"\"|[ruRU]?\'.*?\'|[ruRU]?\".*?\")", args, re.S)
            if str_match:
                s = str_match.group(0)
                # strip quotes
                content = s
                if content.startswith(('r"""', 'R"""', 'u"""', 'U"""')):
                    content = content[4:-3]
                elif content.startswith(('"""', "'''")):
                    content = content[3:-3]
                else:
                    # strip leading char for r/u
                    if content[0].lower() in 'ru':
                        content = content[2:-1]
                    else:
                        content = content[1:-1]
                # check for open tag without close in same string
                opens = html_open.findall(content)
                closes = html_close.findall(content)
                if opens and not closes:
                    issues.append((path, m.start(), 'OPEN_ONLY', content.strip()[:200]))
                if closes and not opens:
                    issues.append((path, m.start(), 'CLOSE_ONLY', content.strip()[:200]))

# print report
if not issues:
    print('No fragmentary HTML invocations found.')
else:
    print('Potential fragmentary HTML usages detected:')
    for p, pos, kind, snippet in issues:
        print(f'- {kind} in {p}:')
        print(f'  snippet: {snippet!r}')
