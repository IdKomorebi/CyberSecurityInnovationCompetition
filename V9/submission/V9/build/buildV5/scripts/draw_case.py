"""NEM combination case, with editable SVG and the original figure aspect ratio."""
from draw_principles import SVG,INK,SUB,LINE,BLUE,TEAL,VIOLET,RED
s=SVG('fig_aggr',487,'同一组公开字段的两个视角','NEM 燃气机组 PPCCGT：三个字段合并越线，风电预测在背景下的最大增量明显高于单独推断。')
s.text(25,33,'同一组公开字段的两个视角',26,INK,700)
s.text(25,61,'NEM 2024 · 燃气机组 PPCCGT 为 2 级保护对象 · 社会公众判定线 0.7',16,SUB)
s.rect(20,85,505,357,'#f9fbfe',LINE,12);s.rect(545,85,435,357,'#f9fbfe',LINE,12)
s.text(38,115,'① 组合视角：三项凑齐后越线',19,INK,700)
s.text(563,115,'② 字段视角：背景放大新增字段的作用',18,INK,700)
points={1:(130,350),2:(273,350),4:(416,350),3:(130,259),5:(273,259),6:(416,259),7:(273,169)}
for a in [1,2,4,3,5,6]:
 for b in [3,5,6,7]:
  if a&b==a and b.bit_count()==a.bit_count()+1:
   x1,y1=points[a];x2,y2=points[b];s.line(x1,y1-29,x2,y2+30,LINE,1.7)
for bits,label,value in [(1,'可用容量','0.045'),(2,'风电预测','0.183'),(4,'光伏预测','0.186'),(3,'容量 + 风电','0.478'),(5,'容量 + 光伏','0.223'),(6,'风电 + 光伏','0.511'),(7,'三项凑齐','0.811')]:
 x,y=points[bits];col=RED if bits==7 else TEAL
 s.rect(x-65,y-30,130,62,'#fff5f5' if bits==7 else 'white',col,9)
 s.text(x,y-5,label,16,col,600,'middle');s.text(x,y+21,value,21,col,700,'middle')
s.text(40,412,'全部单项与两两组合不过线；三项合并越线。',15,SUB)
for y,label,value,color in [(152,'风电预测单独使用',.183,BLUE),(223,'只有背景：可用容量 + 光伏预测',.223,'#8e9eb1'),(294,'背景 + 风电预测',.811,VIOLET)]:
 s.text(565,y,label,16,INK);s.text(962,y,f'{value:.3f}',19,color,700,'end')
 s.rect(565,y+13,395,16,'#e1e8f0',rx=5);s.rect(565,y+13,395*value,16,color,rx=5)
s.rect(562,345,401,76,'#f2edff','#d6c9f1',9)
s.text(579,374,'M = 0.811 − 0.223 = 0.588',22,VIOLET,700)
s.text(579,401,'新增风电预测的作用，明显高于单独的 0.183。',14,SUB)
s.text(25,470,'容量、需求与发电调度之间的联系，使公开字段包含机组出力信息；推断能力由数据验证。',16,SUB)
s.save()
