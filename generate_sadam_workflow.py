from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os, zipfile, shutil, subprocess, tempfile, time

# Animated GitHub profile banner: designed to look like a premium systems console.
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, 'assets')
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, 'sadam-workflow.gif')
PREVIEW = os.path.join(ROOT, 'banner-preview.png')
CONTACT = os.path.join(ROOT, 'animation-contact-sheet.jpg')
W, H = 1200, 430
STAGE_FRAMES = 46
WIPE_FRAMES = 10
FRAME_MS = 100

# Palette — restrained graphite with electric cyan, indigo, mint, and amber signals.
BG = (7, 11, 18)
GRID = (14, 21, 31)
PANEL = (12, 18, 28)
CARD = (15, 23, 35)
CARD2 = (18, 29, 43)
BORDER = (43, 59, 79)
BORDER_HI = (65, 91, 120)
TEXT = (230, 238, 249)
MUTED = (126, 146, 169)
FAINT = (73, 92, 117)
CYAN = (64, 222, 235)
BLUE = (85, 151, 255)
VIOLET = (165, 125, 255)
MINT = (89, 224, 174)
AMBER = (255, 190, 100)
RED = (255, 120, 135)

if os.name == 'nt':
    FONT_SANS = r'C:\Windows\Fonts\segoeui.ttf'
    FONT_BOLD = r'C:\Windows\Fonts\segoeuib.ttf'
    FONT_MONO = r'C:\Windows\Fonts\consola.ttf'
    FONT_MONO_BOLD = r'C:\Windows\Fonts\consolab.ttf'
else:
    FONT_SANS = '/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf'
    FONT_BOLD = '/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf'
    FONT_MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
    FONT_MONO_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'

def font(path, size):
    try: return ImageFont.truetype(path, size)
    except OSError: return ImageFont.load_default()

F_HERO = font(FONT_BOLD, 23)
F_TITLE = font(FONT_BOLD, 18)
F_SUB = font(FONT_SANS, 13)
F_BODY = font(FONT_SANS, 12)
F_LABEL = font(FONT_MONO_BOLD, 11)
F_MONO = font(FONT_MONO, 10)
F_SMALL = font(FONT_MONO, 9)
F_MICRO = font(FONT_MONO, 8)
F_BIG = font(FONT_MONO_BOLD, 15)


def clamp(v, lo=0.0, hi=1.0): return max(lo, min(hi, v))
def ease(v):
    v = clamp(v)
    return v*v*(3-2*v)
def mix(a,b,t):
    t=clamp(t)
    return tuple(int(a[i]*(1-t)+b[i]*t) for i in range(3))
def rgba(c, a=255): return (*c, int(clamp(a/255, 0, 1)*255))

def rounded(draw, box, radius=8, fill=CARD, outline=None, width=1):
    draw.rounded_rectangle(tuple(int(v) for v in box), radius=radius, fill=fill, outline=outline, width=width)
def text(draw, xy, s, f=F_BODY, fill=TEXT, anchor=None):
    draw.text(xy, s, font=f, fill=fill, anchor=anchor)
def centered(draw, xy, s, f=F_BODY, fill=TEXT): text(draw, xy, s, f, fill, 'mm')
def line(draw, pts, fill=BORDER, width=1): draw.line([(int(x),int(y)) for x,y in pts], fill=fill, width=width)
def dot(draw, x, y, r, fill, outline=None):
    draw.ellipse((int(x-r), int(y-r), int(x+r), int(y+r)), fill=fill, outline=outline)
def pill(draw, x, y, label, color=CYAN, fill=(17,31,44), width=None):
    if width is None:
        width = int(draw.textlength(label, font=F_SMALL)) + 18
    rounded(draw,(x,y,x+width,y+20),6,fill,mix(BORDER,color,.55),1)
    dot(draw,x+9,y+10,2,color)
    text(draw,(x+16,y+5),label,F_SMALL,color)
    return width

def glow_dot(glow, x, y, color, r=3, alpha=220):
    g=ImageDraw.Draw(glow,'RGBA')
    g.ellipse((x-r*2.6,y-r*2.6,x+r*2.6,y+r*2.6),fill=(*color,int(alpha*.20)))
    g.ellipse((x-r,y-r,x+r,y+r),fill=(*color,alpha))

def arrow(draw, x1,y1,x2,y2,color=CYAN,width=2,head=5):
    line(draw,[(x1,y1),(x2,y2)],color,width)
    ang=math.atan2(y2-y1,x2-x1)
    p1=(x2-head*math.cos(ang-.55),y2-head*math.sin(ang-.55))
    p2=(x2-head*math.cos(ang+.55),y2-head*math.sin(ang+.55))
    draw.polygon([(x2,y2),p1,p2],fill=color)

def flow_dot(glow, a, b, p, color=CYAN, r=3):
    x=a[0]+(b[0]-a[0])*p; y=a[1]+(b[1]-a[1])*p
    glow_dot(glow,x,y,color,r,235)
    if p>.07:
        for lag in (.08,.16):
            q=p-lag
            if q>=0: glow_dot(glow,a[0]+(b[0]-a[0])*q,a[1]+(b[1]-a[1])*q,color,max(1,r-1),95)

def node(draw, glow, box, title, subtitle='', color=CYAN, visible=1.0, icon=None, status=None, radius=8):
    x1,y1,x2,y2=box
    vis=clamp(visible)
    if vis <= 0.01: return
    xoff=int((1-ease(vis))*9)
    box=(x1+xoff,y1,x2+xoff,y2)
    edge=mix(BORDER,color,.15+.70*vis)
    bg=mix(PANEL,CARD2,.5*vis)
    rounded(draw,box,radius,bg,edge,1 if vis<.7 else 2)
    if icon:
        rounded(draw,(box[0]+9,box[1]+9,box[0]+28,box[1]+28),5,(22,34,50),mix(BORDER,color,.65),1)
        centered(draw,(box[0]+18.5,box[1]+18.5),icon,F_LABEL,color)
        tx=box[0]+36
    else: tx=box[0]+10
    text(draw,(tx,box[1]+10),title,F_LABEL,mix(MUTED,TEXT,vis))
    if subtitle: text(draw,(tx,box[1]+27),subtitle,F_SMALL,mix(FAINT,MUTED,vis))
    if status:
        dot(draw,box[2]-11,box[1]+12,2.5,color if vis>.7 else FAINT)
        if vis>.7: glow_dot(glow,box[2]-11,box[1]+12,color,2,70)

def chart_line(draw, glow, box, values, color=CYAN, progress=1.0, t=0.0):
    x1,y1,x2,y2=box
    line(draw,[(x1,y2),(x2,y2)],(32,47,65),1)
    for k in range(1,4):
        yy=y1+(y2-y1)*k/4
        line(draw,[(x1,yy),(x2,yy)],(25,39,55),1)
    maxn=max(values); minn=min(values); span=max(1,maxn-minn)
    pts=[]; n=max(2,int(len(values)*clamp(progress)))
    for i,v in enumerate(values[:n]):
        x=x1+(x2-x1)*i/(len(values)-1)
        y=y2-4-(v-minn)/span*(y2-y1-8)
        pts.append((x,y))
    if len(pts)>1: line(draw,pts,color,2)
    if pts:
        xx,yy=pts[-1]
        glow_dot(glow,xx,yy,color,3,180)

def icon_server(draw,x,y,color=CYAN):
    rounded(draw,(x,y,x+25,y+28),4,(13,22,34),mix(BORDER,color,.55),1)
    for yy in (y+7,y+14,y+21):
        line(draw,[(x+5,yy),(x+16,yy)],(69,90,115),1)
        dot(draw,x+20,yy,1.7,color)

def icon_mail(draw,x,y,color=AMBER):
    rounded(draw,(x,y,x+28,y+20),4,(14,23,35),mix(BORDER,color,.65),1)
    line(draw,[(x+2,y+3),(x+14,y+11),(x+26,y+3)],color,1)

