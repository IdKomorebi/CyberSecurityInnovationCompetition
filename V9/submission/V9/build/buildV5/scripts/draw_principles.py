"""Draw the five buildV3 additions as editable, self-contained SVG diagrams.

Run with the Pytorch310_codex Python environment (CairoSVG and Pillow installed).
The original aspect ratios are deliberate: replacing the media preserves pagination.
"""
from pathlib import Path
from html import escape
import math
import re
import cairosvg
from PIL import Image
from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
INK = '#182b45'
SUB = '#52647a'
LINE = '#d7e0e9'
BLUE = '#2463b6'
TEAL = '#087e86'
VIOLET = '#7052b5'
AMBER = '#b56a16'
RED = '#bf4a49'
GREY = '#8795a7'


class SVG:
    def __init__(self, name, height, title, desc):
        self.name, self.height = name, height
        self.s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="{height*2}" viewBox="0 0 1000 {height}" role="img" aria-labelledby="title desc">',
                  f'<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>',
                  '<defs>']
        for color in [INK, SUB, BLUE, TEAL, VIOLET, AMBER, RED, GREY]:
            self.s.append(f'<marker id="arrow{color[1:]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="{color}" stroke-width="1.5"/></marker>')
        self.s += ['<pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse"><path d="M-1 1L1-1M0 6L6 0M5 7L7 5" stroke="#d1d9e4" stroke-width="1"/></pattern>', '</defs>', '<rect width="1000" height="100%" fill="white"/>']

    def text(self, x, y, value, size=20, color=INK, weight=400, anchor='start'):
        # Cairo does not perform browser-style glyph fallback. Explicit spans keep
        # subscripts, Greek symbols and accents from becoming missing-glyph boxes.
        parts = re.split(r'([\u2e80-\u9fff\uff00-\uffef]+)', str(value))
        if anchor != 'start':
            width = 0
            for p in parts:
                chinese = bool(re.search(r'[\u2e80-\u9fff\uff00-\uffef]',p))
                fp = ('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if weight>=600 else 'Regular')+'.ttc' if chinese else '/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if weight>=600 else '')+'.ttf')
                ft = ImageFont.truetype(fp,round(size*4),index=2 if chinese else 0)
                width += ft.getlength(p)/4
            x -= width/2 if anchor == 'middle' else width
            anchor = 'start'
        spans = ''.join('<tspan font-family="'+('Noto Sans CJK SC,Microsoft YaHei,PingFang SC,sans-serif' if re.search(r'[\u2e80-\u9fff\uff00-\uffef]',p) else 'DejaVu Sans,Arial,sans-serif')+'">'+escape(p)+'</tspan>' for p in parts if p)
        self.s.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{spans}</text>')

    def rect(self, x, y, w, h, fill='none', stroke='none', rx=0, sw=1.5):
        self.s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def circle(self, x, y, r, fill='white', stroke=LINE, sw=1.5):
        self.s.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def path(self, d, color=LINE, sw=2, fill='none', dash=None, arrow=False):
        extra = (f' stroke-dasharray="{dash}"' if dash else '') + (f' marker-end="url(#arrow{color[1:]})"' if arrow else '')
        self.s.append(f'<path d="{d}" stroke="{color}" stroke-width="{sw}" fill="{fill}" stroke-linejoin="round" stroke-linecap="round"{extra}/>')

    def line(self, x1, y1, x2, y2, color=LINE, sw=2, dash=None, arrow=False):
        self.path(f'M{x1} {y1}L{x2} {y2}', color, sw, dash=dash, arrow=arrow)

    def heading(self, x, y, n, title, color=BLUE):
        self.circle(x+12, y-7, 13, color, color)
        self.text(x+12, y-1, n, 15, 'white', 700, 'middle')
        self.text(x+35, y, title, 23, INK, 700)

    def matrix(self, x, y, rows, cols, cw=22, ch=17, color=BLUE, active=None):
        for r in range(rows):
            for c in range(cols):
                on = active is None or c in active
                self.rect(x+c*cw, y+r*ch, cw-3, ch-3, color if on else 'url(#hatch)', 'white', 2)
        self.path(f'M{x-5} {y-3}h-5v{rows*ch+3}h5M{x+cols*cw} {y-3}h5v{rows*ch+3}h-5',SUB,1.3)

    def network(self, x, y, widths=(3,4,3,1), dx=42, dy=19, color=BLUE, radius=5):
        layers = [[(x+i*dx,y+(j-(w-1)/2)*dy) for j in range(w)] for i,w in enumerate(widths)]
        for a,b in zip(layers,layers[1:]):
            for u in a:
                for v in b: self.line(*u,*v,LINE,1.2)
        for layer in layers:
            for u in layer: self.circle(*u,radius,'white',color,1.8)

    def save(self):
        path = ROOT/'img'/'svg'/f'{self.name}.svg'
        path.write_text('\n'.join(self.s+['</svg>']), encoding='utf-8')
        png = ROOT/'img'/f'{self.name}.png'
        cairosvg.svg2png(url=str(path),write_to=str(png))
        Image.open(png).convert('RGB').save(ROOT/'img'/f'{self.name}.jpg',quality=96,subsampling=0)
        print(path.name)


