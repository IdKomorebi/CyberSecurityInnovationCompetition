"""Fixed-size explanatory boards; values are from the approved NEM example."""
from html import escape

CSS = '''
#v7-board{position:fixed;inset:0;z-index:9999990;background:#f5f8fd;color:#152844;font-family:"Noto Sans CJK SC",sans-serif;overflow:hidden}
#v7-board *{box-sizing:border-box}
#v7-board .eyebrow{position:absolute;left:72px;top:42px;font-size:21px;color:#587299;letter-spacing:2px}
#v7-board h1{margin:0;position:absolute;left:72px;top:94px;font-size:43px;line-height:1.45;letter-spacing:1px}
#v7-board .subhead{position:absolute;left:75px;top:162px;font-size:24px;color:#61718b}
#v7-board .panel{position:absolute;top:220px;height:510px;border:1px solid #d9e3f1;border-radius:20px;background:white;padding:30px}
#v7-board .panel h2{font-size:25px;margin:0 0 24px;color:#244d88}
#v7-board .wide-title{top:130px;font-size:58px;line-height:1.55}
#v7-board .big{font-size:52px;font-weight:750;color:#225db4}
#v7-board .muted{font-size:25px;color:#64748b;line-height:1.8}
#v7-board .formula{font-size:39px;font-weight:750;color:#7250bc;white-space:nowrap;margin:35px 0 25px}
#v7-board .tag{display:inline-block;border-radius:10px;background:#eef4fd;color:#285fac;padding:10px 16px;margin:8px 6px 0 0;font-size:23px;font-weight:600}
#v7-board .note{position:absolute;left:72px;bottom:25px;font-size:20px;color:#6d7e96}
#v7-board .metric-row{margin-top:28px;font-size:25px;color:#47617e}
#v7-board .metric-row strong{float:right;color:#294c7c;font-size:30px}
#v7-board .track{height:28px;background:#eef2f7;border-radius:6px;overflow:hidden;margin-top:12px;position:relative}
#v7-board .fill{height:100%;background:#6399e0;display:inline-block;vertical-align:top}
#v7-board .callout{font-size:27px;font-weight:650;padding:22px;background:#f4f0fc;border-radius:12px;color:#7050b0;margin-top:28px;line-height:1.6}
#v7-board .rail{display:flex;align-items:center;justify-content:center;gap:28px;margin-top:28px}
#v7-board .rail .step{padding:28px 24px;border-radius:14px;background:#edf3fc;text-align:center;font-size:28px;line-height:1.7}
'''


def shell(inner):
    return '<style>'+CSS+'</style>'+inner


def intro(stage=1):
    if stage == 1:
        return shell('''<div class="eyebrow">面向聚合推断威胁的数据定级与共享审查系统</div>
        <h1 class="wide-title">一个字段应该定几级？</h1>
        <div style="position:absolute;left:75px;top:310px;right:75px">
        <div class="muted" style="font-size:30px">通常先看：这个字段泄露以后，会造成什么影响</div>
        <div class="rail" style="justify-content:flex-start;margin-top:55px">
          <div class="step">影响谁<br><b>影响对象</b></div><b style="font-size:34px">＋</b>
          <div class="step">影响多大<br><b>影响程度</b></div><b style="font-size:38px;color:#4f78b5">→</b>
          <div class="step" style="background:#e7f3f1;color:#14796f">字段本身的<br><b>等级</b></div>
        </div></div>''')
    return shell('''<div class="eyebrow">问题：字段之间还存在关联</div>
    <h1 class="wide-title">逐个看起来安全，<br>放在一起，还安全吗？</h1>
    <div style="position:absolute;left:80px;right:80px;top:410px;display:flex;gap:30px;align-items:center">
      <div class="rail" style="gap:15px;margin:0"><div class="step">公开字段 A</div><b>＋</b><div class="step">公开字段 B</div><b>＋</b><div class="step">公开字段 C</div></div>
      <b style="font-size:46px;color:#dc4b50">→</b><div class="step" style="padding:30px;font-size:30px;color:#b63242;border:2px solid #e3a5ab;border-radius:16px">本不该公开的<br><b>保护对象</b></div>
    </div><div class="note">聚合推断：利用多个可获取的字段，推断无权获取的数据。</div>''')


