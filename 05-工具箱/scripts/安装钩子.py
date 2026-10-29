import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    p = argparse.ArgumentParser(description="安装本地 git 钩子")
    p.add_argument("--成员", required=True)
    p.add_argument("--个人仓", default="")
    p.add_argument("--演练", action="store_true")
    a = p.parse_args()

    repo = common.personal_repo(a.成员, a.个人仓 or None)
    if not repo:
        print("找不到个人仓；外部成员请用 --个人仓 指定")
        return 1
    personal_hook = repo / ".git" / "hooks" / "post-commit"
    public_hook = common.PUBLIC / ".git" / "hooks" / "post-commit"
    personal_body = f'''#!/bin/sh
cd "$(git rev-parse --show-toplevel)"
python3 "{common.PUBLIC}/05-工具箱/scripts/同步工作台.py" --成员 {a.成员}{f' --个人仓 "{repo}"' if a.个人仓 else ""}
'''
    public_body = f'''#!/bin/sh
python3 "{common.PUBLIC}/05-工具箱/scripts/巡检.py" || true
python3 "{common.PUBLIC}/05-工具箱/scripts/模拟通知.py" || true
'''
    if a.演练:
        print(f"【演练】写 {personal_hook}")
        print(personal_body)
        print(f"【演练】写 {public_hook}")
        print(public_body)
        return 0

    common.write(personal_hook, personal_body)
    common.write(public_hook, public_body)
    personal_hook.chmod(0o755)
    public_hook.chmod(0o755)
    print(f"已安装：{personal_hook}")
    print(f"已安装：{public_hook}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
