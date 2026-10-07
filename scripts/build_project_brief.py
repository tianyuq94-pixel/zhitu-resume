"""Public English project brief. Only approved biography and synthetic screenshots."""
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.lib.enums import TA_LEFT
from shutil import copyfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf/tianyu-qi-project-brief.pdf'
OUT.parent.mkdir(parents=True,exist_ok=True)
W,H=595.28,841.89
INK=HexColor('#213c34'); MUTED=HexColor('#4e655a'); PAPER=HexColor('#f7f8f2'); LINE=HexColor('#d4ddce'); SAGE=HexColor('#e5edda')
c=Canvas(str(OUT),pagesize=(W,H))
c.setTitle('Tianyu Qi | Applied AI Project Brief');c.setAuthor('Tianyu Qi');c.setSubject('AI-assisted application portfolio, October 2026')
BASE='https://www.zhitucv.online'
def text(value,x,y,width=499,size=10,leading=None,bold=False,color=INK):
    p=Paragraph(value,ParagraphStyle('p',fontName='Helvetica-Bold' if bold else 'Helvetica',fontSize=size,leading=leading or size*1.5,textColor=color,alignment=TA_LEFT))
    _,height=p.wrap(width,H);p.drawOn(c,x,y-height);return y-height
def label(value,x,y): return text(value,x,y,size=8,bold=True,color=MUTED)
def line(y):c.setStrokeColor(LINE);c.line(48,y,W-48,y)
def page(number,kicker,title,subtitle):
    c.setFillColor(PAPER);c.rect(0,0,W,H,fill=1,stroke=0)
    label('TIANYU QI / APPLIED AI STUDIO',48,809);text('PROJECT BRIEF / OCT 2026',363,809,width=184,size=8,color=MUTED)
    line(783);label(kicker,48,762);text(title,48,738,size=30,leading=35,bold=True);text(subtitle,48,686,size=11,color=MUTED)
    line(52);text('zhitucv.online  |  AI-assisted development',48,40,size=8,color=MUTED);text(f'{number:02d} / 04',496,40,width=51,size=8,color=MUTED)
    c.linkURL(BASE,(48,25,270,43),relative=0)
def image(name,y,height=300):
    src=ROOT/'frontend/public/portfolio'/name
    c.drawImage(ImageReader(str(src)),48,y-height,width=499,height=height,preserveAspectRatio=True,anchor='c',mask='auto')
def section(title,body,y):
    y=text(title,48,y,size=11,bold=True);return text(body,48,y-6,size=9.5,leading=13.5,color=MUTED)-16
def link(label_,url,x,y,width=499):
    bottom=text(label_,x,y,width=width,size=10,bold=True,color=HexColor('#3a684b'));c.linkURL(url,(x,bottom-2,x+width,y),relative=0);return bottom

page(1,'PERSONAL PORTFOLIO','Applied AI, in practice.','Three connected application experiences, developed through product-led, AI-assisted iteration.')
y=text('Tianyu Qi',48,638,size=18,bold=True)
y=text('Digital Media Technology undergraduate, Fujian Normal University<br/>Expected graduation: June 2027',48,y-8,size=10,color=MUTED)
y=text('Trying new AI tools and building practical projects has motivated me to pursue systematic postgraduate study in AI or computing, with the aim of moving into AI-related work in a technology or internet company.',48,y-16,size=11,color=MUTED)
y-=24
for number,title,body in [('01','Career Agent','A bounded tool-calling workflow: role analysis, a tailored CV and interview preparation.'),('02','AI Persona','Natural conversation grounded in my curated public experience, with explicit factual boundaries.'),('03','Zhitu CV','The underlying toolkit: CV parsing, review, job matching and formatted PDF / Word export.')]:
    c.setFillColor(SAGE);c.roundRect(48,y-65,499,65,8,fill=1,stroke=0);label(number,62,y-13);text(title,92,y-10,width=438,size=12,bold=True);text(body,92,y-30,width=435,size=9,color=MUTED);y-=77
