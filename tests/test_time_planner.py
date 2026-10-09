# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import time_planner


class TestParseTime(unittest.TestCase):
    def test_parse_valid(self):
        self.assertEqual(time_planner.parse_hhmm("08:40"), 520)
        self.assertEqual(time_planner.parse_hhmm("0:05"), 5)
        self.assertEqual(time_planner.parse_hhmm("23:59"), 1439)

    def test_parse_invalid(self):
        for bad in ["25:00", "08:60", "abc", "", "8:5x"]:
            with self.assertRaises(ValueError):
                time_planner.parse_hhmm(bad)

    def test_format_roundtrip(self):
        self.assertEqual(time_planner.format_hhmm(520), "08:40")
        self.assertEqual(time_planner.format_hhmm(1500), "01:00")


class TestBuildPlan(unittest.TestCase):
    def test_basic_commute(self):
        plan = time_planner.build_plan({
            "arrive_company_at": "08:40",
            "home_to_store_minutes": 18,
            "store_to_company_minutes": 12,
            "buffer_minutes": 15,
            "pickup_wait_minutes": 3,
        })
        # 取餐完成 08:40-12-15=08:13，到店 08:10，预约取整仍为 08:10，出门 07:52
        self.assertEqual(plan["reserve_pickup_at"], "08:10")
        self.assertEqual(plan["arrive_store_at"], "08:10")
        self.assertEqual(plan["leave_home_at"], "07:52")
        self.assertEqual(plan["menu_period"], "breakfast")
        self.assertEqual(plan["warnings"], [])

    def test_slot_rounding(self):
        plan = time_planner.build_plan({
            "arrive_company_at": "08:41",
            "home_to_store_minutes": 18,
            "store_to_company_minutes": 12,
            "buffer_minutes": 15,
            "pickup_wait_minutes": 3,
        })
        # 到店 08:11，向上取整到 5 分钟粒度 -> 08:15
        self.assertEqual(plan["arrive_store_at"], "08:11")
        self.assertEqual(plan["reserve_pickup_at"], "08:15")

    def test_regular_menu_after_breakfast_end(self):
        plan = time_planner.build_plan({
            "arrive_company_at": "12:00",
            "home_to_store_minutes": 10,
            "store_to_company_minutes": 10,
        })
        self.assertEqual(plan["menu_period"], "regular")

    def test_too_late_warning(self):
        plan = time_planner.build_plan({
            "arrive_company_at": "08:40",
            "home_to_store_minutes": 60,
            "now": "08:00",
        })
        self.assertTrue(any("来不及" in w for w in plan["warnings"]))
        self.assertIn("minutes_until_leave_home", plan)

    def test_minutes_until_leave(self):
        plan = time_planner.build_plan({
            "arrive_company_at": "08:40",
            "home_to_store_minutes": 18,
            "store_to_company_minutes": 12,
            "buffer_minutes": 15,
            "pickup_wait_minutes": 3,
            "now": "07:30",
        })
        self.assertEqual(plan["minutes_until_leave_home"], 22)

    def test_reservation_date_mcp_format(self):
        plan = time_planner.build_plan({
            "arrive_company_at": "08:40",
            "home_to_store_minutes": 18,
            "store_to_company_minutes": 12,
            "buffer_minutes": 15,
            "pickup_wait_minutes": 3,
            "date": "2026-10-10",
        })
        # 直接产出 MCP reservationDate 入参格式 yyyy-MM-dd HH:mm
        self.assertEqual(plan["reservation_date"], "2026-10-10 08:10")


if __name__ == "__main__":
    unittest.main()
