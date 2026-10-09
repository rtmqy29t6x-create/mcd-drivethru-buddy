# -*- coding: utf-8 -*-
"""沿途门店打分排序：按绕行成本 / 预约支持 / 营业状态综合评分。

输入门店结构以 query-nearby-stores 真实返回为准（beType=5 时返回的全是
得来速餐厅）：storeCode / beCode / storeName / address / distance(米) /
businessStatus / businessStartTime / businessEndTime / reservation /
reservationTimeOptions。detour_minutes 为绕行估算，需由用户口述或经验值补充。

用法：
    echo '{"stores":[...], "require_reservation":true}' | python3 scripts/store_ranker.py
stdin 一个 JSON 对象，stdout 输出 JSON 排序结果。无第三方依赖。
"""
import json
import sys

DEFAULT_WEIGHTS = {
    "detour_penalty_per_min": 4.0,   # 每多绕行 1 分钟扣分
    "distance_penalty_per_km": 1.0,  # 每偏离路线 1 公里扣分
    "reservation_bonus": 15.0,
    "base_score": 60.0,
}


def normalize_store(store):
    """兼容真实返回字段与旧演示字段，归一化为内部结构。"""
    if "distance" in store:
        distance_km = float(store.get("distance") or 0) / 1000.0
    else:
        distance_km = float(store.get("distance_km", 0))
    return {
        "store_code": store.get("storeCode") or store.get("store_id"),
        "be_code": store.get("beCode"),
        "store_name": store.get("storeName") or store.get("store_name"),
        "address": store.get("address"),
        "is_open": bool(store.get("businessStatus", store.get("is_open", True))),
        "supports_reservation": bool(store.get("reservation", store.get("supports_reservation", False))),
        # beType=5 查询返回的均为得来速餐厅；显式传入 False 时尊重调用方
        "supports_drivethru": bool(store.get("supports_drivethru", True)),
        "detour_minutes": float(store.get("detour_minutes", 0)),
        "distance_km": distance_km,
        "business_hours": "%s-%s" % (store.get("businessStartTime", "?"), store.get("businessEndTime", "?"))
        if store.get("businessStartTime") else store.get("open_hours"),
        "reservation_options": store.get("reservationTimeOptions"),
    }


def score_store(store, weights, require_reservation, require_drivethru):
    """返回 (score, reasons, excluded_reason)。excluded_reason 非空表示被硬过滤。"""
    if not store["is_open"]:
        return None, [], "门店当前未营业"
    if require_drivethru and not store["supports_drivethru"]:
        return None, [], "不支持得来速车道取餐"
    if require_reservation and not store["supports_reservation"]:
        return None, [], "不支持预约单，无法按取餐时间提前下单"

    score = weights["base_score"]
    reasons = []

    score -= store["detour_minutes"] * weights["detour_penalty_per_min"]
    score -= store["distance_km"] * weights["distance_penalty_per_km"]
    reasons.append("绕行约 %g 分钟、距路线 %.1f 公里" % (store["detour_minutes"], store["distance_km"]))

    if store["supports_drivethru"]:
        reasons.append("支持得来速，免下车取餐")
    if store["supports_reservation"]:
        score += weights["reservation_bonus"]
        windows = ""
        if store["reservation_options"]:
            future = [o for o in store["reservation_options"] if not o.get("today")]
            if future:
                windows = "，%s 可约：%s" % (future[0]["date"], future[0]["reservationOptionText"])
        reasons.append("支持预约单%s" % windows)
    if store["business_hours"]:
        reasons.append("营业时间 %s" % store["business_hours"])

    return round(score, 2), reasons, None


def rank_stores(payload):
    weights = dict(DEFAULT_WEIGHTS)
    weights.update(payload.get("weights") or {})
    require_reservation = bool(payload.get("require_reservation", True))
    require_drivethru = bool(payload.get("require_drivethru", True))

    ranked, excluded = [], []
    for raw in payload.get("stores", []):
        store = normalize_store(raw)
        score, reasons, why_excluded = score_store(
            store, weights, require_reservation, require_drivethru)
        entry = {
            "storeCode": store["store_code"],
            "beCode": store["be_code"],
            "storeName": store["store_name"],
            "address": store["address"],
            "detour_minutes": store["detour_minutes"],
            "distance_km": round(store["distance_km"], 2),
            "supports_reservation": store["supports_reservation"],
        }
        if why_excluded:
            entry["excluded_reason"] = why_excluded
            excluded.append(entry)
        else:
            entry["score"] = score
            entry["reasons"] = reasons
            ranked.append(entry)

    ranked.sort(key=lambda e: (-e["score"], e["storeName"] or ""))
    for i, entry in enumerate(ranked, 1):
        entry["rank"] = i

    return {
        "recommended": ranked[0] if ranked else None,
        "ranked": ranked,
        "excluded": excluded,
        "weights": weights,
        "require_reservation": require_reservation,
        "require_drivethru": require_drivethru,
    }


def main():
    try:
        payload = json.load(sys.stdin)
        result = rank_stores(payload)
        json.dump({"ok": True, "result": result}, sys.stdout, ensure_ascii=False, indent=2)
    except (ValueError, KeyError, TypeError) as exc:
        json.dump({"ok": False, "error": str(exc)}, sys.stdout, ensure_ascii=False)
        sys.exit(1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
