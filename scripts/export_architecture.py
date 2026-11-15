"""Export PDF de l'architecture Markdown : python scripts/export_architecture.py.

Dépendance documentaire facultative : pip install -r requirements-docs.txt.
Les sauts de page et le schéma sont lus dans le Markdown source.
"""
from pathlib import Path
from html import escape
import re

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Flowable

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/architecture/architecture.md'
OUTPUT = SOURCE.with_suffix('.pdf')


class Diagram(Flowable):
    """Disposition du parcours RAG ; libellés et arêtes lus dans le Mermaid."""
    def __init__(self, source):
        super().__init__()
        self.width, self.height = 483, 230
        self.labels = dict(re.findall(r'(\w+)\[\(?([^\]\n]+?)\)?\]', source))
        self.edges = re.findall(r'^\s*(\w+)(?:\[[^\n]*?\])?\s*-->\s*(\w+)', source, re.M)
        self.positions = {'DOC': (0, 190), 'ING': (0, 142), 'EP': (0, 94),
                          'DB': (254, 94), 'USER': (254, 190), 'EQ': (254, 142),
                          'CTX': (254, 46), 'LLM': (0, 46), 'REP': (0, 0)}
        if set(self.labels) != set(self.positions):
            raise ValueError('Adapter la disposition au nouveau schéma Mermaid.')

    def draw(self):
        c = self.canv
        w, h = 228, 32
        c.setStrokeColor(colors.HexColor('#60758a'))
        for start, end in self.edges:
            x, y = self.positions[start]
            tx, ty = self.positions[end]
            if y == ty:
                a, b = ((x + w, y + h / 2), (tx, ty + h / 2)) if tx > x else ((x, y + h / 2), (tx + w, ty + h / 2))
            else:
                a, b = (x + w / 2, y), (tx + w / 2, ty + h)
            c.line(*a, *b)
            bx, by = b
            if y != ty:
                c.line(bx, by, bx - 3, by + 5); c.line(bx, by, bx + 3, by + 5)
            else:
                dx = -5 if tx > x else 5
                c.line(bx, by, bx + dx, by - 3); c.line(bx, by, bx + dx, by + 3)
        style = ParagraphStyle('box', fontSize=9, leading=10, alignment=1)
        for node, (x, y) in self.positions.items():
            c.setFillColor(colors.HexColor('#edf3f8'))
            c.roundRect(x, y, w, h, 5, fill=1)
            p = Paragraph(escape(self.labels[node]), style)
            _, ph = p.wrap(w - 12, h)
            p.drawOn(c, x + 6, y + (h - ph) / 2)


def footer(canvas, doc):
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#60758a'))
    canvas.drawString(56, 29, 'ASL-IA | Halil ERGEN et Gabriel SCAVONE | Cadrage J1')
    canvas.drawRightString(A4[0] - 56, 29, str(doc.page))


def main():
    styles = getSampleStyleSheet()
    styles['Normal'].fontSize = 10
    styles['Normal'].leading = 13.5
    styles['Normal'].spaceAfter = 9
    styles['Heading1'].fontSize = 17
    styles['Heading2'].fontSize = 13
    blocks = SOURCE.read_text(encoding='utf-8').split('\n\n')
    story = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block == '<!-- pagebreak -->':
            story.append(PageBreak())
        elif block.startswith('```mermaid'):
            story.extend([Diagram(block), Spacer(1, 8)])
        else:
            level = 'Heading2' if block.startswith('## ') else 'Heading1' if block.startswith('# ') else 'Normal'
            text = re.sub(r'^#{1,2} ', '', block).replace('\n', ' ')
            text = re.sub(r'`([^`]+)`', r'\1', text)
            story.append(Paragraph(escape(text), styles[level]))
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=56, leftMargin=56,
                            topMargin=42, bottomMargin=44,
                            title='Architecture RAG — J1', author='Halil ERGEN et Gabriel SCAVONE')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == '__main__':
    main()
