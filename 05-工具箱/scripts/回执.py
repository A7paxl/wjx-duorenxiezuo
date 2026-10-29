import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    p = argparse.ArgumentParser(description="回执")
    p.add_argument("--from", dest="frm", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--原单", required=True)
    p.add_argument("--产出", required=True)
    p.add_argument("--说明", default="已办结")
    p.add_argument("--个人仓", default="")
    a = p.parse_args()

    if a.frm not in common.members() or a.to not in common.members():
        print(f"成员不在名册；现有：{common.members()}")
        return 1
    row = common.find_ledger(a.原单)
    if not row:
        print(f"台账里找不到原单：{a.原单}")
        return 1
    src = Path(a.产出)
    if not src.is_absolute():
        src = Path.cwd() / src
    if not src.exists():
        print(f"产出不存在：{src}")
        return 1

    receipt = common.OUTBOX / a.frm / f"{a.原单}-回执.md"
    rel = receipt.relative_to(common.SPACE).as_posix()
    ptr = common.INBOX / a.to / f"{a.原单}-回执.pointer.md"
    repo = common.personal_repo(a.frm, a.个人仓 or None)
    personal = repo / "05-单据" / f"{a.原单}-回执.md" if repo else None

    paths = [receipt, ptr, common.LEDGER, common.NOTICE, common.BOARD,
             common.INDEXES / "文件索引.md", common.INDEXES / "关键词索引.md", common.INDEXES / "人物索引.md"]
    if personal:
        paths.append(personal)
    snap = common.snapshot(paths)

    try:
        content = (
            f"# 回执\n\n"
            f"- 原单：{a.原单}\n"
            f"- 发起人：{row[2]}\n"
            f"- 接收人：{row[3]}\n"
            f"- 日期：{common.today()}\n"
            f"- 说明：{a.说明}\n\n---\n\n"
            f"{common.read(src)}"
        )
        common.write(receipt, content)
        common.pointer(a.to, rel, "回执")
        common.copy_to_personal(a.frm, f"{a.原单}-回执.md", content, root=a.个人仓 or None)
        common.update_ledger(a.原单, "已回执")
        common.notice(a.to, "回执", a.原单)
        common.rebuild_board()
        common.rebuild_indexes()
        ok, msg = common.commit_public(f"回执 {a.原单}")
        if not ok:
            common.rollback(snap)
            print(f"回执失败，已回滚：{msg}")
            return 1
        print(f"回执：{rel}")
        print(f"指向消息：{ptr.relative_to(common.SPACE).as_posix()}")
        if msg:
            print(msg)
        return 0
    except Exception as e:
        common.rollback(snap)
        print(f"回执异常，已回滚：{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