def icon_db(draw,x,y,color=CYAN):
    draw.ellipse((x,y,x+30,y+10),fill=(17,37,51),outline=color,width=1)
    draw.rectangle((x,y+5,x+30,y+25),fill=(15,28,41),outline=color,width=1)
    draw.arc((x,y+17,x+30,y+30),0,180,fill=color,width=1)
    draw.ellipse((x,y+20,x+30,y+30),outline=color,width=1)

def icon_bot(draw,x,y,color=VIOLET):
    rounded(draw,(x,y,x+28,y+26),7,(19,25,40),mix(BORDER,color,.75),1)
    line(draw,[(x+14,y-4),(x+14,y)],color,1)
    dot(draw,x+14,y-5,2,color)
    dot(draw,x+8,y+11,2,color); dot(draw,x+20,y+11,2,color)
    line(draw,[(x+8,y+19),(x+20,y+19)],color,1)

def scene_automation(d, g, p, t):
    # Event-driven workflow with node-by-node execution.
    text(d,(340,127),'EVENT-DRIVEN PIPELINE',F_SMALL,MUTED)
    pill(d,936,120,'WEBHOOK  •  EVENT RECEIVED',CYAN,width=204)
    xs=[354,513,672,831,990]; y=191; w=128; h=70
    labels=[('TRIGGER','form.submit','↯',CYAN),('VALIDATE','schema + rules','✓',BLUE),('ENRICH','company data','✦',VIOLET),('ROUTE','fit score > 70','⇢',AMBER),('DELIVER','CRM + alert','✓',MINT)]
    for i in range(4):
        a=(xs[i]+w,y+35); b=(xs[i+1],y+35)
        line(d,[a,b],(38,58,80),2)
        for k in range(1,4): dot(d,a[0]+(b[0]-a[0])*k/4,a[1],1.5,(56,82,111))
        flow_dot(g,a,b,(p*2.5-i*.22)%1,[CYAN,BLUE,VIOLET,AMBER][i],3)
    for i,(title,sub,ic,col) in enumerate(labels):
        v=clamp((p-i*.12)*5)
        node(d,g,(xs[i],y,xs[i]+w,y+h),title,sub,col,v,ic,'ok')
        if v>.75:
            rounded(d,(xs[i]+10,y+52,xs[i]+w-10,y+60),3,(24,40,53),None,0)
            rounded(d,(xs[i]+10,y+52,xs[i]+10+(w-20)*(.35+.65*((t*1.4+i*.17)%1)),y+60),3,col,None,0)
    # execution trace/log row
    rounded(d,(350,286,1138,333),7,(10,16,25),(37,52,72),1)
    text(d,(364,296),'EXECUTION TRACE',F_SMALL,MUTED)
    logs=['event accepted','payload validated','company enriched','buy-box evaluated','CRM record upserted']
    for i,msg in enumerate(logs):
        x=364+i*153
        col=[CYAN,BLUE,VIOLET,AMBER,MINT][i]
        dot(d,x+4,319,2.5,col if p>i*.13 else FAINT)
        text(d,(x+12,314),msg,F_SMALL,TEXT if p>i*.13 else FAINT)


def scene_admin(d, g, p, t):
    text(d,(340,127),'FLEET HEALTH  /  SELF-HOSTED INFRASTRUCTURE',F_SMALL,MUTED)
    pill(d,961,120,'SSH • DOCKER • LINUX',MINT,width=180)
    # host inventory
    rounded(d,(344,148,744,333),9,CARD,BORDER,1)
    text(d,(359,159),'HOST INVENTORY',F_LABEL,TEXT)
    text(d,(643,160),'3 / 3 ONLINE',F_SMALL,MINT)
    hosts=[('edge-vps-01','API + reverse proxy',36,48,CYAN),('worker-02','queues + automations',62,71,VIOLET),('data-node-01','Postgres + backups',27,58,MINT)]
    for i,(name,desc,cpu,mem,col) in enumerate(hosts):
        yy=184+i*47; vis=clamp((p-i*.10)*5)
        if vis>0:
            rounded(d,(356,yy,730,yy+40),6,(13,21,32),mix(BORDER,col,.35*vis),1)
            icon_server(d,365,yy+6,col)
            text(d,(399,yy+6),name,F_LABEL,TEXT)
            text(d,(399,yy+22),desc,F_SMALL,MUTED)
            text(d,(576,yy+5),'CPU',F_MICRO,FAINT); text(d,(624,yy+5),f'{max(1,int(cpu+math.sin(t*2+i)*4))}%',F_SMALL,col)
            rounded(d,(575,yy+18,622,yy+23),2,(29,41,55),None,0); rounded(d,(575,yy+18,575+47*cpu/100,yy+23),2,col,None,0)
            text(d,(638,yy+20),f'{mem}%',F_SMALL,MUTED)
    # terminal + uptime chart
    rounded(d,(759,148,1144,333),9,(9,15,24),BORDER,1)
    text(d,(775,159),'LIVE TELEMETRY',F_LABEL,TEXT)
    pill(d,1034,153,'HEALTHY',MINT,width=91)
    vals=[42,45,44,53,48,62,57,64,60,72,65,76,69,81,73,88,80]
    chart_line(d,g,(778,187,1125,242),vals,MINT,p,t)
    text(d,(778,252),'LOAD AVG',F_MICRO,FAINT); text(d,(778,266),f'{0.42+0.06*math.sin(t*2):.2f}',F_BIG,TEXT)
    text(d,(906,252),'UPTIME',F_MICRO,FAINT); text(d,(906,266),'99.98%',F_BIG,MINT)
    text(d,(1034,252),'DISK',F_MICRO,FAINT); text(d,(1034,266),f'{61+int(2*math.sin(t)):02d}%',F_BIG,CYAN)
    line(d,[(776,292),(1127,292)],(34,49,67),1)
    status=['docker compose ps','nginx: config test passed','backup snapshot verified']
    for i,s in enumerate(status):
        yy=299+i*10
        text(d,(778,yy),['$','+','+'][i],F_SMALL,CYAN if i==0 else MINT)
        text(d,(792,yy),s,F_SMALL,MUTED if p<(i*.22) else TEXT)


def scene_ai(d, g, p, t):
    text(d,(340,127),'AGENT RUNTIME  /  PLAN → TOOL CALLS → RESULT',F_SMALL,MUTED)
    pill(d,1000,120,'CONTEXT GROUNDED',VIOLET,width=142)
    # input -> planner
    node(d,g,(348,205,466,276),'TASK INPUT','classify + resolve',CYAN,clamp(p*5),'↳')
    node(d,g,(516,180,687,294),'AGENT PLANNER','plan / observe / act',VIOLET,clamp((p-.08)*5),'AI','RUNNING')
    line(d,[(466,240),(516,240)],(54,76,102),2); flow_dot(g,(466,240),(516,240),(p*3)%1,CYAN,3)
    # three tool cards
    tools=[(744,148,'WEB SEARCH','source lookup','⌕',CYAN),(744,210,'SQL QUERY','read records','db',MINT),(744,272,'DOCS RAG','retrieve context','R',AMBER)]
    for i,(x,y,title,sub,ic,col) in enumerate(tools):
        line(d,[(687,235),(712,235),(712,y+20),(x,y+20)],(47,65,88),1)
        v=clamp((p-.18-i*.10)*6)
        node(d,g,(x,y,x+142,y+43),title,sub,col,v,ic)
        if v>.5: flow_dot(g,(687,235),(x,y+20),(p*2+i*.25)%1,col,2)
    node(d,g,(940,208,1138,278),'FINAL RESPONSE','structured + traceable',MINT,clamp((p-.47)*4),'✓','READY')
    line(d,[(886,169),(910,169),(910,231),(940,231)],(47,65,88),1)
    line(d,[(886,231),(940,231)],(47,65,88),1)
    line(d,[(886,293),(910,293),(910,255),(940,255)],(47,65,88),1)
    flow_dot(g,(886,231),(940,231),(p*2.3)%1,MINT,3)
    # tool-call timeline
    rounded(d,(350,316,1139,337),5,(10,16,25),(36,51,70),1)
    text(d,(362,322),'TRACE',F_MICRO,MUTED)
    trace=['intent parsed','plan created','tools called','context merged','answer validated']
    for i,s in enumerate(trace):
        x=419+i*139; col=[CYAN,VIOLET,AMBER,BLUE,MINT][i]
        dot(d,x,326,2,col if p>i*.16 else FAINT)
        text(d,(x+7,322),s,F_SMALL,TEXT if p>i*.16 else FAINT)


