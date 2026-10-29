import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    p = argparse.ArgumentParser(description="阶段收口：五问、冻结、重置、经验库")
    p.add_argument("--阶段", required=True)
    p.add_argument("--共识", default="待补充")
    p.add_argument("--决策", default="待补充")
    p.add_argument("--假设", default="待补充")
    p.add_argument("--责任", default="待补充")
    p.add_argument("--资产", default="待补充")
    p.add_argument("--经验", default="")
    p.add_argument("--演练", action="store_true")
    a = p.parse_args()

    archive = common.PUBLIC / "06-归档" / f"{common.today()}_{a.阶段}"
    current = common.PUBLIC / "02-推进管理" / "当前推进.md"
    decisions = common.PUBLIC / "04-知识区" / "动态知识" / "决策记录.md"
    roster = common.PUBLIC / "01-成员与规则" / "成员名册.md"
    board = common.PUBLIC / "02-推进管理" / "任务看板.md"
    exp = common.PUBLIC / "05-工具箱" / "经验库.md"

    files = [current, decisions, roster, board]
    if a.演练:
        print("【演练】将执行：")
        print(f"1. 冻结快照到 {archive.relative_to(common.PUBLIC).as_posix()}")
        for f in files:
            print(f"   - {f.relative_to(common.PUBLIC).as_posix()}")
        print("2. 写收口五问.md")
        print("3. 重置 当前推进.md / 决策记录.md")
        print(f"4. 经验库追加：{a.经验 or '（未提供）'}")
        return 0

    archive_paths = [archive / f.name for f in files] + [archive / "收口五问.md"]
    index_paths = list(common.INDEX_FILES)
    snap = common.snapshot(files + [exp] + archive_paths + index_paths + list(common.OUTER_FILES))
    try:
        archive.mkdir(parents=True, exist_ok=True)
        for f in files:
            common.write(archive / f.name, common.read(f))
        five = f"""# 收口五问 · {a.阶段}

- 日期：{common.today()}

## 共识

{a.共识}

## 决策

{a.决策}

## 假设

{a.假设}

## 责任

{a.责任}

## 资产

{a.资产}
"""
        common.write(archive / "收口五问.md", five)

        common.write(current, f"""# 当前推进

> 统筹维护。只装“现在怎么样”；方案、规则、纪要在知识区。

更新：{common.today()}

## 项目目标

| 目标 | 指标 | 当前 | 回填 |
| --- | --- | --- | --- |
| PLUS 拉新与粘性 | 活动渠道归因新开通会员 10 万+ | 未开始 |  |
| 拍拍以旧换新 | 参与用户中以旧换新人数占比 15%+ | 未开始 |  |

## 阶段

| 阶段 | 目标 | 状态 |
| --- | --- | --- |
| 下一阶段 | 待定 | 未开始 |

## 分工

| 谁 | 干什么 | 到期 | 任务包 |
| --- | --- | --- | --- |
|  |  |  |  |

## 会议待办

| 日期 | 待办 | 拆给谁 | 状态 |
| --- | --- | --- | --- |

## 目标回填

| 日期 | 目标 | 完成了一格 | 证据 |
| --- | --- | --- | --- |
""")
        common.write(decisions, "# 决策记录\n\n> 关键结论逐条登记；只增不改。纪要里只写出处。\n\n| 日期 | 决定 | 来源 |\n| --- | --- | --- |\n")
        if a.经验:
            s = common.read(exp).rstrip().splitlines()
            s.append(f"| {common.today()} | {a.经验} | {a.阶段} 收口 |")
            common.write(exp, "\n".join(s) + "\n")

        common.rebuild_board()
        common.rebuild_indexes()
        common.publish_outer()
        ok, msg = common.commit_public(f"阶段收口 {a.阶段}")
        if not ok:
            common.rollback(snap)
            print(f"收口失败，已回滚：{msg}")
            return 1
        print(f"已收口：{archive.relative_to(common.PUBLIC).as_posix()}")
        print("当前推进与决策记录已重置；旧版在归档快照里。")
        if msg:
            print(msg)
        return 0
    except Exception as e:
        common.rollback(snap)
        print(f"收口异常，已回滚：{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
