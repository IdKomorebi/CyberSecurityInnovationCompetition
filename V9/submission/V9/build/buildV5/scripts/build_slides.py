"""Editable presentation supporting the report and recorded demonstration."""
from pathlib import Path
import sys
sys.path.insert(0,'/tmp/buildv5-pptxdeps')
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'slides';O.mkdir(exist_ok=True)
p=Presentation();p.slide_width=Inches(13.333);p.slide_height=Inches(7.5)
p.core_properties.author='';p.core_properties.last_modified_by='';p.core_properties.title='面向聚合推断威胁的数据定级与共享审查系统'
BLUE='2463B6';INK='182B45';SUB='52647A';BG='F5F8FC';TEAL='087E86';PURPLE='7052B5'
def rect(s,x,y,w,h,c):
 sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h));sh.fill.solid();sh.fill.fore_color.rgb=RGBColor.from_string(c);sh.line.fill.background();return sh

def text(s,x,y,w,h,value,size=24,color=INK,bold=False):
 tf=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)).text_frame;tf.word_wrap=True;tf.margin_left=0;tf.margin_right=0
 for i,line in enumerate(value.split('\n')):
  par=tf.paragraphs[0] if not i else tf.add_paragraph();par.text=line;par.font.name='Noto Sans CJK SC';par.font.size=Pt(size);par.font.bold=bold;par.font.color.rgb=RGBColor.from_string(color);par.space_after=Pt(10)
 return tf

def slide(title,sub='',notes=''):
 s=p.slides.add_slide(p.slide_layouts[6]);s.background.fill.solid();s.background.fill.fore_color.rgb=RGBColor.from_string(BG)
 rect(s,.48,.48,.08,.52,BLUE);text(s,.73,.36,12,0.65,title,29,bold=True)
 if sub:text(s,.75,1.08,11.9,.55,sub,16,SUB)
 text(s,.75,7.08,10,.22,'面向聚合推断威胁的数据定级与共享审查系统',10,SUB)
 text(s,12.05,7.04,.7,.3,f'{len(p.slides):02d}',12,BLUE)
 if notes:s.notes_slide.notes_text_frame.text=notes
 return s

def image(s,name,x=.75,y=1.75,w=11.85,h=5.05):
 path=R/'img'/name;im=Image.open(path);iw,ih=im.size;sc=min(w/iw,h/ih);ww,hh=iw*sc,ih*sc
 s.shapes.add_picture(str(path),Inches(x+(w-ww)/2),Inches(y+(h-hh)/2),width=Inches(ww),height=Inches(hh))

def cards(s,items,y=2.1):
 w=11.85/len(items)-.15
 for i,(title,body,color) in enumerate(items):
  x=.75+i*(w+.2);rect(s,x,y,w,3.35,'FFFFFF');rect(s,x+.22,y+.26,.45,.07,color);text(s,x+.25,y+.55,w-.5,.7,title,24,color,True);text(s,x+.25,y+1.42,w-.5,1.8,body,20,SUB)

s=slide('面向聚合推断威胁的','数据定级与共享审查系统')
text(s,.8,2.1,12,1.5,'从字段自身的敏感程度，\n走向考虑关联推断的整套等级方案。',34,INK,True)
for x,big,small,col in [(1,'7','公开数据集',BLUE),(5,'2116 → 8','已核对越线组合',TEAL),(9,'6 / 7','联合评估效用达到精确最优',PURPLE)]:
 text(s,x,4.6,3.8,.9,big,39,col,True);text(s,x,5.6,3.8,.8,small,18,SUB)
