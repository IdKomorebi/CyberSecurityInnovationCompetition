"""Redraw the six remaining V4 diagrams; leave reports and screenshots untouched.

Shares the palette, typography and vector primitives of draw_principles.py.
Run with the Pytorch310_codex environment. Exports editable SVG, PNG and JPG.
"""
from PIL import Image, ImageDraw, ImageFont

from draw_principles import (
    SVG, ROOT, INK, SUB, LINE, BLUE, TEAL, VIOLET, AMBER, RED, GREY,
)


PALE_BLUE = '#edf4fc'
PALE_TEAL = '#eaf6f5'
PALE_VIOLET = '#f2eef9'
PALE_RED = '#fcf0ef'
LEVELS = [BLUE, TEAL, VIOLET, AMBER]


def document(s, x, y, w=70, h=88, color=BLUE, rows=4):
    s.path(f'M{x} {y}H{x+w-17}L{x+w} {y+17}V{y+h}H{x}Z', color, 2, 'white')
    s.path(f'M{x+w-17} {y}V{y+17}H{x+w}', color, 1.5)
    for k in range(rows):
        yy = y + 30 + k * (h-44) / max(rows-1, 1)
        s.line(x+13, yy, x+w-14-(k % 2)*9, yy, color, 2)


def field(s, x, y, label, color=BLUE, r=20):
    s.circle(x, y, r, 'white', color, 2)
    s.text(x, y+7, label, 21, color, 600, 'middle')


def lock(s, x, y, color=VIOLET, scale=1):
    s.path(f'M{x-7*scale} {y}v{-6*scale}a{7*scale} {7*scale} 0 0 1 {14*scale} 0v{6*scale}', color, 2)
    s.rect(x-11*scale, y, 22*scale, 19*scale, 'white', color, 3, 2)
    s.circle(x, y+8*scale, 2*scale, color, color)
    s.line(x, y+8*scale, x, y+13*scale, color, 1.5)


def person(s, x, y, color=BLUE):
    s.circle(x, y, 11, 'white', color, 2)
    s.path(f'M{x-21} {y+38}v-10q0-14 21-14q21 0 21 14v10', color, 2)


def chip(s, x, y, label, color=VIOLET):
    s.rect(x, y, 65, 55, 'white', color, 5, 2)
    for i in range(4):
        dx = x + 12 + i*14
        s.line(dx, y-7, dx, y, color, 2)
        s.line(dx, y+55, dx, y+62, color, 2)
    for i in range(3):
        dy = y+11+i*16
        s.line(x-7, dy, x, dy, color, 2)
        s.line(x+65, dy, x+72, dy, color, 2)
    s.text(x+32.5, y+34, label, 20, color, 600, 'middle')


def database(s, x, y, color=TEAL):
    s.path(f'M{x} {y+12}v52c0 17 72 17 72 0v-52', color, 2, 'white')
    s.path(f'M{x} {y+12}c0-17 72-17 72 0s-72 17-72 0', color, 2, 'white')
    for yy in [y+32, y+51]:
        s.path(f'M{x} {yy}c0 17 72 17 72 0', color, 1.4)


def grade_row(s, x, y, values, size=35, selected=False):
    for i, v in enumerate(values):
        color = LEVELS[v-1]
        s.rect(x+i*(size+6), y, size, size,
               color if selected else 'white', color, 4, 1.5)
        s.text(x+i*(size+6)+size/2, y+size*.71, v,
               21, 'white' if selected else color, 600, 'middle')


def prediction_plot(s, x, y, w, h, legend=True):
    s.line(x, y+h, x+w+8, y+h, SUB, 1.3, arrow=True)
    s.line(x, y+h, x, y-6, SUB, 1.3, arrow=True)
    actual = [.25, .39, .31, .59, .76, .61, .72, .48, .63, .85, .74]
    pred = [.29, .34, .35, .54, .71, .64, .67, .53, .60, .79, .77]
    for values, col, dash in [(actual, BLUE, None), (pred, TEAL, '6 4')]:
        pts = [(x+8+i*(w-16)/(len(values)-1), y+h-v*h) for i, v in enumerate(values)]
        s.path('M'+'L'.join(f'{a:.1f} {b:.1f}' for a, b in pts), col, 2.7, dash=dash)
    if legend:
        s.line(x+5, y-25, x+34, y-25, BLUE, 2.5)
        s.text(x+43, y-18, '真实值', 20, BLUE)
        s.line(x+126, y-25, x+155, y-25, TEAL, 2.5, dash='5 4')
        s.text(x+164, y-18, '预测值', 20, TEAL)


