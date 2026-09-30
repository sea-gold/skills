#!/usr/bin/env python3
"""mermaid-board 生成器：从 <图名>.md 生成 <图名>.html

用法: python build.py <md文件路径>
输出: 同目录下同名 .html（整体覆盖）
"""
import sys, re, datetime
from pathlib import Path

CARD = '''<div class="card">
  {h2}<pre class="mermaid">
{source}
  </pre>
</div>
'''

def main():
    if len(sys.argv) != 2:
        sys.exit("用法: python build.py <md文件路径>")
    md_path = Path(sys.argv[1])
    text = md_path.read_text(encoding="utf-8")

    # 标题 = 第一个一级标题
    m = re.search(r"^# (.+)$", text, re.M)
    title = m.group(1).strip() if m else md_path.stem

    # 日期 = "> 更新于 ..." 行，否则今天
    m = re.search(r"^> 更新于\s*(\S+)", text, re.M)
    date = m.group(1) if m else datetime.date.today().isoformat()

    # 提取 (小标题, mermaid源码)：小标题 = 块之前最近的二级标题
    blocks = []
    pattern = re.compile(r"```mermaid\n(.*?)```", re.S)
    pos = 0
    for bm in pattern.finditer(text):
        heads = re.findall(r"^## (.+)$", text[pos:bm.start()], re.M)
        blocks.append((heads[-1].strip() if heads else None, bm.group(1).rstrip()))
        pos = bm.end()
    if not blocks:
        sys.exit("错误: md 中没有 mermaid 代码块")

    # 基础检查（只警告不阻断，渲染问题由用户看图反馈）
    for i, (_, src) in enumerate(blocks, 1):
        if "classDef" not in src:
            print(f"警告: 第{i}个图缺少 classDef 配色定义")
        if src.count('"') % 2 != 0:
            print(f"警告: 第{i}个图双引号不成对")
        for ch in ("&", "<u", "#"):
            pass  # <br/> 合法，不做字符级阻断

    template = (Path(__file__).parent / "template.html").read_text(encoding="utf-8")

    cards = "\n".join(
        CARD.format(h2=f"<h2>{h}</h2>\n  " if h else "", source=src)
        for h, src in blocks
    )
    # 替换模板中示例卡片区（首个 .card 到最后一个 </div> 前的注释段）
    html = re.sub(
        r"<!-- 每个 mermaid 块一个卡片.*?</div>\n",
        cards, template, count=1, flags=re.S,
    )
    html = (html.replace("{{TITLE}}", title)
                .replace("{{DATE}}", date)
                .replace("{{MD_FILENAME}}", md_path.name))

    out = md_path.with_suffix(".html")
    out.write_text(html, encoding="utf-8")
    print(f"已生成: {out}（{len(blocks)} 张图）")

if __name__ == "__main__":
    main()