def case(stage):
    # The layout never zooms or pans. Individual nodes become legible as narrated.
    nodes = {
        'capacity': (18, 379, 192, 98, '可用发电容量', '0.045', 7),
        'wind': (239, 379, 192, 98, '风电预测', '0.183', 6),
        'solar': (460, 379, 192, 98, '光伏预测', '0.186', 11),
        'cw': (18, 216, 192, 98, '容量 + 风电', '0.478', 8),
        'cs': (239, 216, 192, 98, '容量 + 光伏', '0.223', 11),
        'ws': (460, 216, 192, 98, '风电 + 光伏', '0.511', 13),
        'all': (225, 45, 220, 106, '三个字段合起来', '0.811', 11),
    }
    edges = [('capacity','cw'),('wind','cw'),('capacity','cs'),('solar','cs'),('wind','ws'),('solar','ws'),('cw','all'),('cs','all'),('ws','all')]
    svg = '<svg width="670" height="500" viewBox="0 0 670 500" style="position:absolute;left:28px;top:32px">'
    for a,b in edges:
        x,y,w,h,*_=nodes[a];xx,yy,ww,hh,*_=nodes[b]
        svg+=f'<path d="M{x+w/2} {y} L{xx+ww/2} {yy+hh}" fill="none" stroke="#d9e3ef" stroke-width="2"/>'
    active = {6:['wind'],7:['capacity'],8:['cw'],10:['capacity','cw'],11:['cs','all'],12:['cs','all'],13:['all'],14:['wind']} .get(stage,[])
    for key,(x,y,w,h,label,value,show_at) in nodes.items():
        visible = stage>=show_at
        if stage == 3: visible=False
        color='#c63846' if key=='all' and visible else '#285b9b'
        border='#db343b' if key in active else '#cedceb'
        shown=value if visible else '—'
        svg+=f'<g id="case-{key}" opacity="{1 if visible else .4}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{("#fff3f4" if key=="all" and visible else "white")}" stroke="{border}" stroke-width="{3 if key in active else 1.4}"/><text x="{x+w/2}" y="{y+35}" text-anchor="middle" font-size="22" font-weight="650" fill="{color}">{label}</text><text x="{x+w/2}" y="{y+78}" text-anchor="middle" font-size="34" font-weight="700" fill="{color}">{shown}</text></g>'
    svg+='</svg>'
    if stage == 3:
        right='''<h2>需要保护的目标</h2><div class="big" style="font-size:40px;margin:45px 0 20px">燃气机组每小时的出力</div><div class="muted">澳大利亚国家电力市场<br>PPCCGT 机组</div><div style="margin-top:45px"><span class="tag">目标：2 级</span><span class="tag">公众可获取：1 级</span></div>'''
    elif stage in [4,5]:
        right='''<h2>推断精度：预测的准确程度</h2><div class="muted">训练模型，用没见过的数据验证</div><div style="display:flex;justify-content:space-between;margin-top:56px"><b class="big">0</b><b class="big">1</b></div><div class="track" style="height:28px;background:linear-gradient(90deg,#c8dcf5,#477fd0)"></div><div style="display:flex;justify-content:space-between;font-size:25px;margin-top:16px"><span>完全推不出</span><span>完全还原</span></div><div class="callout" style="color:#bd3746;background:#fff0f1">判定线 0.7：超过即存在推断风险</div>'''
    elif stage in [6,7,8]:
        right='''<h2>只看单个字段，会遗漏什么？</h2>'''
        for lab,val,at in [('风电预测',.183,6),('可用发电容量',.045,7),('容量 + 风电',.478,8)]:
            if stage>=at:
                right+=f'<div class="metric-row">{lab}<strong>{val:.3f}</strong><div class="track"><div class="fill" style="width:{val*100}%"></div></div></div>'
        if stage==8:right+='<div class="callout" style="margin-top:18px;padding:16px;font-size:25px;line-height:1.5">0.478 &gt; 0.183 + 0.045<br>两者之间存在协同关系</div>'
    elif stage == 10:
        right='''<h2>已有一个背景字段时</h2><div class="muted">背景：可用发电容量<br>再加入：风电预测</div><div class="formula">0.478 − 0.045 = 0.433</div><div class="callout">要看加入风电后提高了多少，<br>不能只看单独的 0.183。</div>'''
    elif stage in [11,12]:
        right='''<h2>已有两个背景字段时</h2><div class="muted" style="font-size:23px">背景：可用发电容量 + 光伏预测</div>
        <div class="metric-row">只有背景<strong>0.223</strong><div class="track"><div class="fill" style="width:22.3%;background:#aebdd0"></div></div></div>
        <div class="metric-row">背景 + 风电<strong>0.811</strong><div class="track"><div class="fill" style="width:22.3%;background:#aebdd0"></div><div class="fill" style="width:58.8%;background:#8760c5"></div></div></div>'''
        if stage==12:right+='<div class="formula" style="margin-top:30px">0.811 − 0.223 = 0.588</div><div class="muted">风电预测带来的最大新增能力</div>'
    else:
        right='''<h2>字段风险与实际组合，一起考虑</h2><div class="metric-row">字段推断风险 M<strong>0.588</strong></div><div class="muted" style="font-size:23px;margin-top:18px">背景配合下，风电可以增加多少能力</div><div class="metric-row" style="margin-top:40px">三个字段的组合精度<strong style="color:#c63846">0.811</strong></div><div class="muted" style="font-size:23px;margin-top:18px">已经超过公众判定线 0.7</div><div class="callout">综合两点，考虑调高风电预测的等级。</div>'''
    return shell(f'''<div class="eyebrow">开场案例 · NEM 2024 · 燃气机组出力</div><h1>同样三个公开字段，两种需要考虑的风险</h1>
        <div class="subhead">左侧看组合的推断能力，右侧看一个字段在背景下增加多少能力</div>
        <div class="panel" style="left:70px;top:210px;width:730px;height:540px;padding:0">{svg}</div>
        <div class="panel" style="left:830px;top:210px;width:700px;height:540px;padding:30px 36px">{right}</div>''')