def inference():
    s = SVG('fig_infer', 690, '推断验证与字段推断风险',
            '只用组合内字段训练独立推断模型，在未参与训练的数据上验证。多随机种子平均并取单调闭包后，形成推断精度表，分别用于字段风险与越线组合分析。曲线为示意，表内数值来自 NEM 示例。')
    s.heading(25, 38, '1', '只提供组合内字段')
    s.heading(351, 38, '2', '独立训练推断模型')
    s.heading(690, 38, '3', '在未见数据上验证', TEAL)
    s.text(38, 84, '组合 S = {a, c, e}', 23, BLUE, 600)
    for j, label in enumerate(['a', 'b', 'c', 'd', 'e']):
        s.text(58+j*36, 118, label, 20, BLUE if j in [0, 2, 4] else GREY, 600, 'middle')
    s.text(269, 118, 'y', 22, AMBER, 600, 'middle')
    s.matrix(43, 132, 8, 5, 36, 15, BLUE, [0, 2, 4])
    s.matrix(257, 132, 8, 1, 27, 15, AMBER)
    s.text(43, 276, '训练数据 80%', 21, BLUE, 600)
    s.matrix(43, 296, 2, 5, 36, 15, TEAL, [0, 2, 4])
    s.matrix(257, 296, 2, 1, 27, 15, AMBER)
    s.text(43, 359, '留出数据 20%', 21, TEAL, 600)
    s.line(300, 174, 349, 174, BLUE, 2.5, arrow=True)
    s.network(372, 174, (3, 5, 3, 1), 69, 27, BLUE, 7)
    s.text(475, 87, '每个组合各自学习参数', 21, SUB, 400, 'middle')
    s.text(476, 266, '训练得到 fₛ', 25, BLUE, 600, 'middle')
    s.text(476, 303, '不接收组合外的字段', 21, SUB, 400, 'middle')
    s.line(598, 174, 691, 174, BLUE, 2.5, arrow=True)
    s.path('M300 318H657V210H691', TEAL, 2, arrow=True)
    s.text(479, 359, '留出行仅用于验证', 21, TEAL, 500, 'middle')
    prediction_plot(s, 716, 117, 240, 129)
    s.text(837, 281, '预测曲线示意', 19, SUB, 400, 'middle')
    s.text(837, 325, 'V(S)', 32, TEAL, 700, 'middle')
    s.text(837, 360, '留出 R²，负值取 0', 21, SUB, 400, 'middle')
    s.line(25, 389, 975, 389, LINE, 1.5)
    s.heading(25, 430, '4', '形成统一的推断精度表', VIOLET)
    s.heading(549, 430, '5', '支撑两部分风险', TEAL)
    s.text(47, 475, '组合（NEM 示例）', 21, SUB, 600)
    s.text(425, 475, 'V(S)', 21, SUB, 600, 'end')
    s.line(43, 488, 439, 488, LINE, 1.5)
    for yy, label, val in [(524, '风电', '0.183'), (566, '风电 + 容量', '0.478'), (608, '风电 + 容量 + 光伏', '0.811')]:
        s.text(47, yy, label, 22, INK)
        s.text(425, yy, val, 24, RED if val == '0.811' else BLUE, 600, 'end')
    s.path('M461 551H510V500H563M510 551V593H563', VIOLET, 2, arrow=True)
    s.line(510, 500, 563, 500, VIOLET, 2, arrow=True)
    field(s, 592, 500, 'i', VIOLET)
    s.text(630, 495, '字段推断风险 M', 25, VIOLET, 700)
    s.text(630, 529, '取背景下最大的新增能力', 21, SUB)
    for xx, yy in [(583, 586), (603, 586), (593, 606)]:
        s.circle(xx, yy, 11, 'white', RED, 1.7)
    s.text(630, 588, '最小越线组合', 25, RED, 700)
    s.text(630, 622, '越线，去掉任一字段即不过线', 21, SUB)
    s.text(43, 666, '统一口径：多随机种子取平均，再取单调闭包；快速估计用于筛选，重新训练用于确认。', 20, SUB)
    s.save()


