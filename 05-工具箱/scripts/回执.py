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
    a = p.parse_args()

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

    receipt = common.PERSONAL / a.frm / "05-出件箱" / f"{a.原单}-回执.md"
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
    rel = receipt.relative_to(common.SPACE).as_posix()
    ptr = common.pointer(a.to, rel, "回执")
    common.update_ledger(a.原单, "已回执")
    common.notice(a.to, "回执", a.原单)

    print(f"回执：{rel}")
    print(f"指向消息：{ptr.relative_to(common.SPACE).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