def scene_database(d, g, p, t):
    text(d,(340,127),'DATA PIPELINE  /  INGEST · TRANSFORM · STORE',F_SMALL,MUTED)
    pill(d,1008,120,'TRANSACTIONAL',CYAN,width=134)
    # source cards
    sources=[('EVENTS','stream','E',CYAN),('REST API','JSON','{}',BLUE),('FILES','CSV / PDF','F',AMBER)]
    for i,(title,sub,ic,col) in enumerate(sources):
        y=154+i*55; v=clamp((p-i*.08)*5)
        node(d,g,(350,y,476,y+43),title,sub,col,v,ic)
    # ingestion / transform stages
    node(d,g,(529,177,665,231),'NORMALIZE','map fields',VIOLET,clamp((p-.12)*5),'01')
    node(d,g,(529,245,665,299),'VALIDATE','types + rules',AMBER,clamp((p-.22)*5),'02')
    for sy in (175,230,285):
        line(d,[(476,sy),(500,sy),(500,204),(529,204)],(47,66,90),1)
    flow_dot(g,(476,204),(529,204),(p*2.4)%1,CYAN,3)
    # data table view
    rounded(d,(700,148,1142,333),9,CARD,BORDER,1)
    text(d,(715,159),'POSTGRESQL  /  DEALS',F_LABEL,TEXT)
    pill(d,1020,153,'CONNECTED',MINT,width=105)
    cols=[('ID',45),('COMPANY',140),('FIT',58),('STATUS',108)]
    x=715; yy=187
    for label,w in cols:
        text(d,(x,yy),label,F_MICRO,MUTED); x+=w
    line(d,[(714,201),(1127,201)],(39,55,75),1)
    rows=[('DL-0182','Northstar Labs','92','QUALIFIED'),('DL-0183','Meridian Cloud','84','REVIEW'),('DL-0184','Pinecone Data','77','QUALIFIED'),('DL-0185','Atlas Systems','63','HOLD'),('DL-0186','Lumen Works','88','QUALIFIED')]
    scan_y=204+(p*5%1)*111
    for i,row in enumerate(rows):
        y=207+i*22
        if abs(y-scan_y)<16:
            rounded(d,(711,y-2,1131,y+17),3,(20,42,55),None,0)
            line(d,[(712,y+16),(1130,y+16)],CYAN,1)
        x=717
        for j,val in enumerate(row):
            col=CYAN if j==0 else (MINT if (j==2 and int(val)>=80) or (j==3 and val=='QUALIFIED') else TEXT if j==1 else AMBER)
            text(d,(x,y+3),val,F_SMALL,col); x+=cols[j][1]
    text(d,(717,321),'2.4K rows  •  batch 042  •  constraints verified',F_MICRO,MUTED)


def scene_api(d, g, p, t):
    text(d,(340,127),'SERVICE INTEGRATION  /  REST + WEBHOOKS',F_SMALL,MUTED)
    pill(d,1004,120,'TLS • AUTH • JSON',BLUE,width=138)
    xs=[349,513,678,843,1008]; w=123; y=191; h=82
    labels=[('CLIENT','POST /leads','↗',CYAN),('GATEWAY','rate limit','⇥',BLUE),('AUTH','JWT verified','✓',VIOLET),('REST API','/v1/deals','{}',AMBER),('SERVICE','201 created','✓',MINT)]
    for i in range(4):
        a=(xs[i]+w,y+40); b=(xs[i+1],y+40)
        line(d,[a,b],(40,59,82),2)
        flow_dot(g,a,b,(p*2.7-i*.16)%1,[CYAN,BLUE,VIOLET,AMBER][i],3)
    for i,(title,sub,ic,col) in enumerate(labels):
        node(d,g,(xs[i],y,xs[i]+w,y+h),title,sub,col,clamp((p-i*.11)*5),ic,'ok')
    # protocol strips
    rounded(d,(350,291,1138,333),6,(10,16,25),(36,50,69),1)
    text(d,(364,299),'REQUEST',F_MICRO,MUTED); text(d,(431,298),'POST',F_LABEL,CYAN); text(d,(478,298),'/api/v1/deals',F_LABEL,TEXT)
    text(d,(690,299),'RESPONSE',F_MICRO,MUTED); pill(d,778,294,'201 CREATED',MINT,width=112)
    text(d,(915,299),'LATENCY',F_MICRO,MUTED); text(d,(981,298),f'{118+int(9*math.sin(t*3))}ms',F_LABEL,CYAN)
    # little packet bytes
    for i in range(16):
        col=CYAN if (i < int(p*16)) else (29,47,64)
        rounded(d,(1030+i*6,319,1034+i*6,324),1,col,None,0)


def scene_email(d, g, p, t):
    text(d,(340,127),'EMAIL AUTOMATION  /  CLASSIFY · PERSONALIZE · FOLLOW UP',F_SMALL,MUTED)
    pill(d,1003,120,'SEQUENCE ACTIVE',AMBER,width=139)
    # inbox stack
    rounded(d,(349,151,515,329),9,CARD,BORDER,1)
    icon_mail(d,363,163,AMBER)
    text(d,(400,166),'INBOX QUEUE',F_LABEL,TEXT)
    text(d,(365,200),'new inbound',F_SMALL,MUTED)
    mails=[('Website lead','pricing request',CYAN),('Partner intro','warm referral',VIOLET),('Invoice reply','billing query',AMBER)]
    for i,(a,b,col) in enumerate(mails):
        yy=218+i*34; v=clamp((p-i*.11)*5)
        if v>0:
            rounded(d,(360,yy,504,yy+28),5,(14,23,35),mix(BORDER,col,.42),1)
            dot(d,369,yy+10,2.5,col)
            text(d,(378,yy+4),a,F_SMALL,TEXT)
            text(d,(378,yy+16),b,F_MICRO,MUTED)
    # automation path
    node(d,g,(550,178,686,229),'CLASSIFY','intent + priority',VIOLET,clamp((p-.08)*5),'AI')
    node(d,g,(550,251,686,302),'PERSONALIZE','CRM context',CYAN,clamp((p-.21)*5),'✎')
    line(d,[(515,239),(534,239),(534,203),(550,203)],(46,64,86),1)
    line(d,[(618,229),(618,251)],(46,64,86),1)
    flow_dot(g,(515,239),(550,203),(p*2.4)%1,AMBER,3)
    # branches to send and schedule
    node(d,g,(732,170,867,222),'SEND NOW','approved template',MINT,clamp((p-.34)*5),'↗')
    node(d,g,(732,253,867,305),'FOLLOW-UP','+ 48 hours',AMBER,clamp((p-.44)*5),'◷')
    line(d,[(686,203),(710,203),(710,196),(732,196)],(47,64,85),1)
    line(d,[(686,277),(710,277),(710,279),(732,279)],(47,64,85),1)
    flow_dot(g,(686,203),(732,196),(p*2.1)%1,MINT,2)
    # delivery results
    rounded(d,(896,151,1141,329),9,(10,16,25),BORDER,1)
    text(d,(911,164),'DELIVERY METRICS',F_LABEL,TEXT)
    metrics=[('DELIVERED',f'{int(92+3*math.sin(t*1.6))}.4%',MINT),('OPEN RATE',f'{int(47+4*math.sin(t*1.3))}.8%',CYAN),('REPLIES',str(24+int(2*math.sin(t*2))),VIOLET)]
    for i,(lab,val,col) in enumerate(metrics):
        yy=199+i*39
        text(d,(912,yy),lab,F_MICRO,MUTED); text(d,(912,yy+12),val,F_BIG,col)
        rounded(d,(1010,yy+14,1124,yy+20),3,(28,41,55),None,0)
        rounded(d,(1010,yy+14,1010+114*(.3+.6*((p+i*.17)%1)),yy+20),3,col,None,0)