def batch():
    s=SVG('fig_batch',568,'遮挡输入的成批训练','上半图以三组遮挡矩阵和三个神经网络展示参数独立；下半图以张量堆叠展示批量计算与独立梯度。')
    s.heading(28,36,'1','遮挡输入，保留组合字段')
    s.heading(410,36,'2','同构网络，各自学习参数')
    s.text(867,36,'留出评估',22,TEAL,700)
    cols=[BLUE,TEAL,VIOLET]
    masks=[[0,2],[1,3,4],[0,1]]
    for i,(color,active) in enumerate(zip(cols,masks)):
        y=105+i*91
        s.text(30,y+8,f'S{i+1}',25,color,700)
        s.matrix(83,y-27,3,5,27,20,color,active)
        s.text(237,y+7,'x ⊙ m',21,SUB)
        s.line(320,y+1,391,y+1,color,2,arrow=True)
        s.network(418,y,(4,5,3,1),67,13,color,5)
        s.text(690,y-10,f'W{i+1}',23,color,700)
        s.text(690,y+17,f'损失 L{i+1}',18,SUB)
        s.line(787,y,846,y,color,2,arrow=True)
        s.circle(905,y,31,'#f4f8fc',color,1.7)
        s.text(905,y+7,f'V(S{i+1})',19,color,600,'middle')
    s.text(84,354,'实色：可见字段',18,SUB)
    s.rect(258,338,18,18,'url(#hatch)',LINE,2)
    s.text(286,354,'斜纹：输入置零',18,SUB)
    s.line(28,375,972,375,LINE,1.5)
    s.heading(28,411,'3','沿组合维堆叠，一次计算',VIOLET)
    for i in reversed(range(3)):
        x=80+i*16; y=444-i*9
        s.rect(x,y,135,59,'white',cols[i],3)
        for r in range(3):
            for c in range(6): s.rect(x+8+c*20,y+7+r*16,15,11,cols[i],rx=1)
    s.text(80,539,'[W₁, W₂, W₃]',20,INK,600)
    s.line(268,471,336,471,VIOLET,2.5,arrow=True)
    s.text(370,463,'批量矩阵乘法',24,VIOLET,700)
    s.text(370,495,'前向与反向同时完成',19,SUB)
    s.line(588,471,650,471,VIOLET,2.5,arrow=True)
    s.text(679,459,'L = L₁ + L₂ + L₃',25,INK,600)
    s.text(679,493,'∂L / ∂Wᵢ = ∂Lᵢ / ∂Wᵢ',23,INK)
    s.text(679,533,'每组梯度只来自自身损失',19,TEAL,600)
    s.save()


