# Rover

Verbatim cell values from `Perf Log Process & Fields Standardization (1).xlsx`. The row number and column letters point to the original workbook; blank cells are left blank. Formulas are retained as formulas. The workbook contains draft, conflicting and deprecated entries; do not assume every row is deployed.

| Row | A | B | C | D | E |
| ---: | --- | --- | --- | --- | --- |
| 1 | Request | Key | Comment | Value | Required/Optional |
| 2 |  |  | Include all common field in the first sheet |  |  |
| 3 | Common |  |  |  |  |
| 4 |  | user_open_id | User unique id for one mini program | string | Optional |
| 5 |  | user_union_id | User unique id for one supplier | string | Optional |
| 6 |  | echo_token | unique token for RQ and RS | string | Optional |
| 7 |  | duration_details |  |  | Optional |
| 8 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |
| 9 |  | process_result | Success or Fail | string | Required |
| 10 |  | supplier_account_id | Supplier account id | string | Required |
| 12 | Hotel |  |  |  |  |
| 13 |  | process | HotelInfo | string | Required |
| 14 |  | hotel_code | hotel code | string, upper case | Required |
| 15 |  | currency | currency code | string,uppercase | Optional |
| 16 |  | supplier | derby supplier code,eg: MELIA, MO | string,upper case | Optional |
| 18 | Authentication |  |  |  |  |
| 19 |  | process | GetAccessToken |  |  |
| 21 | Marketing |  |  |  |  |
| 22 |  | process | ListAdvertises/GetCampaign |  |  |
| 24 | Login/User |  |  |  |  |
| 25 |  | process | process type | WechatLogin, UserBind | Required |
| 26 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 27 |  | process_result | process result, Fail or success | String | Required |
| 28 |  | user_id | request user id if need sign on | String | Optional |
| 29 |  | user_union_id | request user union id if need sign on | String | Optional |
| 30 |  | member_tier | Normal,Member | MUST BE：Normal,Member | Optional |
| 31 |  | user_ip | request user ip | String | Optional |