def regrade():
    s = SVG('fig_regrade', 715, '二次定级的三个步骤',
            '第一步，M 不低于 0.7 的字段以目标等级为等级下限；第二步，强化学习依据包含字段风险、共享成本、越线组合的综合效用学习整套等级；第三步，合并接收方可获取的全部字段重新验证和调整。示意等级不代表实验结果。')
    s.heading(25, 39, '1', '直接定级：确定等级下限', BLUE)
    s.text(954, 38, '等级示意：保护对象为 3 级', 20, SUB, 400, 'end')
    s.text(63, 106, 'M ≥ 0.7', 34, BLUE, 700)
    s.text(63, 145, '调至保护对象等级', 23, INK, 600)
    s.line(299, 113, 374, 113, BLUE, 2.5, arrow=True)
    s.text(403, 78, '后续允许的等级', 21, SUB)
    for j in range(4):
        x = 407+j*60
        s.rect(x, 96, 47, 47, 'url(#hatch)' if j < 2 else ('#f2eef9' if j == 2 else 'white'), LINE if j < 2 else VIOLET, 5, 2)
        s.text(x+23.5, 127, j+1, 26, GREY if j < 2 else VIOLET, 600, 'middle')
    lock(s, 550, 159, VIOLET, .75)
    s.text(579, 170, '下限', 20, VIOLET, 600)
    s.line(659, 118, 708, 118, BLUE, 2, arrow=True)
    s.text(747, 113, 'aᵢ ≥ aᵢᵐⁱⁿ', 29, VIOLET, 600)
    s.text(747, 151, '只升不降', 23, SUB)
    s.text(62, 207, '一次等级更高时保留；涉及多个保护对象时，取最高的等级下限。', 21, SUB)
    s.line(25, 219, 975, 219, LINE, 1.5)
    s.heading(25, 258, '2', '联合评估：学习整套等级', VIOLET)
    s.text(954, 257, '强化学习细节见图 2-10', 20, SUB, 400, 'end')
    s.text(64, 304, '候选等级方案', 22, INK, 600)
    for i, vals in enumerate([[1, 3, 2, 1, 2], [2, 3, 2, 1, 3], [2, 4, 3, 2, 3]]):
        s.text(42, 340+i*43, 'ABC'[i], 21, SUB, 400, 'middle')
        grade_row(s, 64, 316+i*43, vals, 33, i == 1)
    s.line(281, 374, 338, 374, VIOLET, 2.5, arrow=True)
    s.text(369, 310, '综合效用 U(a)', 25, VIOLET, 700)
    for i, (label, color) in enumerate([('字段风险', BLUE), ('共享成本', AMBER), ('越线组合惩罚', RED)]):
        yy = 348 + i*36
        s.line(371, yy-7, 391, yy-7, color, 4)
        s.text(407, yy, label, 22, color, 500)
    s.line(592, 374, 662, 374, VIOLET, 2.5, arrow=True)
    s.text(703, 320, '效用更高的整套方案', 23, TEAL, 700)
    grade_row(s, 706, 346, [2, 3, 2, 1, 3], 40, True)
    s.text(706, 420, '同时权衡所有字段与组合', 21, SUB)
    s.path('M820 441V465H164V445', VIOLET, 1.8, arrow=True)
    s.rect(298, 451, 417, 28, 'white')
    s.text(506, 472, '效用反馈 → 强化学习反复改进', 21, VIOLET, 500, 'middle')
    s.line(25, 493, 975, 493, LINE, 1.5)
    s.heading(25, 531, '3', '整体核对：合并全部可见字段，再次验证', TEAL)
    s.text(954, 531, '核对细节见图 2-11', 20, SUB, 400, 'end')
    person(s, 65, 586, TEAL)
    for xx, yy, label in [(133, 579, 'a'), (183, 579, 'b'), (233, 579, 'c'), (133, 625, 'd'), (183, 625, 'e'), (233, 625, 'f')]:
        field(s, xx, yy, label, TEAL, 16)
    s.line(273, 604, 341, 604, TEAL, 2.5, arrow=True)
    s.text(379, 591, '重新训练并比较判定线', 24, TEAL, 700)
    s.text(379, 628, '仍有风险时，调整等级并复核', 21, SUB)
    s.line(696, 604, 747, 604, TEAL, 2.5, arrow=True)
    document(s, 780, 567, 54, 69, TEAL, 3)
    s.text(859, 594, '最终等级', 23, TEAL, 700)
    s.text(859, 629, '复核结果', 23, TEAL, 700)
    s.rect(25, 670, 950, 32, '#f5f8fb', rx=3)
    s.text(500, 693, '默认模式：权衡共享成本与风险。严格模式：继续调整至不再越线。', 21, INK, 400, 'middle')
    s.save()