def gate():
    s=SVG('fig_gate',489,'门控网络与诱饵门槛','真实字段与打乱副本一起进入分解式门控网络；以诱饵强度90%分位数确定作用强度的筛选门槛。图中强度为示意。')
    s.heading(25,37,'1','构造诱饵')
    s.heading(280,37,'2','整行权重门控',VIOLET)
    s.heading(635,37,'3','按作用强度筛选',TEAL)
    s.line(251,63,251,377,LINE,1,dash='3 5')
    s.line(605,63,605,377,LINE,1,dash='3 5')
    s.text(34,83,'真实列',19,BLUE,600)
    s.text(156,83,'打乱副本',19,GREY,600)
    shades=['#2a61a9','#79a0ce','#b3c9e5','#4e81be','#93b1d7']
    perm=[2,4,0,3,1]
    for i in range(5):
        y=103+i*29
        s.rect(48,y,48,21,shades[i],rx=3)
        s.rect(170,y,48,21,shades[perm[i]],rx=3)
        dest=perm.index(i)
        s.line(101,y+10,165,113+dest*29,LINE,1.2)
    s.text(30,291,'边缘分布保持',19,SUB)
    s.text(30,321,'打乱与目标的对应',19,SUB)
    s.text(30,355,'30 个诱饵作为参照',19,GREY,600)
    # Visible inputs and gates: open / nearly closed channels.
    for i,(label,col,strength) in enumerate([('x₁',BLUE,4),('x₂',BLUE,2.5),('x₃',BLUE,.7),('诱饵',GREY,.6)]):
        y=101+i*66
        s.text(277,y+7,label,20,col,600)
        s.line(322,y,350,y,col,1.6)
        s.circle(366,y,14,'#f4f2fb',VIOLET,1.6)
        s.text(366,y+6,'×',22,VIOLET,500,'middle')
        s.line(381,y,445,y,col,strength)
        for yy in [136,188,240]: s.line(445,y,483,yy,col,max(.6,strength*.4))
    for yy in [136,188,240]:
        s.circle(489,yy,7,'white',VIOLET,2)
        s.line(496,yy,546,188,LINE,1.5)
    s.circle(553,188,9,'white',TEAL,2)
    s.text(566,195,'ŷ',22,TEAL,600)
    s.text(333,352,'门控之积 × 权重行 Ωᵢ',18,VIOLET,600)
    s.text(293,378,'平方惩罚 → 无关行趋近于零',18,SUB)
    # Threshold is vertical on the quantitative axis, not between sorted categories.
    x0=724; scale=225; threshold=.30
    vals=[('字段 7',.91,BLUE),('字段 2',.74,BLUE),('字段 11',.58,BLUE),('诱饵 3',.32,GREY),('字段 5',.21,'#bdc9d7'),('诱饵 8',.12,GREY)]
    for i,(label,v,col) in enumerate(vals):
        y=114+i*37
        s.text(708,y+6,label,18,SUB,400,'end')
        s.line(x0,y,x0+v*scale,y,col,10)
        s.circle(x0+v*scale,y,5,col,col)
    s.line(x0+threshold*scale,84,x0+threshold*scale,320,RED,1.8,dash='5 4')
    s.text(793,76,'90% 分位门槛',18,RED,600)
    s.line(x0,325,957,325,SUB,1.2,arrow=True)
    s.text(827,353,'作用强度 rᵢ',18,SUB)
    s.text(635,380,'高于门槛的真实字段进入组合估计',18,TEAL,600)
    s.rect(25,408,950,59,'#f3f6fa',rx=6)
    s.text(45,445,'rᵢ = |∏ γᵢ| · ‖Ωᵢ‖',24,VIOLET,600)
    s.text(385,445,'诱饵强度提供“无关”的经验参照',21,INK)
    s.text(954,447,'强度示意',16,SUB,400,'end')
    s.save()


