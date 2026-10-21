# -*- coding: utf-8 -*-
"""字段目录草稿：把上传数据表每一列的列名、类型和示例值交给大语言模型，起草中文名、说明、类别、公开情况，
并建议哪些列可能是需要保护的数据。草稿只是建议，公开情况和保护对象由用户在界面上确认。"""
import json, urllib.request
from first_grade import _env, model_name, _post

CATS = ("行业数据", "个人信息", "公共数据", "组织数据")
OPEN = ("已公开", "有条件开放", "未公开")
ROLES = ("候选字段", "保护对象", "不参与")


def _ask(cols, title, note, cfg):
    sys_p = ("你是数据治理助手。用户上传了一张数据表，下面给出每一列的列名、类型和示例值。请为每一列起草字段目录：中文名（简短）、说明（不超过40字）、"
             "类别（只能取：" + "、".join(CATS) + "）、公开情况（只能取：" + "、".join(OPEN) + "，看不出时取“未公开”）、"
             "建议角色（只能取：" + "、".join(ROLES) + "。保护对象指不应被无权者获取、需要防止被其他字段推断出来的数据；编号、姓名、自由文本等对推断没有意义的列取“不参与”）、"
             "理由（不超过30字）。另外判断整张表的行是否按时间顺序排列。"
             "输出 JSON：{\"时间序列\":true或false,\"字段\":[{\"字段\":\"原列名\",\"中文名\":\"\",\"说明\":\"\",\"类别\":\"\",\"公开情况\":\"\",\"建议角色\":\"\",\"理由\":\"\"}]}")
    usr = f"数据表名称：{title}\n用户说明：{note or '无'}\n\n各列：\n" + "\n".join(
        f"- {c['字段']}（{c['类型']}；示例：{'，'.join(c['示例'])}" + (f"；范围 {c['最小']} 至 {c['最大']}" if "最小" in c else "") + "）" for c in cols)
    body = json.dumps({"model": cfg.get("DEEPSEEK_MODEL", "deepseek-chat"), "temperature": 0, "response_format": {"type": "json_object"},
                       "messages": [{"role": "system", "content": sys_p}, {"role": "user", "content": usr}]}).encode()
    r = _post(cfg.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com") + "/chat/completions", body,
              {"Content-Type": "application/json", "Authorization": "Bearer " + cfg["DEEPSEEK_API_KEY"]})
    return json.loads(r["choices"][0]["message"]["content"]), r["usage"]["total_tokens"], r.get("model", "")


def draft(profile, title, note="", batch=30):
    """返回（草稿列表，是否时间序列，消耗词元，模型名）。列多时分批询问。"""
    cfg = _env(); out, ts, tokens, model = {}, [], 0, ""
    if not cfg.get("DEEPSEEK_API_KEY"):
        raise RuntimeError("没有找到大语言模型密钥（secrets/deepseek.env 中的 DEEPSEEK_API_KEY）")
    for lo in range(0, len(profile), batch):
        ans, tk, model = _ask(profile[lo:lo + batch], title, note, cfg); tokens += tk; ts.append(bool(ans.get("时间序列")))
        out.update({str(x.get("字段")): x for x in ans.get("字段", [])})
    rows = []
    for c in profile:
        x = out.get(c["字段"], {})
        rows.append(dict(字段=c["字段"], 类型=c["类型"], 中文名=x.get("中文名") or c["字段"], 说明=x.get("说明", ""),
                         类别=x.get("类别") if x.get("类别") in CATS else "行业数据", 公开情况=x.get("公开情况") if x.get("公开情况") in OPEN else "未公开",
                         建议角色="不参与" if c["类型"] in ("时间", "文本") else x.get("建议角色") if x.get("建议角色") in ROLES else "候选字段", 理由=x.get("理由", "")))
    return rows, (sum(ts) * 2 > len(ts)), tokens, model_name(model)
