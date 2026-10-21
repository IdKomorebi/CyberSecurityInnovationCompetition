# -*- coding: utf-8 -*-
"""大模型复核：由另一个大语言模型逐条检查一次定级的初判，不同意时给出自己的影响对象、影响程度和理由。
复核模型在 secrets/deepseek.env 中配置：REVIEW_API_KEY、REVIEW_BASE_URL、REVIEW_MODEL；
不配置时沿用初判的接口和密钥，模型取 deepseek-reasoner。"""
import json, urllib.request, urllib.error
from first_grade import _env, RULES, model_name, _post


def config():
    c = _env()
    return dict(key=c.get("REVIEW_API_KEY") or c.get("DEEPSEEK_API_KEY"), url=c.get("REVIEW_BASE_URL") or c.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                model=c.get("REVIEW_MODEL") or "deepseek-reasoner", thinking=c.get("REVIEW_THINKING", "1") != "0")


def ask(row, cfg):
    sys_p = ("你是数据分类分级的复核员，依据国家标准《数据安全技术 数据分类分级规则》，检查另一位判定者对一个数据项的初判。"
             "影响对象只能取：" + "、".join(RULES["影响对象"]) + "；影响程度只能取：" + "、".join(RULES["影响程度"]) + "。已对外公开发布的数据影响程度取“无危害”。"
             "如果同意初判，原样给出；不同意时给出你的判断。输出 JSON：{\"同意\":true或false,\"影响对象\":\"\",\"影响程度\":\"\",\"理由\":\"不超过60字\"}")
    usr = (f"数据项：{row['中文名']}\n类别：{row.get('类别', '')}\n公开情况：{row.get('公开情况', '')}\n说明：{row.get('说明', '')}\n"
           f"在本任务中的角色：{row.get('角色', '')}\n\n初判：影响对象 {row.get('影响对象')}，影响程度 {row.get('影响程度')}，理由：{row.get('理由', '')}")
    msg = {"model": cfg["model"], "messages": [{"role": "system", "content": sys_p}, {"role": "user", "content": usr}], "response_format": {"type": "json_object"}}
    if not cfg["thinking"]:
        msg["enable_thinking"] = False                    # 只对支持该参数的接口有效（如阿里云百炼）；关掉后快得多
    body = json.dumps(msg).encode()
    r = _post(cfg["url"] + "/chat/completions", body, {"Content-Type": "application/json", "Authorization": "Bearer " + cfg["key"]})
    txt = r["choices"][0]["message"]["content"]
    return json.loads(txt[txt.find("{"):txt.rfind("}") + 1]), r["usage"]["total_tokens"], r.get("model", cfg["model"])


def review(rows, on_row=None, workers=4):
    """返回（不同意的字段列表，消耗词元，模型名）。列表项可直接写成 _复核.json。几个字段同时复核，结果按原顺序排列。"""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    cfg = config()
    if not cfg["key"]:
        raise RuntimeError("没有找到复核模型的密钥（REVIEW_API_KEY 或 DEEPSEEK_API_KEY）")
    res, tokens, model, done = {}, 0, cfg["model"], 0
    with ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(ask, r, cfg): k for k, r in enumerate(rows)}
        for f in as_completed(futs):
            k = futs[f]; r = rows[k]; a, tk, model = f.result(); tokens += tk; done += 1
            o, d = a.get("影响对象"), a.get("影响程度")
            res[k] = dict(字段=r["字段"], 影响对象=o, 影响程度=d, 理由=str(a.get("理由", ""))[:200], 来源=f"大模型复核（{model_name(model)}）") \
                if o in RULES["影响对象"] and d in RULES["影响程度"] and (o, d) != (r.get("影响对象"), r.get("影响程度")) else None
            if on_row:
                on_row(done, r, res[k])
    return [res[k] for k in sorted(res) if res[k]], tokens, model_name(model)
