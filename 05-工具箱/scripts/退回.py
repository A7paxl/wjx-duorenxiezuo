import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    p = argparse.ArgumentParser(description="退回单")
    p.add_argument("--from", dest="frm", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--原单", required=True)
    p.add_argument("--原因", required=True)
    p.add_argument("--依据", default="")
    p.add_argument("--替代", default="")
    a = p.parse_args()

    row = common.find_ledger(a.原单)
    if not row:
        print(f"台账里找不到原单：{a.原单}")
        return 1

    doc = common.PERSONAL / a.frm / "05-出件箱" / f"{a.原单}-退回.md"
    content = (
        f"# 退回单\n\n"
        f"- 原单：{a.原单}\n"
        f"- 退回人：{a.frm}\n"
        f"- 接收人：{a.to}\n"
        f"- 日期：{common.today()}\n\n"
        f"## 原因\n\n{a.原因}\n\n"
        f"## 依据\n\n{a.依据 or '见术语与口径'}\n\n"
        f"## 替代做法\n\n{a.替代 or '无'}\n"
    )
    common.write(doc, content)
    rel = doc.relative_to(common.SPACE).as_posix()
    ptr = common.pointer(a.to, rel, "退回")
    common.update_ledger(a.原单, "已退回")
    common.notice(a.to, "退回", a.原单)

    print(f"退回单：{rel}")
    print(f"指向消息：{ptr.relative_to(common.SPACE).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