def analogy():
    return shell('''<div class="eyebrow">用一个熟悉的关系理解协同</div><h1 class="wide-title">电压 = 电流 × 电阻</h1>
      <div style="position:absolute;left:80px;right:80px;top:320px;display:flex;gap:32px">
       <div class="panel" style="position:relative;top:0;flex:1;height:290px"><h2>只知道电流</h2><div class="big" style="margin:30px 0">I × ? = ?</div><div class="muted">还不能确定电压</div></div>
       <div class="panel" style="position:relative;top:0;flex:1;height:290px"><h2>只知道电阻</h2><div class="big" style="margin:30px 0">? × R = ?</div><div class="muted">还不能确定电压</div></div>
       <div class="panel" style="position:relative;top:0;flex:1;height:290px;border-color:#9b8ac6"><h2>两者都知道</h2><div class="big" style="margin:30px 0;color:#7755b6">I × R = U</div><div class="muted">共同提供完整信息</div></div>
      </div><div class="note">这是一种帮助理解协同的类比；实际字段关系由数据上的推断模型测量。</div>''')


def solution():
    return shell('''<div class="eyebrow">系统思路</div><h1>既衡量字段风险，也处理实际存在的越线组合</h1>
      <div class="panel" style="left:75px;top:240px;width:690px;height:260px"><h2>① 重新定义字段推断风险 M</h2><div class="muted">考虑最有利的背景知识，<br>衡量一个字段最多增加多少推断能力。</div></div>
      <div class="panel" style="left:800px;top:240px;width:725px;height:260px"><h2 style="color:#c13e4d">② 识别实际存在的越线组合</h2><div class="muted">找出凑齐就越过判定线的组合，<br>在调整等级时尽可能将它们切断。</div></div>
      <div style="position:absolute;top:565px;left:200px;right:200px;text-align:center;font-size:35px;font-weight:700;color:#166f77">综合效用 → 强化学习 → 整套二次分级方案</div>''')


def summary():
    return shell('''<div class="eyebrow">7 个公开数据集 · 二次定级结果</div><h1>越线组合明显减少</h1>
      <div style="position:absolute;left:120px;right:120px;top:280px;display:flex;align-items:center;justify-content:center;gap:100px">
      <div style="text-align:center"><div style="font-size:120px;color:#ce4b55;font-weight:750">2116</div><div class="muted">一次定级后</div></div>
      <div style="font-size:82px;color:#879ab8">→</div>
      <div style="text-align:center"><div style="font-size:120px;color:#0d8b80;font-weight:750">8</div><div class="muted">二次定级后</div></div></div>
      <div class="note">NEM · PJM · IEEE 30 节点 · 社区统计 · 医疗保险 · 钢铁企业用电 · 楼宇人员在室</div>''')


def end():
    return shell('''<div class="eyebrow">作品演示</div><h1 class="wide-title" style="top:190px">面向聚合推断威胁的<br>数据定级与共享审查系统</h1><div style="position:absolute;left:78px;top:480px;color:#526d92;font-size:36px">谢谢观看</div>''')
