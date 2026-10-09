# MCP 集成说明：通勤得来速管家

## 使用的 MCP Server

- **Server**：麦当劳 MCP Server（`https://mcp.mcd.cn`，streamablehttp 协议）
- **认证**：请求头 `Authorization: Bearer $MCD_MCP_TOKEN`，Token 仅从环境变量读取
- 本文枚举与字段已于 2026-10-09 用真实 Token 联调验证

## 已验证的枚举语义

| 枚举 | 取值与含义 |
| --- | --- |
| `beType` | `1`=到店取餐，`2`=麦乐送到家，`5`=得来速(DT)，`6`=企业团餐 |
| `orderType` | `1`=到店（含到店自取 + 得来速车道取餐），`2`=外送（含麦乐送 + 企业团餐） |
| 得来速固定搭配 | `beType=5` + `orderType=1` + `beCode` 必传（来自 query-nearby-stores） |
| `reservationDate` | 预约场景必传，格式 `yyyy-MM-dd HH:mm`；时刻须落在门店 `reservationTimeOptions` 对应日期的时段窗口内 |
| `takeWayCode` | create-order 专用，取自 calculate-price 返回的 `takeWayList`（得来速实测 `take-dt-quick` = 车道自提） |
| 金额单位 | query-meals 的 `currentPrice`/`originalPrice` 为**元**（字符串）；calculate-price 全部金额字段为**分** |

## 使用的 Tool 清单

| Tool | 用途 | 在本项目中的角色 |
| --- | --- | --- |
| `now-time-info` | 获取当前时间信息 | 为时间倒推脚本提供基准（`data.formatted`/`data.date`） |
| `query-nearby-stores` | 查询附近可用门店 | `beType=5` 直达得来速门店列表；`searchType=2` 城市+关键词搜索，`searchType=1` 收藏餐厅；返回 storeCode/beCode/distance(米)/businessStatus/reservation/reservationTimeOptions |
| `query-meals` | 查询当前可售卖餐品列表 | 得来速预约场景传 `beType=5, orderType=1, reservationDate`；菜单随预约时段自动切换（早餐/正餐） |
| `query-meal-detail` | 查询餐品详情 | 确认套餐 rounds/choices 默认搭配（isDefault=1）与特制 selectedKey/unselectedKey 传参规则 |
| `order-list` | 查询历史订单 | 无入参；`data.list[]` 交给 `order_learner.py` 学习"老样子"（createTime/orderProductList/realTotalAmount） |
| `available-coupons` | 麦麦省券列表查询 | 领券前展示（couponStatus：CAN_GET 可领取 / HAVING_RECEIVE 已领取） |
| `auto-bind-coupons` | 麦麦省一键领券 | **消耗性操作**，用户确认后一键领取 |
| `query-my-coupons` | 我的优惠券查询 | 领券后核对；注意券面时段限制（如早餐券 05:00-10:29）与"到店专用/外送专用"标签 |
| `calculate-price` | 商品价格计算 | 只读权威核价，金额为分；返回 takeWayList 供 create-order 回传 takeWayCode |
| `create-order` | 创建订单 | **消耗性操作**，用户确认后创建得来速预约单（takeWayCode + reservationDate + remark） |
| `query-order` | 查询订单详情 | 下单后跟踪订单状态 |
| `cancel-order` | 取消订单 | **消耗性操作**，二次确认后取消 |
| `campaign-calendar` | 活动日历查询 | 可选增益：向用户顺带提示当月早餐相关活动 |

## 调用流程

```
用户：「8:40 到公司，路上吃老样子」
        │
        ▼
① now-time-info ─────────────────────────► 当前时间/日期
        │
        ▼
② scripts/time_planner.py（确定性脚本）
   输入：到公司时间/路程估计/当前时间/日期
   输出：reservation_date(yyyy-MM-dd HH:mm)、出门时间、菜单时段、预警
        │
        ▼
③ query-nearby-stores {beType:5, searchType:2, city, keyword}
   ───────────────────────────────────────► 沿途得来速门店 + 预约时段窗口
        │（AI 补估 detour_minutes）
        ▼
④ scripts/store_ranker.py（确定性脚本）
   输出：打分排序 + 推荐理由 ──► 用户选定门店（拿 storeCode/beCode）
        │
        ▼
⑤ order-list → scripts/order_learner.py 识别"老样子"
   或 query-meals/query-meal-detail（带 reservationDate）手动选品
        │
        ▼
⑥ 【门控】available-coupons 展示 → 用户同意 → auto-bind-coupons
   query-my-coupons 核对（排除时段/场景不匹配的券）
        │
        ▼
⑦ scripts/price_planner.py 预筛最优券
   → calculate-price 权威核价（金额单位：分；拿 takeWayList）
        │
        ▼
⑧ 展示完整方案（门店/餐品/金额/预约取餐时间/出门时间）
        │
        ▼
⑨ 【门控】用户明确确认 → create-order
   （beType=5, orderType=1, beCode, reservationDate, takeWayCode, items, remark?）
        │
        ▼
⑩ 展示订单与取餐信息；后续 query-order 跟踪，cancel-order 需二次确认
```

## 业务价值

1. **差异化的工具组合**：把「得来速车道取餐 + 全场景预约」这条链路串成通勤场景的一站式流程——`beType=5` 找店、`reservationDate` 预约、`takeWayCode=take-dt-quick` 车道自提，而不是单点调用。
2. **确定性护航**：时间倒推、门店打分、券比价、订单统计全部落在零依赖 Python 脚本里，LLM 只编排不口算，杜绝"算错上班时间""报错价格"这类体验事故。
3. **安全可控**：领券、下单、取消三类消耗性操作均有显式确认门控；calculate-price 只读核价先行，金额以其权威返回为准，符合 MCP 服务规则对交易类调用的谨慎要求。
4. **越用越懂你**：`order-list` 历史订单沉淀为"老样子"画像，复购场景一句话搞定，凸显 MCP 数据联通的长期价值。
