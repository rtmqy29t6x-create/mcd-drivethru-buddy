# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import order_learner
from sample_data import SAMPLE_ORDERS


def make_order(order_id, create_time, items, store="上海老沪闵路得来速餐厅"):
    return {
        "orderId": order_id,
        "orderType": "1",
        "createTime": create_time,
        "beType": "5",
        "storeName": store,
        "orderStatus": "订单已完成",
        "orderProductList": [
            {"productCode": c, "productName": n, "quantity": q, "comboItemList": []}
            for c, n, q in items
        ],
        "realTotalAmount": "33",
    }


class TestOrderLearner(unittest.TestCase):
    def test_real_snapshot_usual_combo(self):
        result = order_learner.learn_orders({"orders": SAMPLE_ORDERS})
        self.assertTrue(result["has_history"])
        self.assertEqual(result["order_count"], 4)
        combo = result["usual_combo"]
        self.assertEqual(combo["times_ordered"], 3)
        codes = {item["productCode"] for item in combo["items"]}
        self.assertEqual(codes, {"5022", "514851"})
        self.assertEqual(result["favorite_store"]["storeName"], "上海老沪闵路得来速餐厅")
        self.assertEqual(result["favorite_store"]["times"], 3)
        self.assertEqual(result["typical_order_window"]["hour"], 8)

    def test_empty_history(self):
        result = order_learner.learn_orders({"orders": []})
        self.assertFalse(result["has_history"])
        self.assertIsNone(result["usual_combo"])
        self.assertIn("想吃什么", result["message"])

    def test_combo_quantity_matters(self):
        orders = [
            make_order("1", "2026-09-01 08:00:00", [("A", "甲", 1)]),
            make_order("2", "2026-09-02 08:00:00", [("A", "甲", 2)]),
            make_order("3", "2026-09-03 08:00:00", [("A", "甲", 2)]),
        ]
        result = order_learner.learn_orders({"orders": orders})
        self.assertEqual(result["usual_combo"]["times_ordered"], 2)
        self.assertEqual(result["usual_combo"]["items"][0]["quantity"], 2)

    def test_order_of_items_does_not_matter(self):
        orders = [
            make_order("1", "2026-09-01 08:00:00", [("A", "甲", 1), ("B", "乙", 1)]),
            make_order("2", "2026-09-02 08:00:00", [("B", "乙", 1), ("A", "甲", 1)]),
        ]
        result = order_learner.learn_orders({"orders": orders})
        self.assertEqual(result["usual_combo"]["times_ordered"], 2)

    def test_malformed_create_time_ignored(self):
        orders = [make_order("1", "未知时间", [("A", "甲", 1)])]
        result = order_learner.learn_orders({"orders": orders})
        self.assertIsNone(result["typical_order_window"])
        self.assertEqual(result["usual_combo"]["times_ordered"], 1)

    def test_single_real_order_shape(self):
        # 该账号真实历史订单快照（仅一单中薯条）也能正确解析
        result = order_learner.learn_orders({"orders": SAMPLE_ORDERS[:1]})
        self.assertEqual(result["usual_combo"]["items"][0]["productName"], "中薯条")
        self.assertEqual(result["typical_order_window"]["hour"], 18)


if __name__ == "__main__":
    unittest.main()
