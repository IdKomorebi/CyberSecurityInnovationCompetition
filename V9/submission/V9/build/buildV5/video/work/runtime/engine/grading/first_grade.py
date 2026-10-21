# -*- coding: utf-8 -*-
"""一次定级：检索国标条文 → 大语言模型判断影响对象与影响程度 → 查判定表得到等级。

用法：python first_grade.py <字段目录.csv> [--force]
结果写到同目录的 <名称>_一次定级.json；已有结果的字段不重复调用模型。
密钥从环境变量或项目根目录 secrets/deepseek.env 读取，不写在代码里。
"""
import os, sys, json, csv, urllib.request, urllib.error
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RULES = json.load(open(os.path.join(ROOT, "data", "rules", "gbt43697.json"), encoding="utf-8"))


def _env():
    cfg = {k: os.environ[k] for k in ("DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL") if k in os.environ}
    p = os.path.join(ROOT, "secrets", "deepseek.env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if "=" in line:
                k, v = line.strip().split("=", 1); cfg.setdefault(k, v)
    return cfg


_DIRECT = [False]                                       # 当前用哪种连接方式；经代理不通时改为直连并记住


def _post(url, body, headers, tries=6):
    """发请求：有的代理转发不了某些接口（例如本机代理转发阿里云百炼时握手失败），失败时换另一种连接方式重试。
    每次都新建请求对象：经代理发送时 urllib 会改写请求对象本身，复用会让直连也跟着出错。"""
    import time
    for k in range(tries):
        direct = _DIRECT[0]
        op = urllib.request.build_opener(urllib.request.ProxyHandler({})) if direct else urllib.request.build_opener()
        try:
            return json.load(op.open(urllib.request.Request(url, data=body, headers=headers), timeout=240))
        except urllib.error.HTTPError:
            raise
        except Exception:
            if k == tries - 1:
                raise
            if _DIRECT[0] == direct:
                _DIRECT[0] = not direct
            time.sleep(min(1 + k, 4))


def model_name(m):
    """界面与结果中显示的模型名：DeepSeek 接口返回的内部名（如 deepseek-flash）统一显示为产品名。"""
    return "DeepSeek-V4.1-Flash" if str(m).lower().startswith("deepseek") else m


def retrieve(text, k=4):
    """检索：按字符二元组重合度，从规则库里取最相关的 k 条条文。"""
    grams = lambda s: {s[i:i + 2] for i in range(len(s) - 1)}
    q = grams(text)
    scored = sorted(RULES["条文"], key=lambda c: -len(q & grams(c["标题"] + c["内容"])) / (len(grams(c["内容"])) ** 0.5 + 1))
    must = [c for c in RULES["条文"] if c["编号"] in ("6.5 表1",)]
    out = must + [c for c in scored if c not in must]
    return out[:k]


def kind_of(field, ans):
    """适用哪一条最低参考级别：个人信息看模型判断的类型；公共数据看开放情况。"""
    ks = [ans.get("个人信息类型", "")] if field.get("类别") == "个人信息" else []
    if field.get("类别") == "公共数据":
        ks.append({"有条件开放": "有条件开放的公共数据", "未公开": "禁止开放的公共数据"}.get(field.get("公开情况"), ""))
    return [k for k in ks if k in RULES["最低参考级别"]]


def level_of(obj, deg, kind):
    """查判定表；个人信息、公共数据再按最低参考级别抬高。"""
    t = RULES["判定表"]
    lv = t["无危害"] if deg == "无危害" or obj not in t else t[obj].get(deg, 1)
    return max([lv] + [RULES["最低参考级别"][k] for k in (kind if isinstance(kind, list) else [kind]) if k in RULES["最低参考级别"]])


def ask(field, cfg):
    clauses = retrieve(field["中文名"] + field["说明"] + field["类别"])
    sys_p = ("你是数据分类分级助手，依据国家标准《数据安全技术 数据分类分级规则》判断。只做两件事：判断该数据一旦泄露，"
             "最主要的影响对象和影响程度。影响对象只能取：" + "、".join(RULES["影响对象"]) + "；影响程度只能取：" + "、".join(RULES["影响程度"]) +
             "。已经对外公开发布（公开情况为“已公开”）的数据，影响程度取“无危害”。若属于个人信息，另外判断它是“敏感个人信息”还是“一般个人信息”，否则填“无”。"
             "输出 JSON：{\"影响对象\":\"\",\"影响程度\":\"\",\"个人信息类型\":\"\",\"依据条文\":[\"编号\"],\"理由\":\"不超过60字\"}")
    usr = "可参考的条文：\n" + "\n".join(f"[{c['编号']}] {c['标题']}：{c['内容']}" for c in clauses) + \
          f"\n\n待判断的数据：{field['中文名']}\n类别：{field['类别']}\n公开情况：{field['公开情况']}\n说明：{field['说明']}"
    body = json.dumps({"model": cfg.get("DEEPSEEK_MODEL", "deepseek-chat"), "temperature": 0, "response_format": {"type": "json_object"},
                       "messages": [{"role": "system", "content": sys_p}, {"role": "user", "content": usr}]}).encode()
    r = _post(cfg.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com") + "/chat/completions", body,
              {"Content-Type": "application/json", "Authorization": "Bearer " + cfg["DEEPSEEK_API_KEY"]})
    ans = json.loads(r["choices"][0]["message"]["content"])
    return ans, [c["编号"] for c in clauses], r["usage"]["total_tokens"], r.get("model", "")


def main(path, force=False, on_row=None):
    cfg = _env(); out_path = path[:-4] + "_一次定级.json"
    done = {} if force or not os.path.exists(out_path) else {r["字段"]: r for r in json.load(open(out_path, encoding="utf-8"))["结果"]}
    rows, tokens, model = [], 0, ""
    for f in csv.DictReader(open(path, encoding="utf-8")):
        if f["字段"] in done:
            rows.append(done[f["字段"]]); continue
        ans, got, tk, model = ask(f, cfg); tokens += tk
        kind = kind_of(f, ans)
        lv = level_of(ans.get("影响对象", ""), ans.get("影响程度", "无危害"), kind)
        rows.append({**f, **ans, "检索到的条文": got, "一次等级": lv}); print(f["中文名"], ans.get("影响对象"), ans.get("影响程度"), kind, "→", lv, flush=True)
        if on_row:
            on_row(len(rows), rows[-1])
    json.dump({"模型": model_name(model) if model else (done and json.load(open(out_path, encoding="utf-8"))["模型"]) or "(缓存)", "规则库": RULES["标准"], "结果": rows}, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"本次调用消耗词元 {tokens}")
    return rows, tokens


if __name__ == "__main__":
    main(sys.argv[1], "--force" in sys.argv)