def scene_n8n(d, g, p, t):
    text(d,(340,127),'VISUAL ORCHESTRATION  /  HIGH-LEVEL WORKFLOWS',F_SMALL,MUTED)
    pill(d,1019,120,'N8N-STYLE FLOW',VIOLET,width=123)
    # canvas
    rounded(d,(344,148,879,333),9,(10,16,25),BORDER,1)
    # node graph positions and connections
    pts={'trigger':(374,220),'if':(492,220),'enrich':(611,177),'crm':(730,177),'mail':(611,270),'slack':(730,270)}
    edges=[('trigger','if'),('if','enrich'),('enrich','crm'),('if','mail'),('mail','slack')]
    for i,(a,b) in enumerate(edges):
        a0=pts[a]; b0=pts[b]
        # Orthogonal routed connectors join wider text-first cards.
        midx=(a0[0]+b0[0])//2
        line(d,[ (a0[0]+45,a0[1]),(midx,a0[1]),(midx,b0[1]),(b0[0]-45,b0[1]) ],(43,62,84),2)
        flow_dot(g,(a0[0]+45,a0[1]),(b0[0]-45,b0[1]),(p*2.1-i*.16)%1,[CYAN,VIOLET,MINT,AMBER,BLUE][i],3)
    specs=[('trigger','WEBHOOK','new lead',CYAN),('if','IF / ROUTE','score > 70',VIOLET),('enrich','ENRICH','company data',AMBER),('crm','CRM UPSERT','record saved',MINT),('mail','SEND EMAIL','notify owner',BLUE),('slack','SLACK ALERT','sales channel',VIOLET)]
    for i,(key,title,sub,col) in enumerate(specs):
        x,y=pts[key]
        node(d,g,(x-45,y-29,x+45,y+29),title,sub,col,clamp((p-i*.07)*6),None,radius=7)
    # execution inspector
    rounded(d,(895,148,1142,333),9,CARD,BORDER,1)
    text(d,(910,160),'EXECUTION INSPECTOR',F_LABEL,TEXT)
    text(d,(910,182),'workflow / inbound-lead-v4',F_SMALL,MUTED)
    line(d,[(910,198),(1127,198)],(35,51,71),1)
    logs=[('01','Webhook received',CYAN),('02','Condition true',VIOLET),('03','CRM updated',MINT),('04','Email delivered',AMBER),('05','Run completed',MINT)]
    for i,(num,msg,col) in enumerate(logs):
        yy=208+i*22; vis=p>i*.13
        dot(d,918,yy+5,3,col if vis else FAINT)
        text(d,(928,yy),num,F_MICRO,FAINT)
        text(d,(951,yy),msg,F_SMALL,TEXT if vis else FAINT)
        if vis: text(d,(1110,yy),'OK',F_MICRO,col)


def scene_tracking(d, g, p, t):
    text(d,(340,127),'OBSERVABILITY  /  EVENTS · METRICS · TRACES',F_SMALL,MUTED)
    pill(d,1017,120,'TELEMETRY LIVE',MINT,width=125)
    # KPI cards
    kpis=[(350,'UPTIME','99.98%',MINT),(516,'EVENTS / MIN',f'{2.4+0.1*math.sin(t):.1f}K',CYAN),(682,'P95 LATENCY',f'{138+int(8*math.sin(t*1.8))}ms',VIOLET)]
    for i,(x,lab,val,col) in enumerate(kpis):
        rounded(d,(x,151,x+151,207),7,CARD,mix(BORDER,col,.38),1)
        text(d,(x+12,160),lab,F_MICRO,MUTED)
        text(d,(x+12,177),val,F_BIG,col)
        # pulse sparkline
        vals=[5,8,7,11,9,14,12,16,14,18,15,20]
        px=x+92; py=176
        pts=[]
        for j,v in enumerate(vals): pts.append((px+j*4,py+20-v*(.40+.25*math.sin(t+j))))
        line(d,pts,mix(col,(20,35,49),.25),1)
    # trend chart
    rounded(d,(350,219,818,333),8,(10,16,25),BORDER,1)
    text(d,(365,231),'EVENT THROUGHPUT',F_LABEL,TEXT)
    text(d,(701,232),'LAST 60 MIN',F_MICRO,MUTED)
    vals=[40,42,38,48,45,52,49,60,55,63,58,68,65,74,69,81,76,87,79,91]
    chart_line(d,g,(366,252,800,318),vals,CYAN,p,t)
    # live event stream
    rounded(d,(833,219,1142,333),8,CARD,BORDER,1)
    text(d,(847,231),'EVENT STREAM',F_LABEL,TEXT)
    events=[('lead.created','200',CYAN),('email.sent','202',MINT),('deal.scored','200',VIOLET),('api.request','201',AMBER),('job.finished','200',MINT)]
    for i,(name,status,col) in enumerate(events):
        yy=252+i*15
        if p>i*.12:
            dot(d,849,yy+4,2,col)
            text(d,(858,yy),name,F_SMALL,TEXT)
            text(d,(1090,yy),status,F_SMALL,col)


def scene_chatbot(d, g, p, t):
    text(d,(340,127),'CONVERSATIONAL AI  /  KNOWLEDGE + HUMAN HANDOFF',F_SMALL,MUTED)
    pill(d,1000,120,'ASSISTANT ONLINE',VIOLET,width=142)
    # left customer chat
    rounded(d,(350,151,578,333),9,CARD,BORDER,1)
    text(d,(365,163),'CONVERSATION',F_LABEL,TEXT)
    # message bubbles appearing one by one
    v1=clamp(p*5)
    if v1>.15:
        rounded(d,(365,188,543,218),7,(20,32,47),(44,62,84),1)
        text(d,(375,197),'Can I get an invoice copy?',F_SMALL,TEXT)
    v2=clamp((p-.20)*5)
    if v2>.15:
        rounded(d,(386,230,562,267),7,(24,26,48),(87,71,126),1)
        text(d,(396,238),'Searching billing records…',F_SMALL,VIOLET)
        text(d,(396,251),'source: help-center / billing',F_MICRO,MUTED)
    v3=clamp((p-.48)*5)
    if v3>.15:
        rounded(d,(365,280,543,313),7,(15,39,36),(44,100,82),1)
        text(d,(375,288),'Found invoice #INV-2048.',F_SMALL,MINT)
        text(d,(375,300),'Ready to send securely.',F_MICRO,MUTED)
    # RAG and model route
    node(d,g,(610,178,744,230),'RETRIEVAL','search knowledge',CYAN,clamp((p-.07)*5),'R')
    node(d,g,(610,257,744,309),'LLM ROUTER','intent + response',VIOLET,clamp((p-.22)*5),'AI')
    line(d,[(578,202),(610,202)],(46,66,89),1); flow_dot(g,(578,202),(610,202),(p*2.4)%1,CYAN,2)
    line(d,[(677,230),(677,257)],(46,66,89),1); flow_dot(g,(677,230),(677,257),(p*2)%1,VIOLET,2)
    # handoff card
    rounded(d,(777,151,1142,333),9,(10,16,25),BORDER,1)
    text(d,(793,163),'RESPONSE ROUTING',F_LABEL,TEXT)
    node(d,g,(793,188,936,239),'AI RESOLVED','confidence 0.94',MINT,clamp((p-.36)*5),'✓')
    node(d,g,(793,260,936,311),'HUMAN HANDOFF','if confidence < 0.72',AMBER,clamp((p-.53)*5),'↗')
    line(d,[(744,202),(766,202),(766,213),(793,213)],(46,65,87),1)
    line(d,[(744,284),(766,284),(766,286),(793,286)],(46,65,87),1)
    # handoff status panel
    rounded(d,(958,188,1127,311),7,CARD2,(44,62,84),1)
    text(d,(972,202),'POLICY CHECK',F_MICRO,MUTED)
    for i,(label,col) in enumerate([('PII REDACTED',CYAN),('SOURCE CITED',VIOLET),('AUDIT LOGGED',MINT)]):
        yy=224+i*23; visible=p>(i*.15+.25)
        dot(d,974,yy+3,2.5,col if visible else FAINT)
        text(d,(983,yy),label,F_SMALL,TEXT if visible else FAINT)

