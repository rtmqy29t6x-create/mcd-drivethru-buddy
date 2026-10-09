---
name: mcd-drivethru-buddy
description: 通勤得来速管家。当用户想在开车通勤途中顺路用麦当劳得来速（Drive-Thru）预约点餐、到店免下车取餐时使用。覆盖"沿途找得来速门店 → 算取餐时间 → 选早餐/正餐 → 领券核价 → 确认下单 → 拿取餐码"全流程，支持从 order-list 历史订单学习"老样子"。涉及领券、下单、取消等消耗性操作前必须获得用户明确确认。
---

# 通勤得来速管家

帮助开车通勤的用户：上班路上顺路经过麦当劳得来速门店，提前预约下单，到点摇下车窗取餐就走。

## 前置条件

- 麦当劳 MCP Server：`https://mcp.mcd.cn`（streamablehttp），请求头 `Authorization: Bearer $MCD_MCP_TOKEN`。
- Token 从环境变量 `MCD_MCP_TOKEN` 读取，**严禁**把真实 Token 写进任何文件或对话记录。
- **无 Token 时进入 dry-run 模式**：不要调用 MCP，改用 `scripts/sample_data.py` 中的真实结构快照（2026-10-09 采集）演示完整流程，并在开场明确告知用户"当前为演示模式"。

## 已联调确认的枚举与字段（务必照此传参）

- **beType**：`1`=到店取餐，`2`=麦乐送到家，`5`=得来速(DT)，`6`=企业团餐。
- **orderType**：`1`=到店（含到店自取 + 得来速车道取餐），`2`=外送（含麦乐送 + 企业团餐）。
- **得来速场景固定搭配**：`beType=5 + orderType=1 + beCode 必传`（beCode 来自 query-nearby-stores）。到店自取(beType=1) 时**不要传 beCode**（传了会报错）。
- **预约**：`reservationDate` 必传，格式 `yyyy-MM-dd HH:mm`（如 `2026-10-10 08:10`），且预约时刻必须落在该店 `reservationTimeOptions` 对应日期的时段窗口内（如"早餐(07:14至10:15)"）。传窗口文本会报 `600052 预约时间格式错误`。
- **金额单位**：query-meals 的 `currentPrice`/`originalPrice` 单位为**元**（字符串）；calculate-price 返回的所有金额字段（price/originalPrice/discount/subtotal 等）单位为**分**，展示时除以 100。
- **取餐方式**：calculate-price 返回 `takeWayList`（得来速店实测为 `{code:"take-dt-quick", title:"得来速", subtitle:"车道自提"}`），create-order 需回传 `takeWayCode`。

## 铁律：确认门控

以下操作属于消耗性操作，**严禁静默执行**，必须在向用户展示完整方案明细（门店、餐品、数量、金额、取餐时间）并得到明确"确认/可以/下单"类答复后才能调用：

| 操作 | MCP 工具 | 门控要求 |
| --- | --- | --- |
| 一键领券 | `auto-bind-coupons` | 告知将领取全部可领券，用户同意后再调用 |
| 创建订单 | `create-order` | 展示核价结果与取餐时间，用户确认后调用；每次确认仅下单一次 |
| 取消订单 | `cancel-order` | 二次确认"确定取消订单 X？"后调用 |
| 积分抽奖 | `draw-lottery` | 仅当用户主动提出；展示消耗与奖池后确认（本场景一般不主动引导） |

查询类工具（门店、菜单、核价、历史订单、时间）可自由调用，无需确认。calculate-price 为只读核价，不产生订单。

## 标准工作流程

### 第 1 步：收集需求

向用户确认三件事（可一次问完）：
1. 通勤城市与沿途关键词（用于 `query-nearby-stores` 的 `city`/`keyword`）。
2. 时间：预计几点到公司（或"X 分钟后出门"）。
3. 吃什么：具体餐品，或"老样子"。

### 第 2 步：计算时间窗（必须用脚本，禁止口算）

调用 `now-time-info` 获取当前时间（`data.formatted` / `data.date`），然后运行：

```bash
echo '{"arrive_company_at":"08:40","home_to_store_minutes":18,"store_to_company_minutes":12,"buffer_minutes":15,"now":"07:30","date":"2026-10-10"}' \
  | python3 scripts/time_planner.py
```

- `home_to_store_minutes` / `store_to_company_minutes` 按用户口述的路程估计，不确定就问。
- 从输出取 `reservation_date`（直接就是 MCP 的 reservationDate 入参格式）、`leave_home_at`（出门时间）、`menu_period`（breakfast/regular）。
- 门店预约早餐窗口常见截止 10:15（各店以 `reservationTimeOptions` 为准），脚本判断的是菜单大时段（默认 10:30），**精确窗口必须从门店数据核对**。
- `warnings` 非空时（如"已来不及"），必须如实告知用户并协商调整，不得硬排。

### 第 3 步：沿途门店打分（必须用脚本）

调用 `query-nearby-stores`，得来速场景固定 `beType=5`（返回的全是得来速餐厅）：

```json
{"beType": 5, "searchType": 2, "city": "上海市", "keyword": "漕河泾"}
```

