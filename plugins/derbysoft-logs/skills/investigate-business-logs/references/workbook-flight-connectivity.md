# Flight Connectivity

Verbatim cell values from `Perf Log Process & Fields Standardization (1).xlsx`. The row number and column letters point to the original workbook; blank cells are left blank. Formulas are retained as formulas. The workbook contains draft, conflicting and deprecated entries; do not assume every row is deployed.

| Row | A | B | C | D | E | F | G |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | Request |  | Key | Comment | Value | example | Required/Optional |
| 2 | - |  | err_code_supplier | supplier error code | String | 09002 | Optional |
| 3 |  |  | err_msg_supplier | supplier error code and message, max 1000 | String | Token not found in cache, please contact administrator | Optional |
| 4 |  |  | api_version | A common attribute, 记录当前请求对应的API版本 | String | V1.0/V1.1/V1.2 | Required |
| 5 | AirShopping | RQ | process | AirShopping/OrderReShop | String | AirShopping | Required |
| 6 |  |  | echo_token | 请求链路Key | String |  | Optional |
| 7 |  |  | onward_origin | 去程出发地 | String | KUL | Required |
| 8 |  |  | onward_destination | 去程目的地 | String | CGK | Required |
| 9 |  |  | return_origin | 回程出发地 | String | CGK | Required |
| 10 |  |  | return_destination | 回程目的地 | String | KUL | Required |
| 11 |  |  | seller_code | OTA账号 | String | PKAIR | Required |
| 12 |  |  | supplier_group | 供应组 | String | WANO | Optional |
| 13 |  |  | account_code | OTA 供应侧账号 | String | BF0001-HKG-PKFARE-USD | Required |
| 14 |  |  | airline_code | 航司 | String | FD | Optional |
| 15 |  |  | outbound_date | 去程出发地起飞日期 | String | 2025-12-01 | Required |
| 16 |  |  | inbound_date | 回程出发地起飞日期 | String | 2026-01-01 | Optional |
| 17 |  |  | los | 逗留时间（往返程时间计算待几天） | Number | 12 | Optional |
| 18 |  |  | gdn_order_id | gdn订单id,process=OrderReshop | String | 9180691730607782 | Optional |
| 19 |  |  | supplier_order_id | 供应订单id,process=OrderReshop | String | 917645756852229501 | Optional |
| 20 |  |  | cabin_class | 舱等 | String | First_Class<br>Business_Class<br>Premium_Economy<br>Economy | Required |
| 21 |  |  | currency | 币种 | String | USD | Optional |
| 22 |  |  | adult_cnt | 成人数量 | Number | 1 | Required |
| 23 |  |  | children_cnt | 儿童数量 | Number | 1 | Required |
| 24 |  |  | infant_cnt | 婴儿数量 | Number | 0 | Required |
| 25 |  |  | flight_type | 航线类型 | String | Direct/Connect/Through | Optional |
| 26 |  |  | itinerary_type | 行程类型 | String | OW/RT/OJ/MT | Required |
| 27 |  |  | advance_day | 提前购买天数（ 去程出发地起飞日期 - 出发地当前日期） | Number | 3 | Required |
| 28 |  |  | scenario_correlation_id | A unique identifier used to link multiple related requests, events, or logs that belong to the same business scenario or end-to-end business flow. | String |  | Required |
| 29 |  | RS | err_code | 错误码 | String | 01001 | Optional |
| 30 |  |  | err_msg | 错误信息 | String | Supplier shopping request error | Optional |
| 31 |  |  | offer_from | 报价来源 | String | api/cache/others | Optional |
| 32 |  |  | solution_cnt | solution数量 | Number | 500 | Required |
| 33 |  |  | carrier_supplier_offer_cnt | 航司返回的航线结果报价数量, max size 1024 | Array String | [9C_WANO:300,FR_WANO:500] | Optional |
| 34 |  |  | carrier_supplier_solution_cnt | 航司返回的航线结果数量, max size 1024 | Array String | [9C_WANO:300,FR_WANO:500] | Optional |
| 35 |  |  | carrier_supplier_filter_offer_cnt | 航司返回的航线结果过滤的报价数量,Max array size 1024 | Array String | [9C_WANO_FLIGHT_TYPE:10, 9C_WANO_CARRIER:10, 9C_WANO_SUPPLIER:10] | Optional |
| 36 |  |  | carrier_supplier_filter_solution_cnt | 航司返回的航线过滤的结果数量, Max array size 1024 | Array String | [9C_WANO_FLIGHT_TYPE:10, 9C_WANO_CARRIER:10, 9C_WANO_SUPPLIER:10] | Optional |
| 37 | OfferPrice | RQ | process |  | String | OfferPrice | Required |
| 38 |  |  | echo_token | 请求链路Key | String | 277610630433445351 | Optional |
| 39 |  |  | onward_origin | 去程出发地 | String | KUL | Required |
| 40 |  |  | onward_destination | 去程目的地 | String | CGK | Required |
| 41 |  |  | return_origin | 回程出发地 | String | CGK | Required |
| 42 |  |  | return_destination | 回程目的地 | String | KUL | Required |
| 43 |  |  | seller_code | OTA账号 | String | PKAIR | Required |
| 44 |  |  | outbound_date | 去程出发时间 | String | 2025-12-01 | Required |
| 45 |  |  | inbound_date | 回程出发时间 | String | 2026-01-01 | Optional |
| 46 |  |  | supplier_group | 供应组 | String | WANO | Optional |
| 47 |  |  | account_code | OTA 供应侧账号 | String | BF0001-HKG-PKFARE-USD | Required |
| 48 |  |  | brand_fare_name | 品牌报价名称 | String | Corporate Premium Flex | Required |
| 49 |  |  | cabin_class | 舱等 | String |  First Class/Business Class/Premium EconomyEconomy | Required |
| 50 |  |  | segment_cnt | 航段数 | Number | 3 | Required |
| 51 |  |  | onward_airline_codes | 去程航司二字码集合 | Array String | [AK,D7] | Required |
| 52 |  |  | return_airline_codes | 回程航司二字码集合 | Array String | [D7] | Optional |
| 53 |  |  | booking_codes | 舱位集合 | Array String | [K,L,M,T] | Required |
| 54 |  |  | los | 逗留时间（往返程时间计算待几天） | Array | 12 | Required |
| 55 |  |  | direct_flag | 是否直接验价 | String | MUST BE: true, false | Required |
| 56 |  |  | plating_carrier | 开票航司 | String | FD | Required |
| 57 |  |  | operating_carrier | 承运航司 | String | FD | Required |
| 58 |  |  | marketing_carrier | 销售航司 | String | AK | Required |
| 59 |  |  | main_carrier | 主航司 | String | FD | Required |
| 60 |  |  | flight_numbers | 航班号集合 | Array String | [AK5432,FD123] | Required |
| 61 |  |  | flight_type | 航线类型 | String | Direct/Connect/Through | Required |
| 62 |  |  | itinerary_type | 行程类型 | String | OW/RT/OJ/MT | Optional |
| 63 |  |  | advance_day | 提前购买天数（ 去程出发地起飞日期 - 出发地当前日期） | Number | 3 | Required |
| 64 |  |  | offer_from | 报价来源 | String | api/cache/others | Optional |
| 65 |  |  | offer_id | 机票报价id | String | T2XcxBrxMcDJF4CTZbQTO1UxpmsD8spzCJAyfj6U2Kmrfdujm1ci9yoUrmBEGmyF92FhXavbQrJ/9q6eGDunzJBKc0zrsXANPrLZ9qkV9pApuYQBZZ3T1cG5swr2HuPyGtpx8xQh4nMVQ2n4TeyMe3nMcmTLVQHT2NnnVqn2NjpVnWX+3HG0RP/RooC640PeQ7vuTnEBOnCHmOSn29hLdJHs7lxvU3U2Oe/WXsq7T5T8Id08oQvd+kqfIgSt8irISmaIU0pzWPQ1/BHBBh0SjPa3dDxgd0nSVRMdrq296qr1IHRCyFoQZPebnfJKhSnRTeXBnPMlYPKF5zSfud2HROVV6vzaPDYStuMUcr+qMhV9gHtYjvay9Bg3E9Unia25shYuZSmKnetS/JvhJL0WrgsWCM+mJIdzj0ViWf+uUekDLExJzF5257p7cV8IEHZFVhIsUZSN7AkmG1ecvvZTbEQhi+ENL+LdaMXhUkokK0UD7JvCS7q3VljxxwoJCG8fC0r7xZN0V4wE+SauRFIBWeHfEzw7gHkzG49V7ZUlillcKBZQIJKYVupraQuLcqe7 | Required |
| 66 |  |  | currency | 币种 | String | 采用 ISO 4217 的币种编码，如 USD, CNY | Optional |
| 67 |  |  | onward_origin_country | 去程出发地国家（地区） | String | 采用 ISO 3166-1 的国家编码标准，采用2字码，如 JP, CN | Required |
| 68 |  |  | return_origin_country | 回程出发地国家（地区） | String | 采用 ISO 3166-1 的国家编码标准，采用2字码，如 JP, CN | Optional |
| 69 |  |  | scenario_correlation_id | A unique identifier used to link multiple related requests, events, or logs that belong to the same business scenario or end-to-end business flow. | String |  | Required |
| 70 |  | RS | err_code | 错误码 | String | 打印技术架构的错误 | Optional |
| 71 |  |  | err_msg | 错误信息 | String | Supplier shopping request error | Optional |
| 72 |  |  | round_trip_split_flag | 是否经历往返差单程 | String | MUST BE: true,false | Required |
| 73 |  |  | adult_base_amount | 成人基础价格 | Number | 877.140 | Optional |
| 74 |  |  | adult_service_fee_amount | 成人服务费价格 | Number | 0.00 | Optional |
| 75 |  |  | children_base_amount | 儿童基础价格 | Number | 877.140 | Optional |
| 76 |  |  | children_service_fee_amount | 儿童服务费价格 | Number | 0.00 | Optional |
| 77 |  |  | infant_base_amount | 婴儿基础价格 | Number | 877.140 | Optional |
| 78 |  |  | infant_service_fee_amount | 婴儿服务费价格 | Number | 0.00 | Optional |
| 79 |  |  | tax_total_amount | 税费总额 | Number | 57.590 | Required |
| 80 |  |  | adult_tax_amount | 成人税费 | Number | 35.040 | Optional |
| 81 |  |  | adult_tax_code_list | 成人税费代码集合 | Array String | [Airport Tax, Japan Tourist Tax] | Optional |
| 82 |  |  | adult_tax_amount_list | 成人税费价格明细集合 | Array String | [27.47, 7.47] | Optional |
| 83 |  |  | children_tax_amount | 儿童税费 | Number | 22.550 | Optional |
| 84 |  |  | children_tax_code_list | 儿童税费代码集合 | Array String | [Airport Tax] | Optional |
| 85 |  |  | children_tax_amount_list | 儿童税费价格明细集合 | Array String | [22.550] | Optional |
| 86 |  |  | infant_tax_amount | 婴儿税费 | Number | 22.550 | Optional |
| 87 |  |  | infant_tax_code_list | 婴儿税费代码集合 | Array String | [Airport Tax] | Optional |
| 88 |  |  | infant_tax_amount_list | 婴儿税费价格明细集合 | Array String | [22.550] | Optional |
| 89 |  |  | available_cnt | 可选座位数量 | Number |  | Required |
| 90 |  |  | price_change | shopping报价与offerprice验价的价格的变化情况 | Enum | -1 (价格降低), 0（价格不变）,1（价格升高） | Optional |
| 91 | ServiceList | RQ | process |  | String | ServiceList | Required |
| 92 |  |  | echo_token | 请求链路Key | String | 277610630433445351 | Optional |
| 93 |  |  | onward_origin | 去程出发地 | String | KUL | Required |
| 94 |  |  | onward_destination | 去程目的地 | String | CGK | Required |
| 95 |  |  | return_origin | 回程出发地 | String | CGK | Required |
| 96 |  |  | return_destination | 回程目的地 | String | KUL | Required |
| 97 |  |  | seller_code | OTA账号 | String | PKAIR | Required |
| 98 |  |  | onward_airline_codes | 去程航司二字码 | Array String | [AK,D7] | Required |
| 99 |  |  | return_airline_codes | 回程航司二字码集合 | Array String | [D7] | Optional |
| 100 |  |  | supplier_group | 供应组 | String | WANO | Optional |
| 101 |  |  | account_code | OTA 供应侧账号 | String | BF0001-HKG-PKFARE-USD | Required |
| 102 |  |  | offer_id | 机票报价id | String | T2XcxBrxMcDJF4CTZbQTO1UxpmsD8spzCJAyfj6U2Kmrfdujm1ci9yoUrmBEGmyF92FhXavbQrJ/9q6eGDunzJBKc0zrsXANPrLZ9qkV9pApuYQBZZ3T1cG5swr2HuPyGtpx8xQh4nMVQ2n4TeyMe3nMcmTLVQHT2NnnVqn2NjpVnWX+3HG0RP/RooC640PeQ7vuTnEBOnCHmOSn29hLdJHs7lxvU3U2Oe/WXsq7T5T8Id08oQvd+kqfIgSt8irISmaIU0pzWPQ1/BHBBh0SjPa3dDxgd0nSVRMdrq296qr1IHRCyFoQZPebnfJKhSnRTeXBnPMlYPKF5zSfud2HROVV6vzaPDYStuMUcr+qMhV9gHtYjvay9Bg3E9Unia25shYuZSmKnetS/JvhJL0WrgsWCM+mJIdzj0ViWf+uUekDLExJzF5257p7cV8IEHZFVhIsUZSN7AkmG1ecvvZTbEQhi+ENL+LdaMXhUkokK0UD7JvCS7q3VljxxwoJCG8fC0r7xZN0V4wE+SauRFIBWeHfEzw7gHkzG49V7ZUlillcKBZQIJKYVupraQuLcqe7 | Optional |
| 103 |  |  | supplier_order_id | 供应订单id | String | 917645757182234601 | Optional |
| 104 |  |  | gdn_order_id | gdn订单id | String | 9180691730607782 | Optional |
| 105 |  |  | scenario_correlation_id | A unique identifier used to link multiple related requests, events, or logs that belong to the same business scenario or end-to-end business flow. | String |  | Required |
| 106 |  | RS | err_code | 错误码 | String | 01001 | Optional |
| 107 |  |  | err_msg | 错误信息 | String | Supplier shopping request error | Optional |
| 108 |  |  | onward_meal_cnt | 餐食数量 | Number | 5 | Required |
| 109 |  |  | onward_special_assistance_cnt | 特殊协助数量 | Number | 0 | Required |
| 110 |  |  | onward_sport_equipment_cnt | 体育用品数量 | Number | 0 | Required |
| 111 |  |  | onward_baggage_cnt | 行李数量 | Number | 5 | Required |
| 112 |  |  | return_meal_cnt | 餐食数量 | Number | 5 | Optional |
| 113 |  |  | return_special_assistance_cnt | 特殊协助数量 | Number | 0 | Optional |
| 114 |  |  | return_sport_equipment_cnt | 体育用品数量 | Number | 0 | Optional |
| 115 |  |  | return_baggage_cnt | 行李数量 | Number | 5 | Optional |
| 116 | SeatAvailability | RQ | process |  | String | SeatAvailability | Required |
| 117 |  |  | echo_token | 请求链路Key | String | 277610630433445351 | Optional |
| 118 |  |  | onward_origin | 去程出发地 | String | KUL | Required |
| 119 |  |  | onward_destination | 去程目的地 | String | CGK | Required |
| 120 |  |  | return_origin | 回程出发地 | String | CGK | Required |
| 121 |  |  | return_destination | 回程目的地 | String | KUL | Required |
| 122 |  |  | seller_code | OTA账号 | String | PKAIR | Required |
| 123 |  |  | onward_airline_codes | 去程航司二字码 | Array String | [AK,D7] | Required |
| 124 |  |  | return_airline_codes | 回程航司二字码集合 | Array String | [D7] | Optional |
| 125 |  |  | supplier_group | 供应组 | String | WANO | Optional |
| 126 |  |  | account_code | OTA 供应侧账号 | String | BF0001-HKG-PKFARE-USD | Required |
| 127 |  |  | offer_id | 机票报价id | String | T2XcxBrxMcDJF4CTZbQTO1UxpmsD8spzCJAyfj6U2Kmrfdujm1ci9yoUrmBEGmyF92FhXavbQrJ/9q6eGDunzJBKc0zrsXANPrLZ9qkV9pApuYQBZZ3T1cG5swr2HuPyGtpx8xQh4nMVQ2n4TeyMe3nMcmTLVQHT2NnnVqn2NjpVnWX+3HG0RP/RooC640PeQ7vuTnEBOnCHmOSn29hLdJHs7lxvU3U2Oe/WXsq7T5T8Id08oQvd+kqfIgSt8irISmaIU0pzWPQ1/BHBBh0SjPa3dDxgd0nSVRMdrq296qr1IHRCyFoQZPebnfJKhSnRTeXBnPMlYPKF5zSfud2HROVV6vzaPDYStuMUcr+qMhV9gHtYjvay9Bg3E9Unia25shYuZSmKnetS/JvhJL0WrgsWCM+mJIdzj0ViWf+uUekDLExJzF5257p7cV8IEHZFVhIsUZSN7AkmG1ecvvZTbEQhi+ENL+LdaMXhUkokK0UD7JvCS7q3VljxxwoJCG8fC0r7xZN0V4wE+SauRFIBWeHfEzw7gHkzG49V7ZUlillcKBZQIJKYVupraQuLcqe7 | Required |
| 128 |  |  | supplier_order_id | 供应订单id | String | 917645757182234601 | Optional |
| 129 |  |  | gdn_order_id | gdn订单id | String | 9180691730607782 | Optional |
| 130 |  |  | scenario_correlation_id | A unique identifier used to link multiple related requests, events, or logs that belong to the same business scenario or end-to-end business flow. | String |  | Required |
| 131 |  | RS | onward_availability_cnt | 去程座位数量 | Number | 55 | Required |
| 132 |  |  | return_availability_cnt | 回程座位数量 | Number | 33 | Required |
| 133 |  |  | err_code | 错误码 | String | 01001 | Optional |
| 134 |  |  | err_msg | 错误信息 | String | Supplier shopping request error | Optional |
| 135 | Order | RQ | process |  | String | OrderCreate | Required |
| 136 |  |  | onward_origin | 去程出发地 | String | KUL | Optional |
| 137 |  |  | onward_destination | 去程目的地 | String | CGK | Optional |
| 138 |  |  | return_origin | 回程出发地 | String | CGK | Optional |
| 139 |  |  | return_destination | 回程目的地 | String | KUL | Optional |
| 140 |  |  | seller_code | OTA账号 | String | PKAIR | Required |
| 141 |  |  | supplier_group | 供应组 | String | WANO | Optional |
| 142 |  |  | account_code | OTA 供应侧账号 | String | BF0001-HKG-PKFARE-USD | Required |
| 143 |  |  | offer_id | 机票报价id | String | T2XcxBrxMcDJF4CTZbQTO1UxpmsD8spzCJAyfj6U2Kmrfdujm1ci9yoUrmBEGmyF92FhXavbQrJ/9q6eGDunzJBKc0zrsXANPrLZ9qkV9pApuYQBZZ3T1cG5swr2HuPyGtpx8xQh4nMVQ2n4TeyMe3nMcmTLVQHT2NnnVqn2NjpVnWX+3HG0RP/RooC640PeQ7vuTnEBOnCHmOSn29hLdJHs7lxvU3U2Oe/WXsq7T5T8Id08oQvd+kqfIgSt8irISmaIU0pzWPQ1/BHBBh0SjPa3dDxgd0nSVRMdrq296qr1IHRCyFoQZPebnfJKhSnRTeXBnPMlYPKF5zSfud2HROVV6vzaPDYStuMUcr+qMhV9gHtYjvay9Bg3E9Unia25shYuZSmKnetS/JvhJL0WrgsWCM+mJIdzj0ViWf+uUekDLExJzF5257p7cV8IEHZFVhIsUZSN7AkmG1ecvvZTbEQhi+ENL+LdaMXhUkokK0UD7JvCS7q3VljxxwoJCG8fC0r7xZN0V4wE+SauRFIBWeHfEzw7gHkzG49V7ZUlillcKBZQIJKYVupraQuLcqe7 | Optional |
| 144 |  |  | refund_type | 退票类型 | String | voluntary/involuntary | Optional |
| 145 |  |  | refund_estimation_Id | 退票报价的id | String |  | Optional |
| 146 |  |  | gdn_order_id | gdn订单id | String | 9180691730607782 | Required |
| 147 |  |  | supplier_order_id | 供应订单id | String | 917645756852229501 | Required |
| 148 |  |  | onward_airline_codes | 去程航司二字码 | Array String | [AK,D7] | Optional |
| 149 |  |  | return_airline_codes | 回程航司二字码集合 | Array String | [D7] | Optional |
| 150 |  |  | booking_codes | 舱位集合 | Array String | [K,L,M,T] | Required |
| 151 |  |  | payment_amount | 支付金额 | String | 1000.41 | Optional |
| 152 |  |  | payment_currency | 支付币种 | String | USD | Optional |
| 153 |  |  | scenario_correlation_id | A unique identifier used to link multiple related requests, events, or logs that belong to the same business scenario or end-to-end business flow. | String |  | Required |
| 154 |  | RS | supplier_order_id | 供应订单id | String | 917645756852229501 | Optional |
| 155 |  |  | pnrs | PNR集合 | Array String | [ASD123,LSM324] | Required |
| 156 |  |  | err_code | 错误码 | String | 01001 | Optional |
| 157 |  |  | err_msg | 错误信息 | String | Supplier shopping request error | Optional |
| 158 | queryAirShoppingCache | RQ | process | CacheAirShopping | String | CacheAirShopping | Required |
| 159 |  |  | echo_token | 请求链路Key | String |  | Optional |
| 160 |  |  | account_code | OTA 供应侧账号 | String | BF0001-HKG-PKFARE-USD | Required |
| 161 |  |  | onward_origin | 去程出发地 | String | KUL | Required |
| 162 |  |  | onward_destination | 去程目的地 | String | CGK | Required |
| 163 |  |  | return_origin | 回程出发地 | String | CGK | Required |
| 164 |  |  | return_destination | 回程目的地 | String | KUL | Required |
| 165 |  |  | seller_code | OTA账号 | String | PKAIR | Required |
| 166 |  |  | outbound_date | 去程出发地起飞日期 | String | 2025-12-01 | Required |
| 167 |  |  | inbound_date | 回程出发地起飞日期 | String | 2026-01-01 | Optional |
| 168 |  |  | los | 逗留时间（往返程时间计算待几天） | Number | 12 | Optional |
| 169 |  |  | cabin_class | 舱等 | String | First_Class<br>Business_Class<br>Premium_Economy<br>Economy | Required |
| 170 |  |  | currency | 币种 | String | USD | Optional |
| 171 |  |  | adult_cnt | 成人数量 | Number | 1 | Required |
| 172 |  |  | children_cnt | 儿童数量 | Number | 1 | Required |
| 173 |  |  | infant_cnt | 婴儿数量 | Number | 0 | Required |
| 174 |  |  | flight_type | 航线类型 | String | Direct/Connect/Through | Optional |
| 175 |  |  | itinerary_type | 行程类型 | String | OW/RT/OJ/MT | Required |
| 176 |  |  | advance_day | 提前购买天数（ 去程出发地起飞日期 - 出发地当前日期） | Number | 3 | Required |
| 177 |  |  | scenario_correlation_id | A unique identifier used to link multiple related requests, events, or logs that belong to the same business scenario or end-to-end business flow. | String |  | Required |
| 178 |  | RS | err_code | 错误码 | String | 01001 | Optional |
| 179 |  |  | err_msg | 错误信息 | String | Supplier shopping request error | Optional |
| 180 |  |  | offer_from | 报价来源（直接查询api / 缓存未命中再查询api / 缓存命中但根据策略配置不采用再查询api / 主动缓存命中 / 被动缓存命中） | String | direct_api/ cache_miss_api/ cache_skip_api/ active_cache/ passive_cache | Required |
| 181 |  |  | data_from | 报价数据来源（直接查询api / 缓存未命中再查询api / 缓存命中但根据策略配置不采用再查询api / 主动缓存命中 / 被动缓存命中） | String | direct_api/ cache_miss_api/ cache_skip_api/ active_cache/ passive_cache | Required |
| 182 |  |  | min_available_cnt | 所有offer中的可用座位数的最小值 | Number | 1 | Required |
| 183 |  |  | no_price_cache | no_price_cache | true/false | false | Optional |
| 184 |  |  | is_partial | 标记当前缓存报价数据是否经过过滤（目前唯一场景是低座位数过滤，未来可能增加其他情况） | true/false | true/false | Optional |
| 185 |  |  | low_seat_strategy | 低座位缓存策略 | String | return_partial / treat_as_empty | Optional |
| 186 |  |  | low_seat_fallback | 视为无数据策略下 API 失败是否兜底使用部分缓存 | true/false | true/false | Optional |
| 187 |  |  | miss_strategy | 缓存未命中时的处理策略 | String | 30 | Optional |
| 188 |  |  | solution_cnt | solution_cnt | Number | 500 | Required |