def scene_backup(d, g, p, t):
    text(d,(340,127),'RESILIENCE ENGINE  /  BACKUP · VERIFY · RESTORE',F_SMALL,MUTED)
    pill(d,1018,120,'RECOVERY READY',MINT,width=124)
    # timeline and backup policy card
    rounded(d,(348,149,679,333),9,CARD,BORDER,1)
    text(d,(363,161),'BACKUP ORCHESTRATOR',F_LABEL,TEXT)
    text(d,(363,180),'policy: nightly + pre-release',F_SMALL,MUTED)
    steps=[('SCHEDULE','02:00 UTC',CYAN),('SNAPSHOT','db + volume',BLUE),('CHECKSUM','integrity pass',VIOLET),('RETENTION','30-day policy',AMBER),('RESTORE TEST','verified',MINT)]
    for i,(lab,sub,col) in enumerate(steps):
        yy=204+i*24; vis=clamp((p-i*.13)*6)
        dot(d,369,yy+4,4,col if vis>.5 else FAINT)
        if i<4: line(d,[(369,yy+9),(369,yy+24)],col if vis>.6 else (39,54,73),2)
        text(d,(382,yy-2),lab,F_LABEL,TEXT if vis>.5 else MUTED)
        text(d,(531,yy-1),sub,F_SMALL,col if vis>.5 else FAINT)
        if vis>.72: text(d,(643,yy-1),'PASS',F_MICRO,MINT)
    # vault / artifact inventory
    rounded(d,(694,149,1142,333),9,(10,16,25),BORDER,1)
    text(d,(710,161),'RECOVERY ARTIFACTS',F_LABEL,TEXT)
    pill(d,1027,154,'ENCRYPTED',VIOLET,width=99)
    files=[('postgres.dump','2.4 GB','SHA256 verified',CYAN),('app-config.tar','184 MB','secret-safe archive',BLUE),('uploads-2026.tar','6.1 GB','incremental snapshot',AMBER)]
    for i,(name,size,sub,col) in enumerate(files):
        yy=189+i*39; vis=clamp((p-i*.12)*5)
        rounded(d,(709,yy,1127,yy+31),5,(14,22,33),mix(BORDER,col,.40*vis),1)
        rounded(d,(718,yy+7,737,yy+24),4,(24,35,51),mix(BORDER,col,.7),1)
        centered(d,(727,yy+15),['DB','AR','BK'][i],F_MICRO,col)
        text(d,(746,yy+5),name,F_SMALL,TEXT if vis>.4 else MUTED)
        text(d,(746,yy+18),sub,F_MICRO,MUTED)
        text(d,(1005,yy+9),size,F_SMALL,col)
        rounded(d,(1082,yy+12,1116,yy+18),3,(32,46,61),None,0)
        if vis>.7: rounded(d,(1082,yy+12,1116,yy+18),3,col,None,0)
    text(d,(710,315),'RPO target  ≤ 24h   •   restore drill  /  monthly',F_MICRO,MUTED)


def scene_dev(d, g, p, t):
    text(d,(340,127),'ENGINEERING WORKBENCH  /  CODE · REVIEW · VERSION CONTROL',F_SMALL,MUTED)
    pill(d,1026,120,'GIT WORKFLOW',BLUE,width=116)
    rounded(d,(348,149,770,333),9,(9,15,24),BORDER,1)
    rounded(d,(348,149,770,175),7,(17,25,37),None,0)
    for i,col in enumerate((RED,AMBER,MINT)): dot(d,362+11*i,162,3,col)
    text(d,(405,157),'services/lead_router.py',F_SMALL,MUTED)
    code=[('01','def handle_lead(event):',VIOLET),('02','    payload = validate(event)',CYAN),('03','    match = deduplicate(payload)',AMBER),('04','    score = evaluate_buy_box(match)',MINT),('05','    repo.upsert(score)',BLUE),('06','    audit.record(event.id)',TEXT),('07','    return response(202)',CYAN)]
    for i,(num,src,col) in enumerate(code):
        yy=188+i*18; vis=clamp((p-i*.085)*6)
        text(d,(364,yy),num,F_MICRO,FAINT)
        if vis>.04:
            n=max(1,int(len(src)*vis)); text(d,(389,yy),src[:n],F_SMALL,col)
            if n<len(src) and vis<.98:
                xx=389+d.textlength(src[:n],font=F_SMALL); rounded(d,(xx,yy+2,xx+2,yy+12),1,CYAN,None,0)
    rounded(d,(789,149,1142,333),9,CARD,BORDER,1)
    text(d,(805,161),'CHANGE REVIEW',F_LABEL,TEXT)
    pill(d,1029,154,'BRANCH CLEAN',MINT,width=97)
    # visual branch graph
    line(d,[(822,201),(822,299)],(55,75,98),2)
    branch=[('feature/lead-score',CYAN),('unit tests',MINT),('review approved',VIOLET),('merge commit',AMBER)]
    for i,(lab,col) in enumerate(branch):
        yy=194+i*31; vis=clamp((p-i*.13)*6)
        dot(d,822,yy+5,4,col if vis>.55 else FAINT)
        text(d,(837,yy-1),lab,F_SMALL,TEXT if vis>.5 else MUTED)
        if vis>.72: text(d,(1090,yy-1),'PASS',F_MICRO,col)
    rounded(d,(805,321,1125,327),3,(28,42,57),None,0)
    rounded(d,(805,321,805+320*ease(p),327),3,BLUE,None,0)


def scene_cicd(d, g, p, t):
    text(d,(340,127),'RELEASE ENGINEERING  /  BUILD · TEST · SHIP · VERIFY',F_SMALL,MUTED)
    pill(d,1022,120,'DEPLOY PIPELINE',AMBER,width=120)
    # horizontal CI/CD stages
    xs=[350,507,664,821,978]; y=174; w=132; h=80
    specs=[('SOURCE','commit 8f21c9',BLUE,'G'),('QUALITY','lint + 42 tests',MINT,'✓'),('PACKAGE','Docker image',VIOLET,'D'),('RELEASE','rolling deploy',AMBER,'↗'),('VERIFY','health checks',CYAN,'OK')]
    for i in range(4):
        a=(xs[i]+w,y+40); b=(xs[i+1],y+40)
        line(d,[a,b],(43,61,81),2)
        flow_dot(g,a,b,(p*2.5-i*.19)%1,[BLUE,MINT,VIOLET,AMBER][i],3)
    for i,(lab,sub,col,ic) in enumerate(specs):
        vis=clamp((p-i*.11)*5.5)
        node(d,g,(xs[i],y,xs[i]+w,y+h),lab,sub,col,vis,ic,'ok')
        if vis>.6:
            rounded(d,(xs[i]+10,y+61,xs[i]+w-10,y+67),3,(27,42,57),None,0)
            rounded(d,(xs[i]+10,y+61,xs[i]+10+(w-20)*clamp((p-i*.13)*3),y+67),3,col,None,0)
    # rollout and health gates
    rounded(d,(350,276,1140,333),8,(10,16,25),BORDER,1)
    text(d,(365,288),'RELEASE GATES',F_LABEL,TEXT)
    gates=[('unit tests',MINT),('image scan',CYAN),('config check',VIOLET),('smoke test',AMBER),('rollback ready',BLUE)]
    for i,(lab,col) in enumerate(gates):
        x=500+i*126; vis=p>i*.14
        dot(d,x,298,3.5,col if vis else FAINT)
        text(d,(x+9,292),lab,F_SMALL,TEXT if vis else FAINT)
        text(d,(x+9,308),'PASS' if vis else 'WAIT',F_MICRO,col if vis else FAINT)


