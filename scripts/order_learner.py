# -*- coding: utf-8 -*-
"""历史订单学习：从 order-list 真实返回中提炼"老样子"——最常点的组合、常去门店、常见下单时段。

order-list 返回结构：data.list[].orderId / createTime(yyyy-MM-dd HH:mm:ss) /
storeName / orderStatus / orderProductList[].productCode+productName+quantity /
realTotalAmount(元)。

用法：
    echo '{"orders":[...data.list...]}' | python3 scripts/order_learner.py
stdin 一个 JSON 对象，stdout 输出 JSON。无第三方依赖。
"""
import json
import sys
from collections import Counter


def combo_key(items):
    """一份订单的商品组合归一化为可比较的 key：[(code, qty), ...] 按 code 排序。"""
    return tuple(sorted(
        (str(item.get("productCode") or item.get("code") or item.get("productName") or item.get("name")),
         int(item.get("quantity", 1)))
        for item in items
    ))


def learn_orders(payload):
    orders = payload.get("orders", [])
    if not orders:
        return {
            "has_history": False,
            "usual_combo": None,
            "favorite_store": None,
            "typical_order_window": None,
            "order_count": 0,
            "message": "暂无历史订单，无法推荐老样子，请直接告诉我今天想吃什么",
        }

    combo_counter = Counter()
    combo_display = {}
    store_counter = Counter()
    hour_counter = Counter()

    for order in orders:
        items = order.get("orderProductList") or order.get("items") or []
        if items:
            key = combo_key(items)
            combo_counter[key] += 1
            combo_display[key] = [
                {"productCode": c, "quantity": q,
                 "productName": next(
                     (i.get("productName") or i.get("name") for i in items
                      if str(i.get("productCode") or i.get("code")
                             or i.get("productName") or i.get("name")) == c), c)}
                for c, q in key
            ]
        store_name = order.get("storeName") or order.get("store_name")
        if store_name:
            store_counter[store_name] += 1
        created = str(order.get("createTime") or order.get("created_at") or "")
        if len(created) >= 13 and created[10] == " ":
            try:
                hour_counter[int(created[11:13])] += 1
            except ValueError:
                pass

    top_combo, top_combo_count = combo_counter.most_common(1)[0] if combo_counter else (None, 0)
    top_store, top_store_count = store_counter.most_common(1)[0] if store_counter else (None, 0)

    window = None
    if hour_counter:
        hour, hour_count = hour_counter.most_common(1)[0]
        window = {"hour": hour, "label": "%02d:00-%02d:59" % (hour, hour), "count": hour_count}

    return {
        "has_history": True,
        "order_count": len(orders),
        "usual_combo": {
            "items": combo_display[top_combo],
            "times_ordered": top_combo_count,
        } if top_combo else None,
        "favorite_store": {"storeName": top_store, "times": top_store_count} if top_store else None,
        "typical_order_window": window,
    }


def main():
    try:
        payload = json.load(sys.stdin)
        result = learn_orders(payload)
        json.dump({"ok": True, "result": result}, sys.stdout, ensure_ascii=False, indent=2)
    except (ValueError, KeyError, TypeError) as exc:
        json.dump({"ok": False, "error": str(exc)}, sys.stdout, ensure_ascii=False)
        sys.exit(1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