def route():
    s = SVG('fig_route', 635, '技术路线：从字段风险到整套等级',
            '三个阶段依次为字段本身、聚合推断风险、定级与效果。一次等级与单独推断为起点；字段推断风险 M 和最小越线组合共同进入二次定级；通过整体核对与效果复核得到等级和风险变化。推断精度是贯穿三个阶段的共同尺度。图中条形及等级为示意。')
    s.heading(25, 39, '1', '字段本身', BLUE)
    s.heading(353, 39, '2', '聚合推断风险', VIOLET)
    s.heading(682, 39, '3', '定级与效果', TEAL)
    s.line(328, 70, 328, 529, LINE, 1, dash='3 6')
    s.line(657, 70, 657, 529, LINE, 1, dash='3 6')
    s.text(42, 89, '一次定级', 24, BLUE, 700)
    document(s, 49, 111, 66, 82, BLUE)
    s.text(83, 224, '字段目录', 21, SUB, 400, 'middle')
    s.line(131, 155, 172, 155, BLUE, 2, arrow=True)
    for j in range(4):
        s.rect(185+j*27, 191-(j+1)*19, 20, (j+1)*19, LEVELS[j], rx=2)
        s.text(195+j*27, 216, j+1, 19, LEVELS[j], 600, 'middle')
    s.text(239, 248, '一次等级 Lᵢ', 22, BLUE, 600, 'middle')
    s.text(42, 300, '单独推断', 24, BLUE, 700)
    field(s, 67, 348, 'i', BLUE, 23)
    s.line(100, 348, 143, 348, BLUE, 2, arrow=True)
    s.network(158, 348, (2, 3, 1), 45, 23, BLUE, 5)
    s.text(167, 415, 'V({i})', 31, BLUE, 700, 'middle')
    s.text(167, 454, '单个字段能推断多少', 22, SUB, 400, 'middle')
    s.text(167, 502, '确定起点：等级与单独能力', 20, SUB, 400, 'middle')
    s.line(298, 275, 355, 275, SUB, 2.3, arrow=True)
    s.text(370, 89, '字段推断风险 M', 24, VIOLET, 700)
    for xx, yy, lab in [(398, 145, 'a'), (440, 145, 'b'), (419, 188, 'c')]:
        field(s, xx, yy, lab, GREY, 16)
    s.text(477, 174, '+', 30, VIOLET, 600, 'middle')
    field(s, 528, 168, 'i', VIOLET, 23)
    s.line(565, 168, 606, 168, VIOLET, 2, arrow=True)
    s.text(620, 178, 'M', 29, VIOLET, 700, 'middle')
    s.text(496, 224, '在最有利背景下', 22, SUB, 400, 'middle')
    s.text(496, 255, '这个字段最多增加多少能力', 21, SUB, 400, 'middle')
    s.text(370, 300, '最小越线组合', 24, RED, 700)
    s.path('M401 336Q494 295 586 336L555 406Q495 435 434 406Z', '#e5b7b5', 1.6, PALE_RED)
    for xx, yy, lab in [(433, 354, 'a'), (554, 354, 'b'), (494, 399, 'c')]:
        field(s, xx, yy, lab, RED, 19)
    s.text(495, 454, 'V(S) > θ', 29, RED, 600, 'middle')
    s.text(495, 502, '哪些字段不能同时开放', 22, SUB, 400, 'middle')
    s.line(628, 275, 685, 275, SUB, 2.3, arrow=True)
    s.text(698, 89, '二次定级', 24, TEAL, 700)
    grade_row(s, 710, 119, [1, 2, 2, 1, 3], 39)
    s.line(825, 171, 825, 208, TEAL, 2, arrow=True)
    s.text(825, 243, '综合效用 + 强化学习', 22, TEAL, 600, 'middle')
    s.text(825, 278, '联合调整整套等级', 22, SUB, 400, 'middle')
    s.text(698, 324, '整体核对与效果复核', 24, TEAL, 700)
    s.text(709, 365, '调整前', 20, SUB)
    s.line(797, 359, 941, 359, '#bf7c79', 14)
    s.text(709, 407, '调整后', 20, SUB)
    s.line(797, 401, 851, 401, TEAL, 14)
    s.text(825, 454, '比较整体推断能力的变化', 21, SUB, 400, 'middle')
    s.text(825, 502, '输出等级、依据与复核结果', 20, SUB, 400, 'middle')
    s.line(25, 543, 975, 543, LINE, 1.5)
    s.text(45, 585, '统一尺度', 23, INK, 700)
    s.text(181, 585, '推断精度 V(S)', 26, BLUE, 700)
    s.line(384, 578, 436, 578, BLUE, 2, arrow=True)
    s.text(457, 585, '只用组合 S 训练模型，在留出数据上验证', 23, SUB)
    s.text(45, 620, '输入：数据表、字段目录、保护对象与共享规则。图中等级与条形长度仅作流程示意。', 19, SUB)
    s.save()


