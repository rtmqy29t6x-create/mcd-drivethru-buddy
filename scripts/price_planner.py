# -*- coding: utf-8 -*-
"""券前比价：在调用 MCP calculate-price 核价前，用确定性脚本预估最优用券方案。

约定单笔订单最多使用一张券（与常见门店规则一致，真实核销以 calculate-price 为准）。
金额全程用"分"做整数运算，避免浮点误差。

用法：
    echo '{"items":[...], "coupons":[...]}' | python3 scripts/price_planner.py
stdin 一个 JSON 对象，stdout 输出 JSON。无第三方依赖。
"""
import json
import sys

CENT = 100


def to_cents(yuan):
    return int(round(float(yuan) * CENT))


def to_yuan(cents):
    return round(cents / CENT, 2)


def cart_subtotal_cents(items):
    total = 0
    for item in items:
        total += to_cents(item["price"]) * int(item.get("quantity", 1))
    return total


def apply_coupon(cart_cents, items, coupon):
    """返回 (应付分, 优惠分, 说明)。券不可用返回 None。"""
    ctype = coupon.get("type")

    if ctype == "amount_off":
        threshold = to_cents(coupon.get("threshold", 0))
        if cart_cents < threshold:
            return None
        off = to_cents(coupon["amount"])
        off = min(off, cart_cents)
        return cart_cents - off, off, "满 %s 减 %s" % (coupon.get("threshold"), coupon.get("amount"))

    if ctype == "percent_off":
        rate = float(coupon["rate"])
        if not 0 < rate <= 1:
            return None
        off = cart_cents - int(round(cart_cents * rate))
        cap = coupon.get("cap")
        if cap is not None:
            off = min(off, to_cents(cap))
        return cart_cents - off, off, "打 %g 折" % (rate * 10)

    if ctype == "fixed_price":
        target = coupon.get("item_code")
        fixed = to_cents(coupon["price"])
        saved = 0
        for item in items:
            if item.get("code") == target:
                saved += max(0, to_cents(item["price"]) - fixed)
                break
        else:
            return None
        if saved <= 0:
            return None
        return cart_cents - saved, saved, "单品特价 %s 元" % coupon.get("price")

    return None


def plan_price(payload):
    items = payload.get("items", [])
    if not items:
        raise ValueError("items 不能为空")
    cart_cents = cart_subtotal_cents(items)

    baseline = {
        "coupon_id": None,
        "coupon_title": "不使用优惠券",
        "payable": to_yuan(cart_cents),
        "saved": 0.0,
    }
    candidates = [baseline]
    unusable = []
    for coupon in payload.get("coupons", []):
        applied = apply_coupon(cart_cents, items, coupon)
        if applied is None:
            unusable.append({"coupon_id": coupon.get("id"), "coupon_title": coupon.get("title"),
                             "reason": "不满足使用条件或类型不支持"})
            continue
        payable, saved, desc = applied
        candidates.append({
            "coupon_id": coupon.get("id"),
            "coupon_title": coupon.get("title"),
            "payable": to_yuan(payable),
            "saved": to_yuan(saved),
            "rule": desc,
        })

    best = min(candidates, key=lambda c: (c["payable"], c["saved"] == 0))
    return {
        "subtotal": to_yuan(cart_cents),
        "best": best,
        "candidates": sorted(candidates, key=lambda c: c["payable"]),
        "unusable_coupons": unusable,
        "note": "本结果为本地预估，真实应付金额、配送费与可用券以 MCP calculate-price 返回为准",
    }


def main():
    try:
        payload = json.load(sys.stdin)
        result = plan_price(payload)
        json.dump({"ok": True, "result": result}, sys.stdout, ensure_ascii=False, indent=2)
    except (ValueError, KeyError, TypeError) as exc:
        json.dump({"ok": False, "error": str(exc)}, sys.stdout, ensure_ascii=False)
        sys.exit(1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