y=section('My contribution','I defined requirements and product priorities, tested the application in practice, identified ineffective outputs and usability issues, and drove successive revisions and public delivery. AI coding tools performed much of the implementation; this portfolio does not claim unaided authorship of every component.',y-2)
link('Explore the live portfolio and recorded example',BASE+'/demo',48,109)
link('View the source repository','https://github.com/tianyuq94-pixel/zhitu-resume',48,87)
c.showPage()

page(2,'01 / TOOL-CALLING WORKFLOW','Career Agent','How can an AI application carry a goal through reliable, reviewable steps?')
image('agent.png',648,293);text('Actual interface with a fictional CV and employer; not a real hiring assessment.',48,349,size=8,color=MUTED)
y=section('Mechanism','Confirmed CV + role -> allowed tool selection -> validated execution -> saved result -> next step or user question. The server enforces dependencies, validates outputs and checks task revisions to limit duplicate execution.',320)
y=section('Decisions I drove','I requested a results-first layout, meaningful-change filtering for CV edits, a reusable library of genuine experience and interview preparation before optional simulation. These choices came from hands-on trials, including suggestions that merely repeated the original text.',y)
y=section('Verification and boundary','Workflow tests cover invalid tools, ordering, revisions and recovery. The live recorded example uses a real model API with fictional input. This is a bounded workflow: no job-site crawling, application submission or background continuation after closing the browser.',y)
link('Read the case study and inspect the implementation',BASE+'/projects/career-agent',48,84)
c.showPage()

page(3,'02 / GROUNDED CONVERSATION','AI Persona','A familiar chat interface to the person and decisions behind the applications.')
image('persona.png',648,293);text('Actual model-generated conversation. The interface identifies the speaker as an AI persona.',48,349,size=8,color=MUTED)
y=section('Mechanism','The model receives approved public facts and recent dialogue, then returns a structured answer with fact identifiers. Unknown identifiers trigger a fallback. Visitors cannot create new biographical facts through their chat messages.',320)
y=section('My contribution','I proposed a conversational persona, chose the chat-app-like interaction, requested real model-generated responses rather than mechanical information cards, and approved the scope of public information. The current topics include project contributions, technical mechanisms, limitations and study motivation.',y)
y=section('Verification and boundary','Tests cover response structure, invalid identifiers, private visitor data isolation and contact requests. The system uses curated context, not fine-tuning or vector retrieval. Valid fact IDs are not proof of sentence-level factual correctness; the persona cannot make commitments on my behalf.',y)
link('Open the Persona case study',BASE+'/projects/ai-persona',48,84)
c.showPage()

page(4,'03 / DOCUMENT WORKFLOW','Zhitu CV','Turning AI advice into an editable, usable document while preserving real experience.')
image('toolkit.png',648,293);text('Actual CV toolkit. All applicant details in this screenshot are synthetic.',48,349,size=8,color=MUTED)
y=section('Mechanism and contribution','PDF / DOCX extraction -> user confirmation -> analysis or tailoring -> review -> export. I set the core features, supplied a layout reference, requested source-versus-suggestion review and added editable Word export to the requirements.',320)
y=section('Evidence, not inflated metrics','94 backend tests passed on 7 October 2026, mostly using controlled model responses. The recorded example includes actual PDF / Word exports. It identified missing PostgreSQL evidence and retained original wording when no rewrite passed the meaningful-change filter. These checks are not a model accuracy score or a study of hiring outcomes.',y)
y=section('Limitations and next evaluation','No scanned-document OCR. Match scores are heuristic, not hiring probabilities. A future step is a documented CV / role test set compared with a simpler baseline, assessing supported claims, useful edits and failure recovery. This comparison has not yet been completed.',y)
link('Read the case study',BASE+'/projects/zhitu-cv',48,84,width=235)
link('Contact: dvwaefu7708@163.com','mailto:dvwaefu7708@163.com',296,84,width=251)
c.showPage();c.save()
copyfile(OUT,ROOT/'frontend/public/portfolio/tianyu-qi-project-brief.pdf')
print(f'Created 4-page project brief: {OUT}')