def architecture():
    s = SVG('fig_arch', 704, '系统架构：界面、服务、计算与资源',
            '浏览器中的三组操作通过接口连接任务与后台作业。流水线调度定级引擎与推断引擎，依托大语言模型、规则库、数据和 CPU 或 GPU 运行。')
    layers = [(BLUE, 99, '界面层'), (VIOLET, 270, '服务层'), (TEAL, 438, '计算层'), (AMBER, 610, '资源层')]
    for color, y, title in layers:
        s.line(38, y-35, 38, y+43, color, 5)
        s.text(60, y+13, title, 26, color, 700)
    # A browser window is the only enclosing frame: its interior is actual navigation.
    s.rect(202, 30, 754, 133, 'white', BLUE, 8, 1.8)
    s.line(203, 57, 955, 57, LINE, 1.5)
    for x in [220, 234, 248]:
        s.circle(x, 44, 3, LINE, LINE)
    s.text(577, 49, '浏览器', 19, SUB, 400, 'middle')
    for x, title, detail, col in [(326, '字段本身', '一次定级 · 单独推断', BLUE), (578, '聚合推断风险', '字段推断风险 · 越线组合', VIOLET), (830, '定级与效果', '二次定级 · 效果复核', TEAL)]:
        s.line(x-90, 77, x+90, 77, col, 3)
        s.text(x, 109, title, 25, col, 600, 'middle')
        s.text(x, 143, detail, 20, SUB, 400, 'middle')
    s.line(557, 172, 557, 211, SUB, 1.8, arrow=True)
    s.line(596, 211, 596, 172, SUB, 1.8, arrow=True)
    s.text(627, 199, '请求 / 结果', 20, SUB)
    # Endpoints, a job queue, and a device selector.
    for yy in [244, 265, 286]:
        s.circle(249, yy, 5, 'white', VIOLET, 1.6)
        s.line(257, yy, 281, yy, VIOLET, 1.8)
    s.path('M283 244H298V286H283', VIOLET, 1.8)
    s.line(298, 265, 323, 265, VIOLET, 1.8, arrow=True)
    s.text(343, 260, '任务接口', 24, VIOLET, 700)
    s.text(343, 295, '查询 · 配置 · 触发', 20, SUB)
    for k in range(3):
        s.rect(560+k*7, 237+k*12, 65, 20, 'white', VIOLET, 3, 1.5)
    s.text(651, 260, '作业管理', 24, VIOLET, 700)
    s.text(651, 295, '后台运行 · 进度', 20, SUB)
    s.line(843, 241, 875, 241, VIOLET, 2)
    s.circle(865, 241, 5, 'white', VIOLET, 2)
    s.line(843, 263, 875, 263, VIOLET, 2)
    s.circle(851, 263, 5, 'white', VIOLET, 2)
    s.text(908, 263, '设备', 23, VIOLET, 700, 'middle')
    s.text(895, 295, '自动选择', 20, SUB, 400, 'middle')
    s.line(203, 325, 956, 325, LINE, 1.5)
    s.line(577, 336, 577, 367, SUB, 1.8, arrow=True)
    s.text(625, 358, '调度计算', 20, SUB)
    # A small pipeline, an explicit grading matrix, and a neural network.
    s.text(322, 398, '流水线', 24, TEAL, 700, 'middle')
    for i in range(4):
        x = 241+i*53
        s.circle(x, 436, 12, 'white', TEAL, 2)
        s.text(x, 442, i+1, 17, TEAL, 600, 'middle')
        if i < 3:
            s.line(x+15, 436, x+36, 436, TEAL, 1.7, arrow=True)
    s.text(322, 499, '组织各阶段的执行', 20, SUB, 400, 'middle')
    s.text(580, 398, '定级引擎', 24, TEAL, 700, 'middle')
    for r in range(2):
        grade_row(s, 500, 420+r*29, [1+r, 2, 3, 4], 23)
    s.text(580, 499, '规则定级 · 强化学习', 20, SUB, 400, 'middle')
    s.text(838, 398, '推断引擎', 24, TEAL, 700, 'middle')
    s.network(757, 440, (3, 4, 3, 1), 52, 16, TEAL, 4.5)
    s.text(838, 499, '训练 · 估计 · 验证', 20, SUB, 400, 'middle')
    s.line(203, 513, 956, 513, LINE, 1.5)
    s.line(577, 524, 577, 553, SUB, 1.8, arrow=True)
    s.text(625, 547, '调用资源', 20, SUB)
    s.path('M230 572H295Q303 572 303 580V614Q303 622 295 622H259L242 638V622H230Q222 622 222 614V580Q222 572 230 572Z', AMBER, 2, 'white')
    for xx in [244, 263, 282]:
        s.circle(xx, 597, 3.5, AMBER, AMBER)
    s.text(263, 675, '大语言模型', 22, INK, 600, 'middle')
    document(s, 428, 569, 62, 74, AMBER)
    s.text(459, 675, '规则库', 22, INK, 600, 'middle')
    database(s, 621, 571, AMBER)
    s.text(657, 675, '数据', 22, INK, 600, 'middle')
    chip(s, 818, 576, '算力', AMBER)
    s.text(851, 675, 'CPU / GPU', 22, INK, 600, 'middle')
    s.save()


