# -*- coding: utf-8 -*-
"""内置样例数据：无 MCD_MCP_TOKEN 时供 dry-run 演示与离线单测使用。

数据快照采集于 2026-10-09，来自麦当劳 MCP Server 真实返回
（query-nearby-stores / query-meals / order-list / available-coupons），
字段结构与线上保持一致；detour_minutes 为演示用绕行估算值，非 MCP 返回字段。
SAMPLE_ORDERS 中除首条为真实历史订单快照外，其余为同结构演示数据。
"""

# query-nearby-stores {"beType":5,"searchType":2,"city":"上海市","keyword":"漕河泾"} 真实快照
# beType=5 返回的全部是得来速餐厅；distance 单位为米
SAMPLE_STORES = [
    {
        "storeCode": "1450485",
        "beCode": "145048541",
        "storeName": "上海老沪闵路得来速餐厅",
        "address": "老沪闵路1492号国拓1501综合产业园麦当劳餐厅",
        "distance": 7405,
        "detour_minutes": 4,
        "businessStatus": True,
        "businessStartTime": "07:00",
        "businessEndTime": "22:00",
        "reservation": True,
        "reservationTimeOptions": [
            {"date": "2026-10-09", "today": True, "reservationOptionText": "夜市(17:14至21:45)"},
            {"date": "2026-10-10", "today": False,
             "reservationOptionText": "早餐(07:14至10:15)，午餐(10:44至14:15)，下午茶(14:44至16:45)，夜市(17:14至21:45)"},
        ],
    },
    {
        "storeCode": "1450560",
        "beCode": "145056041",
        "storeName": "上海景西路得来速餐厅",
        "address": "银都路1959 号4幢一层A1、A2麦当劳",
        "distance": 8162,
        "detour_minutes": 6,
        "businessStatus": True,
        "businessStartTime": "06:00",
        "businessEndTime": "22:00",
        "reservation": True,
        "reservationTimeOptions": [
            {"date": "2026-10-09", "today": True, "reservationOptionText": "夜市(17:14至21:45)"},
            {"date": "2026-10-10", "today": False,
             "reservationOptionText": "早餐(06:14至10:15)，午餐(10:44至14:15)，下午茶(14:44至16:45)，夜市(17:14至21:45)"},
        ],
    },
    {
        "storeCode": "1450098",
        "beCode": "145009841",
        "storeName": "上海莘松路得来速餐厅",
        "address": "新桥镇莘松路1028号101室",
        "distance": 8866,
        "detour_minutes": 9,
        "businessStatus": True,
        "businessStartTime": "07:00",
        "businessEndTime": "01:00",
        "reservation": True,
        "reservationTimeOptions": [
            {"date": "2026-10-09", "today": True,
             "reservationOptionText": "夜市(17:14至21:45)，宵夜(22:14至23:59)"},
            {"date": "2026-10-10", "today": False,
             "reservationOptionText": "宵夜(00:00至00:46,22:14至23:59)，早餐(07:14至10:15)，午餐(10:44至14:15)，下午茶(14:44至16:45)，夜市(17:14至21:45)"},
        ],
    },
    {
        "storeCode": "1450407",
        "beCode": "145040741",
        "storeName": "上海康建商务广场得来速餐厅",
        "address": "真南路1288号麦当劳",
        "distance": 11629,
        "detour_minutes": 14,
        "businessStatus": True,
        "businessStartTime": "07:00",
        "businessEndTime": "21:00",
        "reservation": True,
        "reservationTimeOptions": [
            {"date": "2026-10-09", "today": True, "reservationOptionText": "夜市(17:14至20:46)"},
            {"date": "2026-10-10", "today": False,
             "reservationOptionText": "早餐(07:14至10:15)，午餐(10:44至14:15)，下午茶(14:44至16:45)，夜市(17:14至20:46)"},
        ],
    },
    {
        "storeCode": "1450347",
        "beCode": "145034741",
        "storeName": "上海松江泗泾得来速餐厅",
        "address": "泗泾镇沪松公路2871弄69号汇泾商业广场项目一楼-17室、二楼-34室商铺",
        "distance": 13610,
        "detour_minutes": 18,
        "businessStatus": True,
        "businessStartTime": "06:30",
        "businessEndTime": "23:00",
        "reservation": True,
        "reservationTimeOptions": [
            {"date": "2026-10-09", "today": True,
             "reservationOptionText": "夜市(17:14至21:45)，宵夜(22:14至22:46)"},
            {"date": "2026-10-10", "today": False,
             "reservationOptionText": "早餐(06:44至10:15)，午餐(10:44至14:15)，下午茶(14:44至16:45)，夜市(17:14至21:45)，宵夜(22:14至22:46)"},
        ],
    },
]

# query-meals 预约早餐场景真实快照（storeCode=1450485, beType=5, orderType=1,
# reservationDate="2026-10-10 08:00"），menu_period=breakfast
# currentPrice/originalPrice 单位为元（字符串）；calculate-price 返回金额单位为分
SAMPLE_MENU = {
    "menu_period": "breakfast",
    "reservation_date": "2026-10-10 08:00",
    "categories": [
        "人气热卖", "超值早餐", "6折起早餐卡专区", "厚松饼堡系列", "麦满分系列",
        "麦咖啡™", "炒双蛋堡系列", "早安营养卷", "一早现磨", "粥王系列", "小食甜品/其他", "饮品",
    ],
    "meals": {
        "5022": {"name": "猪柳蛋麦满分", "currentPrice": "18", "originalPrice": "18", "discountType": None},
        "5024": {"name": "猪柳麦满分", "currentPrice": "14", "originalPrice": "14", "discountType": None},
        "9900003431": {"name": "大脆鸡扒麦满分组合", "currentPrice": "8.1", "originalPrice": "13.5",
                       "discountType": "早餐卡优惠"},
        "514850": {"name": "抹茶阿芙佳朵", "currentPrice": "15", "originalPrice": "15", "discountType": None},
        "514851": {"name": "咖啡阿芙佳朵", "currentPrice": "15", "originalPrice": "15", "discountType": None},
        "2430": {"name": "【美汁源】“黄金橙橙”", "currentPrice": "13", "originalPrice": "13", "discountType": None},
    },
}