def scene_queue(d, g, p, t):
    text(d,(340,127),'EVENT RELIABILITY  /  QUEUES · WORKERS · RETRIES',F_SMALL,MUTED)
    pill(d,1003,120,'DELIVERY GUARDED',AMBER,width=139)
    # queue/broker at left
    node(d,g,(350,205,475,267),'JOB QUEUE','broker / events',CYAN,clamp(p*5),'Q')
    # worker cards
    workers=[(543,155,'WORKER 01','success',MINT),(543,216,'WORKER 02','retrying',AMBER),(543,277,'WORKER 03','success',MINT)]
    for i,(x,y,lab,sub,col) in enumerate(workers):
        line(d,[(475,236),(506,236),(506,y+20),(x,y+20)],(45,64,85),1)
        vis=clamp((p-.09-i*.10)*5)
        node(d,g,(x,y,x+142,y+42),lab,sub,col,vis,['✓','↻','✓'][i])
        if vis>.5: flow_dot(g,(475,236),(x,y+20),(p*2.2+i*.17)%1,col,2)
    # retry/dead-letter path
    rounded(d,(710,149,1141,333),9,CARD,BORDER,1)
    text(d,(726,161),'FAILURE POLICY',F_LABEL,TEXT)
    # branch path and three nodes
    node(d,g,(727,193,856,240),'RETRY','backoff 2s → 8s',AMBER,clamp((p-.24)*5),'↻')
    node(d,g,(727,267,856,314),'DLQ','max attempts hit',RED,clamp((p-.50)*5),'!')
    node(d,g,(956,213,1125,276),'RECOVERY','inspect + replay',MINT,clamp((p-.63)*5),'↗')
    line(d,[(685,237),(706,237),(706,216),(727,216)],(47,65,88),1)
    line(d,[(791,240),(791,267)],(47,65,88),1)
    line(d,[(856,290),(912,290),(912,244),(956,244)],(47,65,88),1)
    flow_dot(g,(856,290),(956,244),(p*2.1)%1,MINT,3)
    text(d,(726,322),'idempotency key  •  bounded retries  •  traceable jobs',F_MICRO,MUTED)


def scene_rag(d, g, p, t):
    text(d,(340,127),'KNOWLEDGE PIPELINE  /  DOCUMENTS → RETRIEVAL → GROUNDED ANSWERS',F_SMALL,MUTED)
    pill(d,1006,120,'RAG INDEX READY',VIOLET,width=136)
    # ingestion side
    rounded(d,(348,149,532,333),9,CARD,BORDER,1)
    text(d,(362,161),'SOURCE DOCUMENTS',F_LABEL,TEXT)
    docs=[('policies.pdf','PDF',AMBER),('support.md','MD',CYAN),('contracts.docx','DOC',BLUE)]
    for i,(name,tag,col) in enumerate(docs):
        yy=190+i*40; vis=clamp((p-i*.10)*5)
        rounded(d,(360,yy,519,yy+31),5,(13,22,33),mix(BORDER,col,.45*vis),1)
        rounded(d,(368,yy+6,389,yy+25),4,(25,35,50),mix(BORDER,col,.7),1)
        centered(d,(378,yy+15),tag,F_MICRO,col)
        text(d,(396,yy+9),name,F_SMALL,TEXT if vis>.5 else MUTED)
    # chunk and embed nodes
    node(d,g,(558,174,692,221),'CHUNK','overlap 120 tokens',BLUE,clamp((p-.08)*5),'01')
    node(d,g,(558,253,692,300),'EMBED','vector encoding',VIOLET,clamp((p-.19)*5),'AI')
    line(d,[(532,206),(545,206),(545,197),(558,197)],(47,65,88),1)
    line(d,[(625,221),(625,253)],(47,65,88),1)
    flow_dot(g,(532,206),(558,197),(p*2.1)%1,CYAN,2)
    # vector store and answer panel
    rounded(d,(714,149,1142,333),9,(10,16,25),BORDER,1)
    text(d,(730,161),'RETRIEVAL & CONTEXT',F_LABEL,TEXT)
    node(d,g,(730,191,856,241),'VECTOR DB','top-k similarity',CYAN,clamp((p-.29)*5),'V')
    node(d,g,(730,263,856,312),'RERANK','relevance scores',AMBER,clamp((p-.46)*5),'R')
    line(d,[(692,276),(708,276),(708,216),(730,216)],(47,65,88),1)
    line(d,[(793,241),(793,263)],(47,65,88),1)
    node(d,g,(897,214,1126,276),'GROUNDED ANSWER','citations + context',MINT,clamp((p-.62)*5),'✓')
    line(d,[(856,287),(877,287),(877,246),(897,246)],(47,65,88),1)
    flow_dot(g,(856,287),(897,246),(p*2.2)%1,MINT,2)
    text(d,(897,292),'Evidence checked before response',F_SMALL,MUTED)
    text(d,(897,311),'No matching source? → abstain / escalate',F_MICRO,AMBER)


def scene_security(d, g, p, t):
    text(d,(340,127),'TRUST BOUNDARIES  /  IDENTITY · POLICY · AUDIT',F_SMALL,MUTED)
    pill(d,1017,120,'ZERO TRUST FLOW',RED,width=125)
    xs=[350,505,660,815]; y=181; w=128; h=76
    specs=[('REQUEST','token attached',BLUE,'IN'),('IDENTITY','JWT / OAuth',CYAN,'ID'),('POLICY','role + scope',VIOLET,'RB'),('SERVICE','allow / deny',MINT,'✓')]
    for i in range(3):
        a=(xs[i]+w,y+38); b=(xs[i+1],y+38)
        line(d,[a,b],(44,62,83),2)
        flow_dot(g,a,b,(p*2.4-i*.20)%1,[BLUE,CYAN,VIOLET][i],3)
    for i,(lab,sub,col,ic) in enumerate(specs):
        vis=clamp((p-i*.13)*5.5)
        node(d,g,(xs[i],y,xs[i]+w,y+h),lab,sub,col,vis,ic,'ok')
    # secret vault and audit rail
    rounded(d,(350,280,1141,333),8,(10,16,25),BORDER,1)
    text(d,(365,291),'SECRET VAULT',F_LABEL,TEXT)
    text(d,(365,309),'masked • rotated • access-scoped',F_MICRO,MUTED)
    line(d,[(540,290),(540,322)],(39,55,74),1)
    text(d,(558,291),'AUDIT TRAIL',F_LABEL,TEXT)
    audit=[('03:14:02','scope checked'),('03:14:03','operation approved'),('03:14:03','event recorded')]
    for i,(tm,msg) in enumerate(audit):
        x=670+i*150; vis=p>i*.20
        dot(d,x,306,2.5,[CYAN,MINT,VIOLET][i] if vis else FAINT)
        text(d,(x+7,299),tm,F_MICRO,MUTED)
        text(d,(x+7,312),msg,F_MICRO,TEXT if vis else FAINT)