s.notes_slide.notes_text_frame.text='系统针对合法获取数据后的关联推断风险，在国标一次定级基础上补充聚合推断分析、联合定级和效果核对。'
s=slide('公开字段组合后，可能推出受保护信息','NEM 燃气机组 PPCCGT：单独与两两组合均不过线，三项合并达到 0.811。');image(s,'fig_aggr.jpg')
s=slide('沿“识别风险—调整等级—验证效果”形成完整流程','用户上传数据表、确认保护对象后，系统自动完成后续分析。');image(s,'fig_route.jpg')
s=slide('一次定级：依据国标确定字段本身的等级','大模型判断影响对象与程度，等级由 GB/T 43697 判定表确定；结果支持复核。');image(s,'ui_grade1.jpg')
s=slide('字段推断风险 M：背景下新增字段的最大作用','在至多 K 个背景字段的范围内，寻找能使该字段发挥最大作用的背景。')
for y,label,val,col in [(2.0,'风电预测单独使用',.183,BLUE),(3.1,'只有背景：可用容量 + 光伏预测',.223,'8795A7'),(4.2,'背景 + 风电预测',.811,PURPLE)]:
 text(s,.85,y,6,.4,label,21);rect(s,6.5,y+.05,4.5,.27,'E1E8F0');rect(s,6.5,y+.05,4.5*val,.27,col);text(s,11.25,y-.09,1,.5,f'{val:.3f}',24,col,True)
rect(s,.8,5.5,11.7,.85,'EDE7F6');text(s,1.1,5.62,11.1,.55,'M = 0.811 − 0.223 = 0.588  ≥  单独推断 0.183',26,PURPLE,True)
s=slide('越线组合：定位实际共享权限下的具体风险','PPCCGT 有 13 个已重训确认、用于定级的最小越线组合；均包含风电预测。', '截图默认还包含更大规模的估计候选，页面总数与 13 个已重训结果不是同一统计范围。');image(s,'ui_combos.jpg')
s=slide('二次定级：以统一效用确定整套等级方案','M ≥ 0.7 的字段直接定为对应保护对象等级；其他字段通过效用函数统一权衡。')
cards(s,[('字段推断风险','M 越大，留在低等级的风险扣分越高。',BLUE),('数据使用成本','等级调高，会减少能够获取该字段的接收方。',TEAL),('残留组合风险','仍可被接收方凑齐的越线组合，额外扣分。',PURPLE)])
text(s,.9,6.03,11.6,.6,'目标：降低推断风险，同时尽量保留共享价值。综合效用越高越好。',23,BLUE,True)
s=slide('强化学习：用组内比较寻找高效用方案','每一步采样完整方案、计算效用并更新策略，无需预先标注好的等级。');image(s,'fig_grpo3.jpg')
s=slide('整体核对：检查接收方真正能获取的全部字段','以完整可获取集合重新训练推断模型，发现风险后继续调整并核对。');image(s,'fig_whole.jpg')
s=slide('NEM 案例：风险降低，并保留可追溯的调级依据','调高 17 个字段；三台机组合计 14 个已重训确认的越线组合全部拆开。');image(s,'chart_nem.jpg',.75,1.7,11.85,4.6)
text(s,.9,6.4,11.7,.45,'PPCCGT 合并全部可见字段后的精度仍为 0.726，系统保留并展示残余风险。',17,SUB)
s=slide('七个公开数据集：已核对越线组合由 2116 个降至 8 个','覆盖电力市场、电网、社区统计、医疗保险、企业用电及人员在室等数据。');image(s,'chart_combos.jpg')
s=slide('联合评估：6 个任务达到精确最优效用','社区统计任务与精确最优相差 0.6%；比较范围为联合评估阶段的同一效用函数。');image(s,'chart_utility.jpg')
s=slide('可运行系统：从数据表到定级结果','提供任务管理、一次定级、单独推断、字段风险、越线组合、二次定级与效果核对。');image(s,'ui_tasks.jpg')
s=slide('风险结论与共享需求一起交给决策者','系统给出风险来源、调级理由和残余风险，支持按业务需求调整权衡。')
cards(s,[('风险可解释','字段为什么危险？\n哪些组合共同产生风险？',BLUE),('方案可比较','提升等级带来多少收益？\n会损失多少共享价值？',TEAL),('效果可核对','接收方合并全部字段后，\n还能推出多少保护信息？',PURPLE)])
text(s,.9,6.0,11.6,.55,'交付：正式报告、可运行程序、演示视频，以及可编辑的图稿与展示材料。',23,BLUE,True)
p.save(O/'作品展示.pptx')
print('slides',len(p.slides))
