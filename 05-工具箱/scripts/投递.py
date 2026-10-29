import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    p = argparse.ArgumentParser(description="投递协同单到公共仓交换区")
    p.add_argument("--from", dest="frm", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--type", default="协同单")
    p.add_argument("--主题", required=True)
    p.add_argument("--动作", default="请求确认")
    p.add_argument("--正件", required=True)
    p.add_argument("--说明", default="")
    a = p.parse_args()

    if a.frm not in common.members() or a.to not in common.members():
        print(f"成员不在名册；现有：{common.members()}")
        return 1
    src = Path(a.正件)
    if not src.is_absolute():
        src = Path.cwd() / src
    if not src.exists():
        print(f"正件不存在：{src}")
        return 1

    doc = common.doc_id(a.frm, a.to, a.主题, a.type)
    dest = common.OUTBOX / a.frm / f"{doc}.md"
    rel = dest.relative_to(common.SPACE).as_posix()
    ptr = common.INBOX / a.to / f"{doc}.pointer.md"
    personal = common.personal_repo(a.frm)
    personal_copy = personal / "05-单据" / f"{doc}.md" if personal else None

    paths = [dest, ptr, common.LEDGER, common.NOTICE, common.BOARD,
             common.INDEXES / "文件索引.md", common.INDEXES / "关键词索引.md", common.INDEXES / "人物索引.md"]
    if personal_copy:
        paths.append(personal_copy)
    snap = common.snapshot(paths)

    try:
        content = common.read(src)
        common.write(dest, content)
        common.pointer(a.to, rel, "来单")
        if personal_copy:
            common.write(personal_copy, content)
        common.append_ledger(f"| {doc} | {a.type} | {a.frm} | {a.to} | {a.主题} | 已投递 | {common.today()} |")
        common.notice(a.to, "来单", doc)
        common.rebuild_board()
        common.rebuild_indexes()
        ok, msg = common.commit_public(f"投递 {doc}")
        if not ok:
            common.rollback(snap)
            print(f"投递失败，已回滚：{msg}")
            return 1
        print(f"单号：{doc}")
        print(f"正件：{rel}")
        print(f"指向消息：{ptr.relative_to(common.SPACE).as_posix()}")
        if msg:
            print(msg)
        return 0
    except Exception as e:
        common.rollback(snap)
        print(f"投递异常，已回滚：{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