def scene_crm_mna(d, g, p, t):
    text(d,(340,127),'M&A INTELLIGENCE  /  INTAKE · DEDUPLICATE · SCORE',F_SMALL,MUTED)
    pill(d,994,120,'DEAL PIPELINE',VIOLET,width=148)
    # intake/inquiry panel
    rounded(d,(348,149,551,333),9,CARD,BORDER,1)
    text(d,(362,161),'INBOUND SIGNAL',F_LABEL,TEXT)
    rounded(d,(361,187,538,229),7,(18,27,40),(46,66,90),1)
    text(d,(372,196),'New broker listing',F_SMALL,TEXT)
    text(d,(372,211),'Northstar Cloud · SaaS',F_MICRO,MUTED)
    rounded(d,(361,240,538,282),7,(22,23,44),(78,68,121),1)
    text(d,(372,249),'AI extraction',F_SMALL,VIOLET)
    text(d,(372,264),'ARR • EBITDA • sector',F_MICRO,MUTED)
    text(d,(362,302),'1 source  /  1 candidate',F_MICRO,MUTED)
    # dedupe / score path
    node(d,g,(577,176,716,227),'DEDUPLICATE','fuzzy match 0.93',CYAN,clamp((p-.10)*5),'≈')
    node(d,g,(577,257,716,308),'BUY-BOX SCORE','fit 87 / 100',AMBER,clamp((p-.29)*5),'★')
    line(d,[(551,207),(565,207),(565,201),(577,201)],(47,65,88),1)
    line(d,[(646,227),(646,257)],(47,65,88),1)
    flow_dot(g,(551,207),(577,201),(p*2.2)%1,CYAN,2)
    # deal pipeline
    rounded(d,(738,149,1142,333),9,(10,16,25),BORDER,1)
    text(d,(753,161),'DEAL PIPELINE',F_LABEL,TEXT)
    cols=[('SOURCE',CYAN),('REVIEW',VIOLET),('QUALIFIED',MINT)]
    for i,(label,col) in enumerate(cols):
        x=752+i*128
        rounded(d,(x,188,x+116,313),6,(13,21,32),mix(BORDER,col,.40),1)
        text(d,(x+9,198),label,F_MICRO,col)
        # small cards staged across the columns
        cards=[('Lumen AI','fit 72'),('Northstar','fit 87'),('Meridian','fit 91')]
        for j,(company,fit) in enumerate(cards[:i+1]):
            yy=220+j*29; vis=clamp((p-(i+j)*.13)*5)
            if vis>0:
                rounded(d,(x+7,yy,x+109,yy+24),4,(21,31,44),mix(BORDER,col,.35),1)
                text(d,(x+12,yy+4),company,F_MICRO,TEXT)
                text(d,(x+12,yy+14),fit,F_MICRO,col)
    # handoff / audit strip
    text(d,(752,319),'score → associate review → audit event',F_MICRO,MUTED)


SCENES = [
    ('AUTOMATION CONTROL PLANE','Triggers, conditional routing, integrations and execution traces',CYAN,'workflow.run','5 stages executed'),
    ('VISUAL WORKFLOW ORCHESTRATION','Branched n8n-style workflows with CRM, email and team notifications',VIOLET,'workflow.orchestrate','branch paths completed'),
    ('VPS & SYSTEM ADMINISTRATION','Linux hosts, Docker workloads, reverse proxy and service health',MINT,'infra.health','3 hosts healthy'),
    ('BACKUP & DISASTER RECOVERY','Snapshots, integrity checks, retention policy and restore drills',MINT,'backup.verify','restore point verified'),
    ('DEVELOPMENT & GIT WORKFLOWS','Code changes, diffs, branches, reviews and testable commits',BLUE,'git.review','change validated'),
    ('CI/CD & RELEASE ENGINEERING','Build, test, container packaging, deployment and smoke checks',AMBER,'release.pipeline','health check passed'),
    ('REST APIs & WEBHOOKS','Identity, request validation, endpoint routing and service responses',BLUE,'api.gateway','201 response returned'),
    ('QUEUES & RELIABLE EXECUTION','Workers, backoff retries, idempotency, dead-letter and replay',AMBER,'queue.recovery','failed job recovered'),
    ('AI AGENTS & TOOL ORCHESTRATION','Planning, web search, SQL tools, evaluation and structured output',VIOLET,'agent.runtime','tool calls validated'),
    ('RAG & DOCUMENT INTELLIGENCE','Document ingestion, chunking, vector search and grounded answers',VIOLET,'knowledge.retrieve','sources retrieved'),
    ('DATABASES & DATA ENGINEERING','Normalization, schema validation, transactions and record upserts',CYAN,'data.pipeline','batch committed'),
    ('OBSERVABILITY & INCIDENT RESPONSE','Metrics, logs, traces, latency, alerting and recovery checks',MINT,'telemetry.stream','service recovered'),
    ('SECURITY & GOVERNANCE','Token validation, role permissions, secret protection and audit trails',RED,'security.policy','access decision logged'),
    ('EMAIL & BUSINESS AUTOMATION','CRM triggers, audience checks, delivery status and follow-up logic',AMBER,'mail.sequence','follow-up queued'),
    ('AI CHATBOT & HUMAN HANDOFF','Knowledge retrieval, confidence checks, safe responses and escalation',VIOLET,'support.route','answer validated or escalated'),
    ('CRM & M&A INTELLIGENCE','Listing intake, fuzzy deduplication, buy-box scoring and deal progression',VIOLET,'business.intel','deal scored and routed'),
]
DRAW_SCENES = [
    scene_automation, scene_n8n, scene_admin, scene_backup, scene_dev, scene_cicd,
    scene_api, scene_queue, scene_ai, scene_rag, scene_database, scene_tracking,
    scene_security, scene_email, scene_chatbot, scene_crm_mna
]


def static_frame_base(scene_idx, p, t):
    base=Image.new('RGB',(W,H),BG)
    d=ImageDraw.Draw(base)
    g=Image.new('RGBA',(W,H),(0,0,0,0))
    # technical grid and chassis
    for x in range(18,W,24): line(d,[(x,14),(x,H-14)],GRID,1)
    for y in range(17,H,24): line(d,[(14,y),(W-14,y)],GRID,1)
    rounded(d,(12,12,W-12,H-12),16,(8,13,21),(44,60,80),1)
    # left identity / brand rail
    rounded(d,(24,24,298,406),12,(11,17,27),(39,55,75),1)
    rounded(d,(40,42,76,78),9,(20,29,46),(75,91,132),1)
    # original monogram
    line(d,[(49,53),(57,48),(67,53),(67,66),(57,71),(49,66),(49,53)],VIOLET,2)
    line(d,[(53,57),(63,57)],CYAN,2); line(d,[(58,53),(58,67)],CYAN,2)
    text(d,(88,43),'SADAM UL HAQ',F_LABEL,TEXT)
    text(d,(88,60),'SYSTEMS / AUTOMATION',F_SMALL,MUTED)
    line(d,[(40,91),(282,91)],(36,51,70),1)
    text(d,(40,112),'ENGINEERING',F_MICRO,FAINT)
    text(d,(40,130),'From code to',F_HERO,TEXT)
    text(d,(40,156),'intelligent systems.',F_HERO,TEXT)
    text(d,(41,192),'Automation that connects',F_SUB,MUTED)
    text(d,(41,209),'tools, data, and people.',F_SUB,MUTED)
    # small status cards
    items=[('01','AUTOMATION',CYAN),('02','INFRA / OPS',MINT),('03','AI + DATA',VIOLET)]
    for i,(num,label,col) in enumerate(items):
        yy=247+i*35
        rounded(d,(40,yy,280,yy+27),6,(13,21,32),(33,48,66),1)
        text(d,(50,yy+7),num,F_SMALL,col)
        text(d,(79,yy+7),label,F_LABEL,TEXT)
        # tiny animated activity ticks
        # Fixed identity indicators keep the left rail visually stable across scene wipes.
        for j,barh in enumerate((4,6,5,3,4)):
            rounded(d,(227+j*8,yy+13-barh/2,231+j*8,yy+13+barh/2),1,col if j<4 else (40,55,72),None,0)
    # bottom status
    dot(d,44,373,3,MINT); glow_dot(g,44,373,MINT,3,100)
    text(d,(54,368),'SELF-HOSTED  /  OBSERVABLE',F_MICRO,MUTED)
    text(d,(40,389),'DESIGN  •  BUILD  •  OPERATE',F_MICRO,FAINT)
    # right workspace frame and scene header
    rounded(d,(310,24,1176,406),12,(10,16,25),(39,55,76),1)
    # small console crumbs
    text(d,(330,38),'SYSTEMS CONTROL ROOM',F_MICRO,FAINT)
    text(d,(330,56),SCENES[scene_idx][0],F_TITLE,TEXT)
    text(d,(330,82),SCENES[scene_idx][1],F_SUB,MUTED)
    # top-right animated badge
    col=SCENES[scene_idx][2]
    rounded(d,(1007,40,1157,72),7,(15,24,36),mix(BORDER,col,.5),1)
    dot(d,1020,51,3,col); glow_dot(g,1020,51,col,2,100)
    text(d,(1030,45),'SYSTEM ACTIVE',F_MICRO,col)
    text(d,(1030,57),f'MODULE {scene_idx+1:02d} / {len(SCENES):02d}',F_MICRO,MUTED)
    line(d,[(328,102),(1158,102)],(35,50,68),1)
    # active scene canvas
    DRAW_SCENES[scene_idx](d,g,p,t)
    # footer execution record
    line(d,[(328,349),(1158,349)],(34,49,67),1)
    key,msg=SCENES[scene_idx][3],SCENES[scene_idx][4]
    text(d,(332,365),'TRACE',F_MICRO,FAINT)
    text(d,(377,364),key,F_SMALL,col)
    text(d,(510,364),msg,F_SMALL,TEXT)
    # segmented stage progress indicator
    px=872; py=368
    for i in range(len(SCENES)):
        ww=12
        fill=SCENES[i][2] if i<=scene_idx else (35,49,66)
        rounded(d,(px+i*17,py,px+i*17+ww,py+5),2,fill,None,0)
    text(d,(872,382),f'{len(SCENES)}-SCENE SYSTEMS LOOP',F_MICRO,FAINT)
    text(d,(1090,382),f'{scene_idx+1:02d} / {len(SCENES):02d}',F_MICRO,col)
    # glow composite
    soft=g.filter(ImageFilter.GaussianBlur(6))
    base=Image.alpha_composite(base.convert('RGBA'),soft)
    base=Image.alpha_composite(base,g)
    return base.convert('RGB')