# calculate-price 真实快照（猪柳蛋麦满分 ×1，得来速预约 2026-10-10 08:00，金额单位分）
# takeWayList 为该门店可选取餐方式，create-order 需回传 takeWayCode
SAMPLE_PRICE_RESULT = {
    "productOriginalPrice": 1800,
    "productPrice": 1800,
    "originalPrice": 1800,
    "discount": 0,
    "price": 1800,
    "productList": [
        {"productCode": "5022", "productName": "猪柳蛋麦满分", "quantity": 1,
         "originalSubtotal": 1800, "subtotal": 1800},
    ],
    "takeWayList": [
        {"code": "take-dt-quick", "title": "得来速", "subtitle": "车道自提"},
    ],
}

# available-coupons 真实快照（麦麦省可领券列表）
SAMPLE_AVAILABLE_COUPONS = [
    {"couponName": "麦旋风任选", "couponStatus": "HAVING_RECEIVE", "label": "已领取"},
    {"couponName": "巧克力味厚松饼猪柳蛋套餐", "couponStatus": "HAVING_RECEIVE", "label": "已领取"},
    {"couponName": "薯薯任选", "couponStatus": "HAVING_RECEIVE", "label": "已领取"},
    {"couponName": "免费脆薯饼", "couponStatus": "CAN_GET", "label": "可领取"},
    {"couponName": "人气麦旋风买一送一", "couponStatus": "CAN_GET", "label": "可领取"},
    {"couponName": "9.9元中杯冰美式", "couponStatus": "CAN_GET", "label": "可领取"},
]

# query-my-coupons 真实返回要点（2026-10-09）：每张券含用券价格、有效期（精确到日期+时段，
# 如早餐券仅 05:00-10:29 可用）、标签（到店专用/外送专用/今日到期）。
# 以下为 price_planner 演示用的归一化规则，由 AI 阅读券面文字后映射生成，
# 并非 MCP 直接返回的结构；真实核销以 calculate-price 为准
SAMPLE_COUPON_RULES = [
    {"id": "MC001", "title": "火腿扒堡早餐两件套 9.9 元(仅 05:00-10:29, 到店专用)",
     "type": "fixed_price", "item_code": "BF2SET", "price": 9.9},
    {"id": "MC002", "title": "满 30 减 5", "type": "amount_off", "threshold": 30.0, "amount": 5.0},
    {"id": "MC003", "title": "早餐 8.8 折(封顶减 6 元)", "type": "percent_off", "rate": 0.88, "cap": 6.0},
]

# order-list 真实结构（data.list[]）；首条为该账号真实历史订单快照，
# 其余为同结构演示数据。createTime 格式 yyyy-MM-dd HH:mm:ss，realTotalAmount 单位为元
SAMPLE_ORDERS = [
    {
        "orderId": "1030323350000566142884684927",
        "orderType": "1",
        "createTime": "2025-11-04 18:12:22",
        "beType": "1",
        "beCode": "",
        "storeCode": "3330137",
        "storeName": "麦当劳杭州滨江星耀城2期餐厅",
        "orderStatus": "订单已完成",
        "orderProductList": [
            {"productCode": "4810", "productName": "中薯条", "quantity": 1, "comboItemList": []},
        ],
        "realTotalAmount": "6",
    },
    {
        "orderId": "DEMO0001",
        "orderType": "1",
        "createTime": "2026-09-15 08:05:11",
        "beType": "5",
        "beCode": "145048541",
        "storeCode": "1450485",
        "storeName": "上海老沪闵路得来速餐厅",
        "orderStatus": "订单已完成",
        "orderProductList": [
            {"productCode": "5022", "productName": "猪柳蛋麦满分", "quantity": 1, "comboItemList": []},
            {"productCode": "514851", "productName": "咖啡阿芙佳朵", "quantity": 1, "comboItemList": []},
        ],
        "realTotalAmount": "33",
    },
    {
        "orderId": "DEMO0002",
        "orderType": "1",
        "createTime": "2026-09-18 08:10:42",
        "beType": "5",
        "beCode": "145048541",
        "storeCode": "1450485",
        "storeName": "上海老沪闵路得来速餐厅",
        "orderStatus": "订单已完成",
        "orderProductList": [
            {"productCode": "5022", "productName": "猪柳蛋麦满分", "quantity": 1, "comboItemList": []},
            {"productCode": "514851", "productName": "咖啡阿芙佳朵", "quantity": 1, "comboItemList": []},
        ],
        "realTotalAmount": "33",
    },
    {
        "orderId": "DEMO0003",
        "orderType": "1",
        "createTime": "2026-09-29 08:02:37",
        "beType": "5",
        "beCode": "145048541",
        "storeCode": "1450485",
        "storeName": "上海老沪闵路得来速餐厅",
        "orderStatus": "订单已完成",
        "orderProductList": [
            {"productCode": "5022", "productName": "猪柳蛋麦满分", "quantity": 1, "comboItemList": []},
            {"productCode": "514851", "productName": "咖啡阿芙佳朵", "quantity": 1, "comboItemList": []},
        ],
        "realTotalAmount": "33",
    },
]
