import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    p = argparse.ArgumentParser(description="归集产出到知识区 current")
    p.add_argument("--成果", required=True)
    p.add_argument("--名称", required=True)
    p.add_argument("--来源单", required=True)
    a = p.parse_args()

    src = Path(a.成果)
    if not src.is_absolute():
        src = Path.cwd() / src
    if not src.exists():
        print(f"成果不存在：{src}")
        return 1
    if not common.find_ledger(a.来源单):
        print(f"台账里找不到来源单：{a.来源单}")
        return 1

    name = a.名称
    if not Path(name).suffix:
        name += src.suffix
    current = common.CURRENT / name
    old = common.HISTORY / f"{Path(name).stem}_{common.today()}{Path(name).suffix}" if current.exists() else None

    paths = [current, old, common.LEDGER, common.NOTICE, common.BOARD,
             common.INDEXES / "文件索引.md", common.INDEXES / "关键词索引.md", common.INDEXES / "人物索引.md"]
    snap = common.snapshot([p for p in paths if p])

    try:
        if old:
            common.write(old, common.read(current))
            print(f"旧版进 history：{old.relative_to(common.SPACE).as_posix()}")
        common.write(current, common.read(src))
        common.update_ledger(a.来源单, "已归集")
        common.notice("ALL", "归集", a.来源单)
        common.rebuild_board()
        common.rebuild_indexes()
        ok, msg = common.commit_public(f"归集 {a.来源单}")
        if not ok:
            common.rollback(snap)
            print(f"归集失败，已回滚：{msg}")
            return 1
        print(f"归集：{current.relative_to(common.SPACE).as_posix()}")
        if msg:
            print(msg)
        return 0
    except Exception as e:
        common.rollback(snap)
        print(f"归集异常，已回滚：{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
