import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    p = argparse.ArgumentParser(description="投递协同单")
    p.add_argument("--from", dest="frm", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--type", default="协同单")
    p.add_argument("--主题", required=True)
    p.add_argument("--动作", default="请求确认")
    p.add_argument("--正件", required=True)
    p.add_argument("--说明", default="")
    a = p.parse_args()

    if a.frm not in common.members() or a.to not in common.members():
        print(f"成员不存在；现有：{common.members()}")
        return 1
    src = Path(a.正件)
    if not src.is_absolute():
        src = Path.cwd() / src
    if not src.exists():
        print(f"正件不存在：{src}")
        return 1

    doc = common.doc_id(a.frm, a.to, a.type, a.主题)
    dest = common.PERSONAL / a.frm / "05-出件箱" / f"{doc}.md"
    common.write(dest, common.read(src))
    rel = dest.relative_to(common.SPACE).as_posix()
    ptr = common.pointer(a.to, rel, "来单")
    common.append_ledger(f"| {doc} | {a.type} | {a.frm} | {a.to} | {a.主题} | 已投递 | {common.today()} |")
    common.notice(a.to, "来单", doc)

    print(f"单号：{doc}")
    print(f"正件：{rel}")
    print(f"指向消息：{ptr.relative_to(common.SPACE).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
