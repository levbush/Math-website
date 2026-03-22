import re
from pylatexenc.latex2text import LatexNodes2Text


LATEX_TRANSLATOR = LatexNodes2Text(keep_braced_groups=True, strict_latex_spaces=False)


def latex_to_text(expr: str):
    expr = expr.replace("\n", "__LINEBREAK__")
    text = LATEX_TRANSLATOR.latex_to_text(expr)

    text = re.sub(r'(?<!\s)([∈≤≥<>])', r' \1', text)
    text = re.sub(r'([∈≤≥<>])(?!\s)', r'\1 ', text)

    text = re.sub(r'\s+', ' ', text)

    sum_pattern = r'\\sum_\{([^}]+)\}\^\{([^}]+)\}|\\sum_\{([^}]+)\}\^(\S+)'
    matches = re.findall(sum_pattern, expr)

    for m in matches:
        lower = m[0] or m[2]
        upper = m[1] or m[3]
        lower = lower.strip()
        upper = upper.strip()
        upper = upper.replace(r'\infty', '∞')

        if '=' in lower:
            var, val = [x.strip() for x in lower.split('=')]
            formatted = f"∑_({var}={val})^({upper}) "
        else:
            formatted = f"∑_({lower})^({upper}) "

        orig = r"\sum_{" + lower + r"}^" + (f"{{{upper}}}" if '{' in expr else upper)
        broken = LATEX_TRANSLATOR.latex_to_text(orig)
        text = text.replace(broken, formatted)
    text = text.replace("__LINEBREAK__", '\n')

    return text.strip()


def stats_to_text(stats: dict[str, int]):
    return '\n'.join([f'{k}: {v}' for k, v in stats.items()]) + f'\nTotal: {sum(v for v in list(stats.values())[-10:])}'