def readout():
    s=SVG('fig_readout',533,'共享主干与逐组合闭式读出','预训练时同时预测保护对象和重建遮挡字段。预训练之后冻结同一个主干，每个组合提取特征并独立求岭回归闭式解，在留出行计算估计精度。')
    s.heading(26,35,'1','预训练一次：预测 + 重建',VIOLET)
    s.text(31,90,'随机遮挡',21,INK,600)
    s.matrix(39,111,3,5,24,20,BLUE,[0,2,4])
    s.text(32,205,'[x ⊙ m, m]',21,SUB)
    s.line(189,141,255,141,VIOLET,2,arrow=True)
    s.network(277,141,(4,5,5,5),55,20,VIOLET,6)
    s.text(325,220,'主干 h：3 × 256',21,VIOLET,600)
    s.path('M457 141H511V103H548',VIOLET,2,arrow=True)
    s.path('M511 141V186H548',VIOLET,2,arrow=True)
    s.text(567,80,'预测保护对象',20,TEAL,600)
    s.line(568,127,718,127,LINE,1)
    s.path('M570 117L588 101L603 113L623 89L641 106L661 85L681 101L703 91',TEAL,2.5)
    s.text(567,162,'重建被遮字段',20,BLUE,600)
    s.matrix(572,178,2,5,26,17,BLUE,[1,3])
    s.text(757,112,'预测误差',21,TEAL,600)
    s.text(805,145,'+',24,SUB)
    s.text(757,181,'重建误差',21,BLUE,600)
    s.line(26,247,974,247,LINE,1.5)
    s.heading(26,285,'2','冻结同一主干，逐组合求解',VIOLET)
    s.text(774,283,'每个组合独立拟合 β',20,BLUE,600)
    for i,(color,mask) in enumerate([(BLUE,[0,2]),(TEAL,[1,2,3])]):
        y=348+i*89
        s.text(31,y+7,f'S{i+1}',22,color,700)
        s.matrix(78,y-16,2,4,22,17,color,mask)
        s.line(177,y,230,y,color,2,arrow=True)
        s.path(f'M236 {y}H269L300 391',color,1.7)
        s.path(f'M430 391L465 {y}H500',color,1.7,arrow=True)
        s.matrix(521,y-16,2,5,18,17,color)
        s.text(637,y+7,f'φS{i+1}',20,color,600)
        s.line(692,y,735,y,color,2,arrow=True)
        s.circle(772,y,25,'#f3f7fb',color,1.5)
        s.text(772,y+7,f'βS{i+1}',20,color,600,'middle')
        s.line(809,y,857,y,color,2,arrow=True)
        s.text(882,y+7,f'Ṽ(S{i+1})',23,color,700)
    s.network(302,391,(3,4,3),60,18,VIOLET,5)
    # Lock glyph identifies the only shared, frozen component.
    s.path('M354 333V325C354 312 373 312 373 325V333',VIOLET,2)
    s.rect(348,331,31,23,'#eee9f8',VIOLET,3)
    s.circle(363.5,340,2,VIOLET,VIOLET)
    s.line(363.5,342,363.5,347,VIOLET,1.5)
    s.text(362,466,'共享 h',19,VIOLET,600,'middle')
    s.text(521,478,'φS = [x ⊙ m, (x ⊙ m)², h]',19,SUB)
    s.text(31,514,'训练行：βS = (ΦSᵀΦS + λI)⁻¹ΦSᵀY',22,INK)
    s.text(611,514,'留出行：计算 Ṽ(S)',21,TEAL,600)
    s.save()


