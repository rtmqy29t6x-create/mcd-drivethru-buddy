# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import price_planner
from sample_data import SAMPLE_COUPON_RULES, SAMPLE_PRICE_RESULT

# 真实菜单快照中的餐品（query-meals 的 currentPrice 单位为元）
ITEMS = [
    {"code": "5022", "name": "猪柳蛋麦满分", "price": 18.0, "quantity": 1},
    {"code": "514851", "name": "咖啡阿芙佳朵", "price": 15.0, "quantity": 1},
]


class TestPricePlanner(unittest.TestCase):
    def test_sample_best_coupon(self):
        result = price_planner.plan_price({"items": ITEMS, "coupons": SAMPLE_COUPON_RULES})
        # 小计 33 元：满30减5 -> 28；88折 -> 29.04；特价券目标 BF2SET 不在购物车不可用
        self.assertEqual(result["subtotal"], 33.0)
        self.assertEqual(result["best"]["coupon_id"], "MC002")
        self.assertEqual(result["best"]["payable"], 28.0)
        self.assertEqual(result["best"]["saved"], 5.0)
        unusable_ids = {c["coupon_id"] for c in result["unusable_coupons"]}
        self.assertIn("MC001", unusable_ids)

    def test_amount_off_threshold_not_met(self):
        items = [{"code": "5024", "name": "猪柳麦满分", "price": 14.0, "quantity": 1}]
        result = price_planner.plan_price({"items": items, "coupons": SAMPLE_COUPON_RULES})
        # 满30减5 不可用；88折生效：14 * 0.88 = 12.32
        self.assertEqual(result["best"]["coupon_id"], "MC003")
        self.assertEqual(result["best"]["payable"], 12.32)
        unusable_ids = {c["coupon_id"] for c in result["unusable_coupons"]}
        self.assertIn("MC002", unusable_ids)

    def test_percent_off_cap(self):
        items = [{"code": "5022", "name": "猪柳蛋麦满分", "price": 18.0, "quantity": 5}]
        coupons = [{"id": "X", "title": "88折封顶6元", "type": "percent_off", "rate": 0.88, "cap": 6.0}]
        result = price_planner.plan_price({"items": items, "coupons": coupons})
        # 90 * 0.12 = 10.8 > 6，封顶减 6
        self.assertEqual(result["best"]["payable"], 84.0)
        self.assertEqual(result["best"]["saved"], 6.0)

    def test_fixed_price_only_discounts_target(self):
        items = [{"code": "5022", "name": "猪柳蛋麦满分", "price": 18.0, "quantity": 2}]
        coupons = [{"id": "F", "title": "特价15.9", "type": "fixed_price",
                    "item_code": "5022", "price": 15.9}]
        result = price_planner.plan_price({"items": items, "coupons": coupons})
        # 36 - (18 - 15.9) = 33.9，只优惠一件
        self.assertEqual(result["best"]["payable"], 33.9)

    def test_no_coupons_falls_back_to_baseline(self):
        result = price_planner.plan_price({"items": ITEMS, "coupons": []})
        self.assertEqual(result["best"]["coupon_id"], None)
        self.assertEqual(result["best"]["payable"], 33.0)

    def test_empty_items_rejected(self):
        with self.assertRaises(ValueError):
            price_planner.plan_price({"items": [], "coupons": []})

    def test_cent_precision(self):
        items = [{"code": "A", "name": "a", "price": 0.1, "quantity": 3}]
        result = price_planner.plan_price({"items": items, "coupons": []})
        self.assertEqual(result["subtotal"], 0.3)

    def test_real_price_snapshot_consistency(self):
        # 真实 calculate-price 快照：猪柳蛋麦满分 ×1 = 1800 分 = 18 元，
        # 与 query-meals 的 currentPrice "18"(元) 口径一致
        self.assertEqual(SAMPLE_PRICE_RESULT["price"], 1800)
        self.assertEqual(SAMPLE_PRICE_RESULT["price"] / 100, 18.0)
        self.assertEqual(SAMPLE_PRICE_RESULT["takeWayList"][0]["code"], "take-dt-quick")


if __name__ == "__main__":
    unittest.main()
