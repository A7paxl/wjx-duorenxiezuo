import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    paths = [common.BOARD, *common.INDEX_FILES, *common.OUTER_FILES]
    snap = common.snapshot(paths)
    try:
        common.rebuild_board()
        common.rebuild_indexes()
        common.publish_outer()
        ok, msg = common.commit_public("重建看板与索引")
        if not ok:
            common.rollback(snap)
            print(f"重建失败，已回滚：{msg}")
            return 1
        print("已重建：02-推进管理/任务看板.md、索引/")
        if msg:
            print(msg)
        return 0
    except Exception as e:
        common.rollback(snap)
        print(f"重建异常，已回滚：{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