def grpo():
    s=SVG('fig_grpo3',570,'组相对策略优化的训练循环','策略输出字段等级概率，采样整套等级方案，以三项效用评分，通过组内标准化优势更新策略。精确最优在循环之外只作对照。矩阵、概率和效用条均为机制示意。')
    s.heading(27,36,'1','策略给出等级概率',VIOLET)
    s.heading(605,36,'2','采样整套等级方案',BLUE)
    s.network(43,122,(3,4,3),39,23,VIOLET,6)
    s.line(132,122,174,122,VIOLET,2,arrow=True)
    for r,values in enumerate([[.60,.40,0,0],[.10,.55,.25,.10],[0,.20,.55,.25]]):
        y=77+r*40
        s.text(186,y+18,'ABC'[r],17,SUB)
        x=212
        for j,v in enumerate(values):
            if v:
                s.rect(x,y,171*v,23,[BLUE,TEAL,AMBER,VIOLET][j],rx=2)
                if v>.24: s.text(x+171*v/2,y+17,str(v),15,'white',500,'middle')
            x+=171*v
    for j in range(4):
        s.circle(203+j*52,213,5,[BLUE,TEAL,AMBER,VIOLET][j],'none')
        s.text(214+j*52,219,str(j+1)+'级',15,SUB)
    s.text(32,251,'一次等级 / 下限 / M / 罚分占比 / 权重',17,SUB)
    s.line(410,125,571,125,BLUE,2.5,arrow=True)
    s.text(491,106,'独立采样',18,BLUE,600,'middle')
    for j,label in enumerate(['A','B','C','…']): s.text(755+j*50,76,label,18,SUB,500,'middle')
    matrix=[[1,2,3],[2,2,4],[1,3,3],[2,2,3]]
    for i,row in enumerate(matrix):
        y=91+i*37
        s.text(622,y+21,f'方案 {i+1}',18,SUB)
        for j,v in enumerate(row):
            s.rect(737+j*50,y,35,28,['',BLUE,TEAL,AMBER,VIOLET][v],rx=4)
            s.text(754+j*50,y+21,v,19,'white',600,'middle')
        s.text(906,y+21,'…',20,SUB)
    s.path('M949 144H974V304H949',BLUE,2.5,arrow=True)
    s.heading(605,283,'3','效用评分与组内比较',AMBER)
    s.text(622,317,'安全收益 − 可用性成本 − 聚合惩罚',17,SUB)
    # Higher utility is rightward; bars show centered group advantages.
    s.line(784,338,784,431,GREY,1.2,dash='4 4')
    for i,(val,col) in enumerate([(-.65,RED),(.85,TEAL),(-.35,RED),(.50,TEAL)]):
        y=345+i*25
        s.text(681,y+6,str(i+1),17,SUB)
        s.line(784,y,784+val*115,y,col,10)
    s.text(784,456,'组内均值',16,SUB,400,'middle')
    s.heading(27,303,'4','按相对优势更新策略',VIOLET)
    s.text(49,346,'Â = (U − 组内均值) / 标准差',22,INK,600)
    s.text(49,385,'提高优于组内平均的方案概率',21,VIOLET,600)
    s.text(49,422,'记录已采样方案中效用最高者',19,SUB)
    s.path('M604 386H458',VIOLET,2.5,arrow=True)
    s.path('M23 400H10V122H27',VIOLET,2.5,arrow=True)
    s.text(494,222,'128 套 / 步',19,INK,700,'middle')
    s.text(494,252,'400 步',20,VIOLET,700,'middle')
    s.line(27,480,974,480,LINE,1.5,dash='5 5')
    s.text(28,520,'独立对照',21,TEAL,700)
    s.text(159,520,'同一效用 U',20,INK)
    s.line(284,513,330,513,GREY,1.8,arrow=True)
    s.text(349,520,'穷举 / 整数规划',20,INK)
    s.line(532,513,579,513,GREY,1.8,arrow=True)
    s.text(599,520,'精确最优',20,TEAL,600)
    s.text(764,520,'检验学习结果',20,SUB)
    s.text(974,552,'精确解不参与策略训练；矩阵与条形为机制示意',16,SUB,400,'end')
    s.save()


