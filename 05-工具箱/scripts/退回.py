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
    p.add_argument("--个人仓", default="")
    a = p.parse_args()

    if a.frm not in common.members() or a.to not in common.members():
        print(f"成员不在名册；现有：{common.members()}")
        return 1
    row = common.find_ledger(a.原单)
    if not row:
        print(f"台账里找不到原单：{a.原单}")
        return 1

    doc = common.OUTBOX / a.frm / f"{a.原单}-退回.md"
    rel = doc.relative_to(common.SPACE).as_posix()
    ptr = common.INBOX / a.to / f"{a.原单}-退回.pointer.md"
    personal = common.copy_to_personal(a.frm, f"{a.原单}-退回.md", "", root=a.个人仓 or None)

    paths = [doc, ptr, common.LEDGER, common.NOTICE, common.BOARD,
             common.INDEXES / "文件索引.md", common.INDEXES / "关键词索引.md", common.INDEXES / "人物索引.md"]
    if personal:
        paths.append(personal)
    snap = common.snapshot(paths)

    try:
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
        common.pointer(a.to, rel, "退回")
        common.copy_to_personal(a.frm, f"{a.原单}-退回.md", content, root=a.个人仓 or None)
        common.update_ledger(a.原单, "已退回")
        common.notice(a.to, "退回", a.原单)
        common.rebuild_board()
        common.rebuild_indexes()
        ok, msg = common.commit_public(f"退回 {a.原单}")
        if not ok:
            common.rollback(snap)
            print(f"退回失败，已回滚：{msg}")
            return 1
        print(f"退回单：{rel}")
        print(f"指向消息：{ptr.relative_to(common.SPACE).as_posix()}")
        if msg:
            print(msg)
        return 0
    except Exception as e:
        common.rollback(snap)
        print(f"退回异常，已回滚：{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
