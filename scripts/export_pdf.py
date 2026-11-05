"""Export the project's authored Markdown sources as one searchable PDF."""
import argparse
import hashlib
import re
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, PageBreak, PageTemplate,
                               Paragraph, Spacer, Preformatted, KeepTogether)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT=Path(__file__).resolve().parents[1]
INK=colors.HexColor('#142737')
TEAL=colors.HexColor('#087e8b')
MUTED=colors.HexColor('#536878')
PALE=colors.HexColor('#edf5f6')


def fonts():
    candidates=[
        (Path('C:/Windows/Fonts'),('calibri.ttf','calibrib.ttf','consola.ttf')),
        (Path('/usr/share/fonts/truetype/dejavu'),('DejaVuSans.ttf','DejaVuSans-Bold.ttf','DejaVuSansMono.ttf')),
    ]
    for folder,names in candidates:
        if all((folder/name).exists() for name in names):
            for alias,name in zip(('Body','Bold','Mono'),names):
                pdfmetrics.registerFont(TTFont(alias,str(folder/name)))
            pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')
            return 'Body','Bold','Mono'
    return 'Helvetica','Helvetica-Bold','Courier'


BODY,BOLD,MONO=fonts()
styles={
    'body':ParagraphStyle('body',fontName=BODY,fontSize=10,leading=14,textColor=INK,spaceAfter=7),
    'h1':ParagraphStyle('chapter',fontName=BOLD,fontSize=23,leading=28,textColor=INK,spaceAfter=18,keepWithNext=True),
    'h2':ParagraphStyle('section',fontName=BOLD,fontSize=14,leading=18,textColor=TEAL,spaceBefore=13,spaceAfter=8,keepWithNext=True),
    'h3':ParagraphStyle('subsection',fontName=BOLD,fontSize=11,leading=15,textColor=INK,spaceBefore=10,spaceAfter=6,keepWithNext=True),
    'bullet':ParagraphStyle('bullet',fontName=BODY,fontSize=10,leading=14,textColor=INK,leftIndent=12,firstLineIndent=-10,spaceAfter=5),
    'code':ParagraphStyle('code',fontName=MONO,fontSize=8,leading=11,textColor=INK,backColor=PALE,borderPadding=8,spaceBefore=4,spaceAfter=12),
    'small':ParagraphStyle('small',fontName=BODY,fontSize=8.5,leading=12,textColor=MUTED,spaceAfter=8),
}


def inline(text):
    text=text.replace('\u2011','-').replace('\u2013','-').replace('\u2014','-')
    text=escape(text)
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                lambda m:f'<link href="{m[2]}" color="#087e8b">{m[1]}</link>',text)
    text=re.sub(r'`([^`]+)`',lambda m:f'<font name="{MONO}" size="8.7">{m[1]}</font>',text)
    return re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',text)


class Architecture(Flowable):
    def __init__(self):
        super().__init__()
        self.width=490
        self.height=76

    def draw(self):
        canvas=self.canv
        labels=[('Customer','English conversation'),('Agent','Bounded tool loop'),('Tools','Validated read access'),('Evidence','CSV data + PDF policies')]
        for i,(top,bottom) in enumerate(labels):
            x=i*125
            canvas.setFillColor(PALE)
            canvas.roundRect(x,10,115,60,5,fill=1,stroke=0)
            canvas.setFillColor(TEAL)
            canvas.setFont(BOLD,11)
            canvas.drawCentredString(x+57.5,48,top)
            canvas.setFillColor(MUTED)
            canvas.setFont(BODY,7.5)
            canvas.drawCentredString(x+57.5,29,bottom)
            if i<3:
                canvas.setStrokeColor(TEAL)
                canvas.line(x+117,40,x+123,40)


class Report(BaseDocTemplate):
    def __init__(self,path):
        super().__init__(str(path),pagesize=A4,leftMargin=49,rightMargin=49,
                         topMargin=58,bottomMargin=48,title='Guilherme - AI Engineer - Project README and Documentation',
                         author='Guilherme; implementation and documentation assisted by OpenAI Codex',
                         subject='Artefact technical challenge - Emporio da Musica support agent')
        self.addPageTemplates(PageTemplate(id='main',frames=Frame(49,48,A4[0]-98,A4[1]-106,id='normal',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0),onPage=self.decorate))
        self.heading_counter=0

    def decorate(self,canvas,doc):
        w,h=A4
        canvas.saveState()
        if doc.page==1:
            canvas.setFillColor(TEAL)
            canvas.rect(0,h-16,w,16,fill=1,stroke=0)
        else:
            canvas.setFillColor(MUTED)
            canvas.setFont(BODY,8)
            canvas.drawString(49,h-32,'EMPORIO DA MUSICA  /  TECHNICAL CASE STUDY')
            canvas.setStrokeColor(colors.HexColor('#d9e5e9'))
            canvas.line(49,h-40,w-49,h-40)
        canvas.setFillColor(MUTED)
        canvas.setFont(BODY,8)
        canvas.drawString(49,27,'Guilherme | AI Engineer | 04 November 2026')
        canvas.drawRightString(w-49,27,str(doc.page))
        canvas.restoreState()

    def afterFlowable(self,flowable):
        if isinstance(flowable,Paragraph) and getattr(flowable,'toc_level',None) is not None:
            text=flowable.getPlainText()
            key=f'heading-{self.seq.nextf("heading")}'
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text,key,level=0 if flowable.toc_level==0 else 1,closed=False)
            self.notify('TOCEntry',(flowable.toc_level,text,self.page,key))


