# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import store_ranker
from sample_data import SAMPLE_STORES


def make_store(**kw):
    base = {
        "storeCode": "X", "beCode": "X41", "storeName": "测试店",
        "address": "某路 1 号", "distance": 1000, "detour_minutes": 5,
        "businessStatus": True, "businessStartTime": "07:00", "businessEndTime": "22:00",
        "reservation": True,
    }
    base.update(kw)
    return base


class TestRankStores(unittest.TestCase):
    def test_real_snapshot_ranking(self):
        result = store_ranker.rank_stores({"stores": SAMPLE_STORES})
        ranked = result["ranked"]
        # 真实快照 5 家店全部营业且支持预约，无人被过滤
        self.assertEqual(len(ranked), 5)
        self.assertEqual(result["excluded"], [])
        # 老沪闵路店绕行 4 分钟最少，应排第一
        self.assertEqual(ranked[0]["storeCode"], "1450485")
        self.assertEqual(result["recommended"]["storeCode"], "1450485")
        self.assertEqual([e["rank"] for e in ranked], [1, 2, 3, 4, 5])
        # distance 单位已从米换算为公里
        self.assertAlmostEqual(ranked[0]["distance_km"], 7.41, places=2)
        # 推荐理由中带预约窗口文本
        self.assertTrue(any("可约" in r for r in ranked[0]["reasons"]))

    def test_score_descending(self):
        result = store_ranker.rank_stores({"stores": SAMPLE_STORES})
        scores = [e["score"] for e in result["ranked"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_closed_store_excluded(self):
        stores = [make_store(storeCode="A"), make_store(storeCode="B", businessStatus=False)]
        result = store_ranker.rank_stores({"stores": stores})
        self.assertEqual([e["storeCode"] for e in result["ranked"]], ["A"])
        self.assertEqual(result["excluded"][0]["storeCode"], "B")
        self.assertIn("未营业", result["excluded"][0]["excluded_reason"])

    def test_no_reservation_excluded_by_default(self):
        stores = [make_store(storeCode="A"), make_store(storeCode="B", reservation=False)]
        result = store_ranker.rank_stores({"stores": stores})
        self.assertEqual([e["storeCode"] for e in result["ranked"]], ["A"])
        self.assertIn("不支持预约", result["excluded"][0]["excluded_reason"])

    def test_not_requiring_reservation_keeps_store(self):
        stores = [make_store(storeCode="A"), make_store(storeCode="B", reservation=False)]
        result = store_ranker.rank_stores({"stores": stores, "require_reservation": False})
        self.assertEqual({e["storeCode"] for e in result["ranked"]}, {"A", "B"})

    def test_custom_weights_change_ranking(self):
        stores = [
            make_store(storeCode="A", storeName="甲", detour_minutes=1, reservation=False),
            make_store(storeCode="B", storeName="乙", detour_minutes=9, reservation=True),
        ]
        default = store_ranker.rank_stores({"stores": stores, "require_reservation": False})
        self.assertEqual(default["ranked"][0]["storeCode"], "A")
        heavy = store_ranker.rank_stores({
            "stores": stores,
            "require_reservation": False,
            "weights": {"reservation_bonus": 100.0},
        })
        self.assertEqual(heavy["ranked"][0]["storeCode"], "B")

    def test_empty_stores(self):
        result = store_ranker.rank_stores({"stores": []})
        self.assertIsNone(result["recommended"])
        self.assertEqual(result["ranked"], [])


if __name__ == "__main__":
    unittest.main()