- `searchType=1` 查收藏餐厅，`searchType=2` 按城市+关键词搜索。
- 返回字段：`storeCode`、`beCode`、`storeName`、`address`、`distance`（**单位米**）、`businessStatus`、`businessStartTime/EndTime`、`reservation`、`reservationTimeOptions`（按日期给出"早餐(07:14至10:15)，午餐(10:44至14:15)…"窗口文本，**逐条完整展示，不得省略**）。
- 为每家店补估 `detour_minutes`（绕行成本，向用户确认或按经验估值，MCP 不返回该字段），然后：

```bash
echo '{"stores":[...MCP返回的门店(已补detour_minutes)...]}' | python3 scripts/store_ranker.py
```

取 `recommended` 作为首选；把前 2 名及各自 `reasons` 展示给用户选择。默认硬过滤未营业（`businessStatus=false`）和不支持预约（`reservation=false`）的门店。

### 第 4 步：确认餐品

- 用户说"老样子"：调用 `order-list`（无入参），把 `data.list` 交给脚本学习：

```bash
echo '{"orders":[...data.list...]}' | python3 scripts/order_learner.py
```

用 `usual_combo`（productCode + productName + quantity）复述给用户确认（"还是猪柳蛋麦满分+咖啡阿芙佳朵？"）。
- 否则：调用 `query-meals` 选品：

```json
{"storeCode": "1450485", "beCode": "145048541", "beType": 5, "orderType": 1, "reservationDate": "2026-10-10 08:10"}
```

  - 预约场景 `reservationDate` 必传；菜单随预约时段变化（早餐时段返回"麦满分系列/粥王系列"等早餐分类，正餐时段返回汉堡正餐分类），无需自己过滤时段。
  - 返回 `categories[].meals[].code` + `meals` 映射表（`name`、`currentPrice`(元)、`originalPrice`(元)、`discountType`、`tags`）及 `frequent` 常点餐品。
- 选定后用 `query-meal-detail`（入参 `{storeCode, beCode, beType, orderType, code, reservationDate?}`）确认套餐组成：`rounds[].choices[]` 中 `isDefault=1` 为默认搭配；用户要换配时按 diffPrice 说明差价。特制（modification）选项用户不问不展开；若用户改了特制，`selectedKey`/`unselectedKey` 规则严格按工具描述传给 calculate-price/create-order。

### 第 5 步：领券与核价

1. 先用 `available-coupons` 看麦麦省可领券（`couponStatus`：`CAN_GET`=可领取，`HAVING_RECEIVE`=已领取），询问"需要我一键领取当前可领的券吗？"→ 用户同意后调用 `auto-bind-coupons`（确认门控）。
2. 用 `query-my-coupons` 核对账户券。注意券面限制：**有效期精确到日期+时段**（如早餐两件套券仅 05:00-10:29 可用）、**标签区分"到店专用/外送专用"**，得来速属于到店场景；与取餐时间冲突的券直接排除。
3. 把适用券映射为规则后跑本地预估：

```bash
echo '{"items":[{"code":"5022","name":"猪柳蛋麦满分","price":18.0,"quantity":1}],"coupons":[...]}' \
  | python3 scripts/price_planner.py
```

4. 以脚本预估的 `best` 方案调用 `calculate-price` 做权威核价（入参同 query-meals，加 `items[{productCode, quantity, couponId?}]` 与 `needTableware`）。**返回金额单位为分**；脚本结果只是预估，金额一律以 calculate-price 返回为准。同时记下返回的 `takeWayList`（第 6 步要用）。

### 第 6 步：确认下单与交付

1. 向用户输出完整方案卡片：门店（storeName + address）、取餐方式（得来速车道自提）、预约取餐时间（reservationDate）、餐品明细、用券、应付金额（分÷100 转元）、出门时间提醒。
2. 用户明确确认后，调用 `create-order`：参数同 calculate-price，另带 `takeWayCode`（取 calculate-price 返回的 takeWayList 中"得来速"项的 code，实测为 `take-dt-quick`）、`reservationDate`，可选 `remark`。
3. 展示订单详情与取餐信息，提醒用户按 `leave_home_at` 出门，到车道报取餐信息即可。
4. 用户后续查进度用 `query-order`；取消按确认门控走 `cancel-order`。

## 错误处理

- 401：提示用户检查 `MCD_MCP_TOKEN` 是否配置或已过期，不重复重试。
- 429：每分钟 600 次限流，放慢节奏，合并查询，稍后再试。
- 600052：reservationDate 格式错误，应为 `yyyy-MM-dd HH:mm`。
- 600057：门店已关闭或不在营业时间——检查 `businessStatus`/营业时段，或 orderType 与 beType 搭配错误（得来速必须是 orderType=1）。
- 工具返回与预期字段不符：以真实返回为准调整，不要臆造字段。

## 边界说明

- 本 Skill 不估计实时路况，`detour_minutes` 与路程时间来自用户口述或经验值，脚本只做确定性算术。
- 券规则（互斥、门槛、时段、到店/外送限制）以券面与 `calculate-price` 为准，`price_planner.py` 仅为预筛选，其输入规则由 AI 阅读券面文字后映射生成。
- 项目输出仅供参考，餐品、价格、供应状态以麦当劳官方渠道实时结果为准。