def make_transition(out_img, in_img, frac, sweep_color=CYAN):
    # A clean left-to-right luminous wipe uses the incoming scene accent color.
    # Pillow compositing is considerably faster than per-pixel Python loops.
    boundary=int(310+frac*(1176-310))
    mask=Image.new('L',(W,H),0)
    md=ImageDraw.Draw(mask)
    if boundary > 310:
        md.rectangle((310,24,min(boundary-1,W-1),406),fill=255)
    out=Image.composite(in_img,out_img,mask)
    # bright vertical sweep edge
    ov=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(ov,'RGBA')
    edge_alpha=int(22*(1-ease(frac)))
    line_alpha=int(210*(1-ease(frac)))
    if edge_alpha > 0:
        gd.rectangle((boundary-7,25,boundary+7,405),fill=(*sweep_color,edge_alpha))
    if line_alpha > 0:
        gd.line((boundary,27,boundary,403),fill=(*sweep_color,line_alpha),width=2)
    ov=ov.filter(ImageFilter.GaussianBlur(5))
    out=Image.alpha_composite(out.convert('RGBA'),ov).convert('RGB')
    return out


def render_scene_frame(scene_idx, frame_idx):
    # Start each scene with its structure already readable; movement then animates progress.
    p=0.75+0.25*ease(frame_idx/(STAGE_FRAMES-1))
    # Use elapsed time for continuous telemetry, pulse and scan-line movement.
    t=scene_idx*(STAGE_FRAMES+WIPE_FRAMES)*FRAME_MS/1000.0+frame_idx*FRAME_MS/1000.0
    return static_frame_base(scene_idx,p,t)


def save_contact_sheet(stage_previews):
    thumbs=[im.resize((480,172),Image.Resampling.LANCZOS) for im in stage_previews]
    sheet=Image.new('RGB',(1000,((len(thumbs)+1)//2)*202),(8,12,19))
    d=ImageDraw.Draw(sheet)
    for i,im in enumerate(thumbs):
        x=12+(i%2)*494; y=12+(i//2)*202
        sheet.paste(im,(x,y))
        d.rectangle((x,y,x+480,y+172),outline=(48,64,85),width=1)
    sheet.save(CONTACT,quality=90,optimize=True)


def build_animation():
    """Render frames to disk as they are made, then encode a looping GIF.

    Streaming PNG frames avoids retaining over a thousand full-resolution images in
    memory and lets FFmpeg perform palette mapping efficiently.
    """
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:
        raise RuntimeError('FFmpeg is required to build this high-frame-count GIF. Install FFmpeg and rerun the script.')

    expected_frames=len(SCENES)*(STAGE_FRAMES+WIPE_FRAMES)
    print(f'Rendering {len(SCENES)} scenes at {W}x{H}; target loop {expected_frames*FRAME_MS/1000:.2f}s',flush=True)
    t_start=time.time()
    with tempfile.TemporaryDirectory(prefix='sadam-workflow-',dir=ROOT) as td:
        frame_dir=os.path.join(td,'frames')
        os.makedirs(frame_dir,exist_ok=True)

        # Pre-render scene endpoints. They provide loop transitions, an attractive
        # static fallback preview, and coverage of every scene accent in the palette.
        first_frames=[]
        last_frames=[]
        for si in range(len(SCENES)):
            scene_start=si*(STAGE_FRAMES+WIPE_FRAMES)*FRAME_MS/1000.0
            first_frames.append(static_frame_base(si,0.75,scene_start))
            last_t=scene_start+(STAGE_FRAMES-1)*FRAME_MS/1000.0
            last_frames.append(static_frame_base(si,1.0,last_t))
        stage_previews=last_frames

        # Build one shared palette from the start and fully-developed view of every scene.
        palette_samples=first_frames+last_frames
        thumb_h=108
        thumb=Image.new('RGB',(300,thumb_h*len(palette_samples)),BG)
        for i,im in enumerate(palette_samples):
            thumb.paste(im.resize((300,thumb_h),Image.Resampling.LANCZOS),(0,thumb_h*i))
        pal=thumb.quantize(colors=256,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE)
        palette=pal.getpalette()[:256*3]
        palette_colors=[tuple(palette[i:i+3]) for i in range(0,len(palette),3)]
        palette_img=Image.new('RGB',(16,16),BG)
        palette_img.putdata(palette_colors)
        palette_path=os.path.join(td,'palette.png')
        palette_img.save(palette_path)

        frame_idx=0
        t_frames=time.time()
        for si in range(len(SCENES)):
            for fi in range(STAGE_FRAMES):
                im=render_scene_frame(si,fi)
                im.save(os.path.join(frame_dir,f'frame_{frame_idx:05d}.png'),format='PNG',compress_level=1)
                frame_idx+=1
            nxt=(si+1)%len(SCENES)
            for wi in range(WIPE_FRAMES):
                frac=ease((wi+1)/WIPE_FRAMES)
                im=make_transition(last_frames[si],first_frames[nxt],frac,SCENES[nxt][2])
                im.save(os.path.join(frame_dir,f'frame_{frame_idx:05d}.png'),format='PNG',compress_level=1)
                frame_idx+=1
            print(f'Completed scene {si+1}/{len(SCENES)} ({frame_idx}/{expected_frames} frames)',flush=True)
        print(f'Frame rendering and PNG export took {time.time()-t_frames:.1f}s',flush=True)

        optimized=OUT+'.optimized.gif'
        cmd=[ffmpeg,'-y','-hide_banner','-loglevel','error',
             '-framerate',f'{1000/FRAME_MS:g}','-i',os.path.join(frame_dir,'frame_%05d.png'),
             '-i',palette_path,
             '-filter_complex','[0:v][1:v]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle',
             '-gifflags','+transdiff','-loop','0',optimized]
        t_encode=time.time()
        subprocess.run(cmd,check=True)
        os.replace(optimized,OUT)
        print(f'GIF encoding took {time.time()-t_encode:.1f}s',flush=True)

    # Make sure the generated file is non-empty before reporting success.
    if not os.path.exists(OUT) or os.path.getsize(OUT)==0:
        raise RuntimeError('GIF output was not created.')
    print(f'Created {OUT}: {expected_frames} frames, {expected_frames*FRAME_MS/1000:.2f}s loop, {os.path.getsize(OUT)/1024/1024:.2f} MiB',flush=True)
    print(f'Total build time: {time.time()-t_start:.1f}s',flush=True)
    return stage_previews, expected_frames


if __name__=='__main__':
    stage_previews, frame_count=build_animation()
    stage_previews[0].save(PREVIEW)
    save_contact_sheet(stage_previews)
    print(f'Preview: {PREVIEW}')
    print(f'Contact sheet: {CONTACT}')