def first_grade():
    s = SVG('fig_grade1', 650, '一次定级：检索、判断、查表与复核',
            '字段目录结合规则库检索条文，大模型给出影响对象、影响程度及依据；按判定表和最低参考级别计算等级；人工确认或参考第二模型意见，保留初判和复核依据。判定矩阵中的色块仅表示查表过程。')
    s.heading(25, 38, '1', '检索相关条文', BLUE)
    s.heading(353, 38, '2', '大模型判断', VIOLET)
    s.heading(700, 38, '3', '查表并校正', TEAL)
    document(s, 47, 94, 67, 85, BLUE)
    s.text(80, 211, '字段目录', 21, BLUE, 500, 'middle')
    for k in range(3):
        document(s, 206+k*7, 94-k*6, 59, 79, GREY, 3)
    s.text(244, 211, '规则库', 21, SUB, 500, 'middle')
    s.path('M81 225V247H244V225', BLUE, 1.6)
    s.line(162, 247, 162, 268, BLUE, 1.8, arrow=True)
    s.text(163, 303, '相关条文 + 必选判定表', 22, BLUE, 600, 'middle')
    s.line(304, 155, 354, 155, BLUE, 2.3, arrow=True)
    s.network(377, 149, (3, 4, 3, 1), 67, 25, VIOLET, 7)
    for xx, label in [(421, '影响对象'), (576, '影响程度')]:
        s.line(xx-55, 218, xx+55, 218, VIOLET, 3)
        s.text(xx, 253, label, 24, VIOLET, 600, 'middle')
    s.text(499, 303, '同时给出条文编号与理由', 21, SUB, 400, 'middle')
    s.line(636, 155, 690, 155, VIOLET, 2.3, arrow=True)
    s.text(833, 83, '影响对象 × 影响程度', 22, TEAL, 500, 'middle')
    # An unnumbered lookup matrix avoids inventing statutory grade assignments.
    for r in range(4):
        for c in range(4):
            x, y = 740+c*42, 105+r*30
            s.rect(x, y, 36, 24, ['#eef5fb', '#dcecf4', '#bfdae7', '#83b9cb'][min(3, (r+c)//2)], rx=2)
    s.rect(821, 162, 42, 30, 'none', TEAL, 3, 2.5)
    s.line(708, 177, 817, 177, TEAL, 1.3, dash='4 3')
    s.line(842, 96, 842, 158, TEAL, 1.3, dash='4 3')
    s.text(834, 255, '查表得到等级', 23, TEAL, 600, 'middle')
    s.text(834, 303, '满足适用的最低参考级别', 21, SUB, 400, 'middle')
    s.line(25, 332, 975, 332, LINE, 1.5)
    s.line(834, 320, 834, 363, TEAL, 2.2, arrow=True)
    s.heading(510, 399, '4', '人工复核并确认', TEAL)
    s.text(42, 399, '输出：一次等级与依据', 25, BLUE, 700)
    person(s, 572, 449, TEAL)
    s.text(572, 521, '人工确认', 22, TEAL, 600, 'middle')
    s.path('M670 460H727', GREY, 1.6, arrow=True)
    chip(s, 758, 437, '模型', VIOLET)
    s.text(791, 521, '第二模型提供建议', 21, SUB, 400, 'middle')
    # The suggestion flows back to the human, who controls adoption.
    s.line(744, 475, 626, 475, VIOLET, 1.6, arrow=True)
    s.text(697, 563, '修改影响对象 / 程度后，重新查表', 21, SUB, 400, 'middle')
    s.path('M930 541H960V351H907V319', TEAL, 1.7, dash='5 4', arrow=True)
    s.line(488, 478, 435, 478, TEAL, 2.3, arrow=True)
    s.text(60, 447, '字段', 21, SUB, 600)
    s.text(182, 447, '等级', 21, SUB, 600)
    s.text(290, 447, '依据', 21, SUB, 600)
    s.line(48, 460, 411, 460, LINE, 1.5)
    for i, label in enumerate(['a', 'b', 'c']):
        yy = 495+i*39
        s.text(79, yy, label, 23, BLUE, 600, 'middle')
        s.text(203, yy, ['L₁', 'L₂', 'L₃'][i], 23, BLUE, 600, 'middle')
        s.line(289, yy-6, 385, yy-6, LINE, 3)
    s.line(25, 594, 975, 594, LINE, 1.5)
    s.text(500, 632, '等级由判定表与参考下限计算；初判、复核意见、修改来源与理由均保留。', 22, INK, 400, 'middle')
    s.save()


def theory():
    s = SVG('fig_theory', 850, '字段推断风险与越线组合的关系',
            '上半图以 NEM 风电预测示例区分字段 M 与实际越线组合。中部用三条关系说明二者一致：成员 M 之和约束组合精度；关键字段等价于属于最小越线组合；组合的不可约增益不超过任何成员在相应预算下的 M。下部说明二者在定级中承担不同作用。')
    s.heading(25, 38, '1', '字段层面：最有利背景下的增益', VIOLET)
    s.heading(528, 38, '2', '集合层面：实际越线组合', RED)
    s.line(505, 64, 505, 339, LINE, 1, dash='3 6')
    s.text(40, 82, '在允许的背景中，取最大新增能力', 22, SUB)
    x0, scale = 157, 367
    s.text(40, 126, '风电单独', 21, BLUE, 600)
    s.rect(x0, 107, .183*scale, 26, BLUE, rx=3)
    s.text(x0+.183*scale+14, 128, '0.183', 23, BLUE, 600)
    s.text(40, 186, '背景', 21, GREY, 600)
    s.rect(x0, 167, .223*scale, 26, '#a6b4c5', rx=3)
    s.text(x0+.223*scale+14, 188, '0.223', 23, SUB, 600)
    s.text(40, 246, '背景+风电', 20, VIOLET, 600)
    s.rect(x0, 227, .223*scale, 26, '#a6b4c5', rx=2)
    s.rect(x0+.223*scale+2, 227, .588*scale-2, 26, VIOLET, rx=2)
    s.path(f'M{x0+.223*scale} 268v8h{.588*scale}v-8', VIOLET, 1.8)
    s.text(x0+(.223+.588/2)*scale, 303, 'M = 0.588', 26, VIOLET, 700, 'middle')
    s.text(40, 337, '背景：可用容量 + 光伏预测；K = 3。', 20, SUB)
    s.text(547, 82, '接收方可获取字段，但无权获取目标', 21, SUB)
    for xx, label in [(606, '风电'), (754, '容量'), (902, '光伏')]:
        field(s, xx, 131, label, RED, 29)
        s.line(xx, 162, 754, 214, '#d5a3a1', 1.6)
    s.text(754, 244, 'V(S) = 0.811', 29, RED, 700, 'middle')
    start, span, yy = 565, 371, 289
    s.rect(start, yy, span, 15, '#f0f3f7', rx=3)
    s.rect(start, yy, .811*span, 15, RED, rx=3)
    s.line(start+.7*span, yy-16, start+.7*span, yy+24, INK, 1.8, dash='4 3')
    s.text(start, 337, '已超过公众判定线 0.7', 22, RED, 600)
    s.line(25, 359, 975, 359, LINE, 1.5)
    s.text(37, 391, '共同前提：V 单调，V(∅) = 0。前两条关系限定组合规模 ≤ K + 1。', 21, SUB)
    # Three compact visual proofs: a bound, a threshold crossing, and an increment.
    s.text(37, 434, '① 总量约束', 22, BLUE, 700)
    for i, width in enumerate([67, 87, 74]):
        s.rect(40+sum([67, 87, 74][:i]), 449, width-3, 12, [BLUE, TEAL, VIOLET][i], rx=2)
    s.rect(40, 474, 174, 12, '#9fb4ce', rx=2)
    s.text(292, 460, 'ΣM', 20, SUB)
    s.text(292, 487, 'V', 20, SUB)
    s.text(376, 445, 'V(A) ≤ Σᵢ∈A Mᵢ⁽ᴷ⁾', 28, BLUE, 600)
    s.text(376, 483, '成员风险之和，为组合推断能力提供上界。', 22, SUB)
    s.line(37, 505, 960, 505, LINE, 1)
    s.text(37, 543, '② 关键字段', 22, VIOLET, 700)
    s.line(43, 578, 307, 578, LINE, 5)
    s.line(43, 578, 174, 578, GREY, 9)
    s.line(174, 578, 281, 578, VIOLET, 9)
    s.line(222, 558, 222, 596, RED, 1.8, dash='4 3')
    s.text(222, 620, 'θ', 22, RED, 500, 'middle')
    s.text(376, 554, '关键字段 ⇔ 属于某个最小越线组合', 25, VIOLET, 600)
    s.text(376, 592, '加入该字段，能让一个未越线背景越过判定线。', 22, SUB)
    s.line(37, 637, 960, 637, LINE, 1)
    s.text(37, 675, '③ 协同增益', 22, TEAL, 700)
    s.rect(43, 693, 159, 13, '#b8c4d1', rx=2)
    s.rect(204, 693, 90, 13, TEAL, rx=2)
    s.path('M204 717v8h90v-8', TEAL, 1.5)
    s.text(249, 754, '不可约增益', 19, TEAL, 500, 'middle')
    s.text(376, 687, 'V(E) − max V(E′) ≤ minⱼ Mⱼ⁽|ᴱ|⁻¹⁾', 24, TEAL, 600)
    s.text(376, 725, 'E′ 为真子集，|E| ≥ 2；强协同需要每个成员的 M 足够大。', 20, SUB)
    s.line(25, 774, 975, 774, LINE, 1.5)
    s.text(40, 815, '字段 M → 等级下限与安全收益', 23, VIOLET, 700)
    s.text(541, 815, '越线组合 → 聚合推断惩罚', 23, RED, 700)
    s.save()


def preview():
    names = [
        ('fig_route', '图 2-1  技术路线'),
        ('fig_arch', '图 2-2  系统架构'),
        ('fig_grade1', '图 2-3  一次定级流程'),
        ('fig_infer', '图 2-4  推断验证'),
        ('fig_theory', '图 2-8  两个层面的关系'),
        ('fig_regrade', '图 2-9  二次定级三步'),
    ]
    # At 1000 px per diagram this is also an A4-width legibility proof at ~160 dpi.
    cell_w, cell_h = 1050, 920
    sheet = Image.new('RGB', (cell_w*2, cell_h*3), '#eaf0f5')
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 27, index=2)
    for i, (name, caption) in enumerate(names):
        x, y = (i % 2)*cell_w+25, (i//2)*cell_h
        d.text((x, y+18), caption, font=font, fill=INK)
        im = Image.open(ROOT/'img'/f'{name}.png').convert('RGB')
        im.thumbnail((1000, 850), Image.Resampling.LANCZOS)
        sheet.paste(im, (x+(1000-im.width)//2, y+65))
    dest = ROOT/'previews'/'六张原理图重绘总览.png'
    dest.parent.mkdir(exist_ok=True)
    sheet.save(dest)
    print(dest.name)


if __name__ == '__main__':
    (ROOT/'img'/'svg').mkdir(exist_ok=True)
    inference()
    regrade()
    route()
    architecture()
    first_grade()
    theory()
    preview()