def whole():
    s=SVG('fig_whole',469,'整体核对与路径选择','从接收方可见的全部字段出发，重新训练神经网络和梯度提升树；若仍越线，以估计筛选和重训确认逐步撤出字段，在路径上选择累计代价加惩罚最低的位置，再逆序尝试放回。曲线仅示意机制。')
    s.heading(25,34,'1','合并全部可见字段',BLUE)
    for i in range(6):
        x=48+(i%3)*66; y=81+(i//3)*42
        s.circle(x,y,14,'#eaf2fb',BLUE,1.5)
        s.text(x,y+6,'abcdef'[i],17,BLUE,600,'middle')
    s.text(28,165,'按接收方权限取集合',18,SUB)
    s.line(202,104,267,104,BLUE,2,arrow=True)
    s.text(287,82,'重新训练',23,INK,700)
    s.text(287,115,'神经网络 + 梯度提升树',18,SUB)
    s.text(287,146,'取较高精度，与判定线比较',18,SUB)
    s.line(538,104,590,104,RED,2,arrow=True)
    s.text(565,83,'越线',17,RED,600,'middle')
    s.heading(610,34,'2','逐步撤出字段',VIOLET)
    s.text(622,82,'估计各字段撤出后的效果',20,INK)
    s.text(622,115,'前 6 个重新训练 → 撤出净收益最大者',18,SUB)
    for i in range(5):
        x=640+i*66
        s.circle(x,155,13,'white',VIOLET,1.5)
        s.text(x,161,'abcde'[i],17,VIOLET,500,'middle')
        if i<4: s.line(x+15,155,x+48,155,VIOLET,1.5,arrow=True)
    s.path('M933 157H960V64H941',VIOLET,1.8,arrow=True)
    s.line(25,194,975,194,LINE,1.5)
    s.heading(25,229,'3','沿撤出路径选停止位置',TEAL)
    s.text(486,229,'路径示意',16,SUB,400,'end')
    # Cost + whole-inference penalty, both shown on the same conceptual scale.
    x0=61; y0=374; xs=[x0+i*70 for i in range(6)]
    cost=[0,13,29,48,71,98]; penalty=[112,76,44,20,10,4]
    total=[a+b for a,b in zip(cost,penalty)]
    s.line(x0,255,x0,y0,SUB,1.3)
    s.line(x0,y0,438,y0,SUB,1.3,arrow=True)
    for vals,col in [(cost,AMBER),(penalty,BLUE),(total,TEAL)]:
        s.path('M'+'L'.join(f'{x} {y0-v}' for x,v in zip(xs,vals)),col,2.6)
        for x,v in zip(xs,vals): s.circle(x,y0-v,3,col,col)
    best=3
    s.line(xs[best],y0-total[best],xs[best],y0,TEAL,1.5,dash='4 4')
    s.circle(xs[best],y0-total[best],6,'white',TEAL,2.5)
    s.text(xs[best]+9,y0-total[best]-12,'最小值',18,TEAL,700)
    for i,x in enumerate(xs): s.text(x,397,i,16,SUB,400,'middle')
    s.text(448,399,'撤出步数 j',16,SUB)
    for y,label,col in [(267,'累计代价',AMBER),(298,'整体惩罚',BLUE),(329,'两者之和',TEAL)]:
        s.line(447,y,471,y,col,2.5)
        s.text(482,y+6,label,17,col,600)
    s.heading(636,229,'4','逆序尝试放回',TEAL)
    for i,label in enumerate(['c','b','a']):
        x=672+i*103
        s.circle(x,283,21,'#edf7f5',TEAL,1.8)
        s.text(x,290,label,22,TEAL,600,'middle')
        if i<2:s.line(x+26,283,x+74,283,TEAL,1.8,arrow=True)
    s.text(638,337,'放回节省的代价 > 增加的惩罚',18,INK)
    s.text(638,370,'满足则放回，得到最终等级',20,TEAL,600)
    s.rect(25,418,950,36,'#f3f6fa',rx=5)
    s.text(43,443,'默认模式：按代价与风险权衡停止位置。严格模式：持续撤出至不再越线。',19,INK)
    s.save()


if __name__ == '__main__':
    (ROOT/'img'/'svg').mkdir(parents=True,exist_ok=True)
    for draw in (batch,gate,readout,grpo,whole): draw()