def heading(text,style,level=None):
    p=Paragraph(inline(text),styles[style])
    p.toc_level=level
    return p


def markdown(path,example=False):
    story=[]
    lines=path.read_text(encoding='utf-8').splitlines()
    paragraph=[]
    code=[]
    in_code=False
    body_style=styles['body']
    bullet_style=styles['bullet']
    sub_style=styles['h3']
    if example:
        body_style=ParagraphStyle('example-body',parent=styles['body'],fontSize=9.5,leading=12.2,spaceAfter=5)
        bullet_style=ParagraphStyle('example-bullet',parent=styles['bullet'],fontSize=9.5,leading=12.2,spaceAfter=4)
        sub_style=ParagraphStyle('example-label',parent=styles['h3'],fontSize=10,leading=13,spaceBefore=7,spaceAfter=4)
    def flush():
        if paragraph:
            story.append(Paragraph(inline(' '.join(paragraph)),body_style))
            paragraph.clear()
    for line in lines:
        if line.startswith('```'):
            flush()
            if in_code:
                wrapped=[]
                for code_line in code:
                    wrapped.extend(textwrap.wrap(code_line,width=86,replace_whitespace=False,drop_whitespace=False) or [''])
                story.append(Preformatted('\n'.join(wrapped),styles['code']))
                code.clear()
            in_code=not in_code
            continue
        if in_code:
            code.append(line)
            continue
        if line.startswith('# '):
            flush()
            continue
        if line.startswith('### '):
            flush()
            story.append(heading(line[4:],'h3'))
        elif line.startswith('## '):
            flush()
            if example:
                story.append(Paragraph(inline(line[3:]),sub_style))
            else:
                story.append(heading(line[3:],'h2',1))
        elif line.startswith('- '):
            flush()
            story.append(Paragraph('- '+inline(line[2:]),bullet_style))
        elif not line.strip():
            flush()
        else:
            paragraph.append(line.strip())
    flush()
    return story


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'submission.pdf')
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    story=[Spacer(1,50),Paragraph('ARTEFACT / AI ENGINEER',styles['small']),Spacer(1,22),
        Paragraph('AI Customer Support',ParagraphStyle('cover',fontName=BOLD,fontSize=34,leading=40,textColor=INK,spaceAfter=10)),
        Paragraph('README &amp; Documentation',ParagraphStyle('subtitle',fontName=BODY,fontSize=23,leading=30,textColor=TEAL)),
        Spacer(1,20),Paragraph('Emporio da Musica',styles['h2']),
        Paragraph('A read-only agent that connects customer questions to structured operational data and source policies.',styles['body']),
        Spacer(1,26),Architecture(),Spacer(1,27),
        Paragraph('<b>Guilherme</b><br/>AI Engineer - Full-Stack Generative AI Applications',styles['body']),
        Paragraph('04 November 2026',styles['small']),Spacer(1,12),
        Paragraph('Delivery status: working local prototype. Offline behavior and SDK transport tested. Live-model validation and public GitHub publication remain pending.',styles['body']),
        Paragraph('Prepared with OpenAI Codex. The README discloses the scope of AI assistance.',styles['small']),PageBreak(),
        heading('Contents','h1')]
    toc=TableOfContents()
    toc.levelStyles=[ParagraphStyle('toc0',fontName=BOLD,fontSize=11,leading=17,textColor=INK,spaceBefore=10),
                     ParagraphStyle('toc1',fontName=BODY,fontSize=9,leading=13,leftIndent=14,textColor=MUTED)]
    story.extend([toc,PageBreak()])
    for title,path in [('1. Project README',ROOT/'README.md'),('2. Technical Documentation',ROOT/'docs'/'DOCUMENTATION.md'),
                       ('3. Validation Record',ROOT/'docs'/'VALIDATION.md')]:
        story.append(heading(title,'h1',0))
        story.extend(markdown(path))
        story.append(PageBreak())
    story.append(heading('4. Executed Conversation Examples','h1',0))
    story.append(Paragraph('These transcripts were generated by the deterministic offline demo against the real supplied fixtures. They demonstrate tool behavior and policy handling; they are not live-model transcripts.',styles['body']))
    for index,path in enumerate(sorted((ROOT/'examples').glob('*.md'))):
        if index: story.append(PageBreak())
        title=path.read_text(encoding='utf-8').splitlines()[0].lstrip('# ')
        story.append(heading(f'4.{index+1} {title}','h2',1))
        story.extend(markdown(path,example=True))
    doc=Report(args.output)
    doc.multiBuild(story)
    digest=hashlib.sha256(args.output.read_bytes()).hexdigest()
    print(f'Created {args.output.resolve()}\nSHA256 {digest}')


if __name__=='__main__': main()
