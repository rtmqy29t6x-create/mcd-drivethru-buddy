# -*- coding: utf-8 -*-
"""通勤时间确定性计算：由"到公司时间"倒推预约取餐时间窗、出门时间、菜单时段。

用法：
    echo '{"arrive_company_at":"08:40", ...}' | python3 scripts/time_planner.py
stdin 一个 JSON 对象，stdout 输出 JSON 结果。无第三方依赖。
"""
import json
import re
import sys

MINUTES_PER_DAY = 24 * 60
DEFAULTS = {
    "buffer_minutes": 15,        # 到店取餐后到正式开工之间的缓冲
    "pickup_wait_minutes": 3,    # 得来速窗口取餐预估耗时
    "home_to_store_minutes": 20,
    "store_to_company_minutes": 10,
    "breakfast_end": "10:30",    # 早餐菜单大时段截止；各店预约早餐窗口以 reservationTimeOptions 为准（常见至 10:15）
    "slot_round_minutes": 5,     # 预约取餐时间按 5 分钟取整
}

_TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")


def parse_hhmm(text):
    """'HH:MM' -> 当日分钟数。非法输入抛 ValueError。"""
    m = _TIME_RE.match(str(text).strip())
    if not m:
        raise ValueError("非法时间格式: %r，应为 HH:MM" % (text,))
    hour, minute = int(m.group(1)), int(m.group(2))
    if hour > 23 or minute > 59:
        raise ValueError("非法时间: %r" % (text,))
    return hour * 60 + minute


def format_hhmm(minutes):
    minutes = minutes % MINUTES_PER_DAY
    return "%02d:%02d" % (minutes // 60, minutes % 60)


def round_up_to_slot(minutes, slot):
    """向上取整到 slot 分钟粒度，用于预约取餐时间。"""
    if slot <= 0:
        return minutes
    return ((minutes + slot - 1) // slot) * slot


def menu_period_at(minutes, breakfast_end):
    """取餐时刻适用的菜单时段：breakfast / regular。"""
    return "breakfast" if minutes < breakfast_end else "regular"


def build_plan(params):
    cfg = dict(DEFAULTS)
    cfg.update({k: v for k, v in params.items() if v is not None})

    arrive_company = parse_hhmm(cfg["arrive_company_at"])
    breakfast_end = parse_hhmm(cfg["breakfast_end"])

    buffer_min = int(cfg["buffer_minutes"])
    pickup_wait = int(cfg["pickup_wait_minutes"])
    home_to_store = int(cfg["home_to_store_minutes"])
    store_to_company = int(cfg["store_to_company_minutes"])
    slot = int(cfg["slot_round_minutes"])

    # 倒推：到公司 <- 路上 <- 取餐完成 <- 到店 <- 出门
    pickup_done = arrive_company - store_to_company - buffer_min
    arrive_store = pickup_done - pickup_wait
    reserve_pickup_at = round_up_to_slot(arrive_store, slot)
    leave_home = arrive_store - home_to_store

    warnings = []
    now_minutes = None
    if cfg.get("now"):
        now_minutes = parse_hhmm(cfg["now"])
        if leave_home < now_minutes:
            warnings.append(
                "按当前时间 %s 已经来不及 %s 出门，请推迟到公司时间或放弃途中取餐"
                % (format_hhmm(now_minutes), format_hhmm(leave_home))
            )
    if menu_period_at(reserve_pickup_at, breakfast_end) == "breakfast" and \
            menu_period_at(reserve_pickup_at + pickup_wait + 10, breakfast_end) == "regular":
        warnings.append(
            "取餐时间临近早餐截止 %s，若路上延误可能错过早餐菜单" % cfg["breakfast_end"]
        )

    plan = {
        "arrive_company_at": format_hhmm(arrive_company),
        "reserve_pickup_at": format_hhmm(reserve_pickup_at),
        "arrive_store_at": format_hhmm(arrive_store),
        "leave_home_at": format_hhmm(leave_home),
        "menu_period": menu_period_at(reserve_pickup_at, breakfast_end),
        "breakfast_end": cfg["breakfast_end"],
        "assumptions": {
            "buffer_minutes": buffer_min,
            "pickup_wait_minutes": pickup_wait,
            "home_to_store_minutes": home_to_store,
            "store_to_company_minutes": store_to_company,
            "slot_round_minutes": slot,
        },
        "warnings": warnings,
    }
    if cfg.get("date"):
        # 直接产出 MCP 预约入参格式（query-meals/calculate-price/create-order 的
        # reservationDate，yyyy-MM-dd HH:mm）；预约时刻须落在门店
        # reservationTimeOptions 对应时段窗口内
        plan["reservation_date"] = "%s %s" % (cfg["date"], format_hhmm(reserve_pickup_at))
    if now_minutes is not None:
        plan["minutes_until_leave_home"] = (leave_home - now_minutes) % MINUTES_PER_DAY
    return plan


def main():
    try:
        params = json.load(sys.stdin)
        result = build_plan(params)
        json.dump({"ok": True, "plan": result}, sys.stdout, ensure_ascii=False, indent=2)
    except (ValueError, KeyError, TypeError) as exc:
        json.dump({"ok": False, "error": str(exc)}, sys.stdout, ensure_ascii=False)
        sys.exit(1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
