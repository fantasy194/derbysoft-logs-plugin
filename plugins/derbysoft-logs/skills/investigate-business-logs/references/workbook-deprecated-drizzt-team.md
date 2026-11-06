# Deprecated -Drizzt Team

Verbatim cell values from `Perf Log Process & Fields Standardization (1).xlsx`. The row number and column letters point to the original workbook; blank cells are left blank. Formulas are retained as formulas. The workbook contains draft, conflicting and deprecated entries; do not assume every row is deployed.

| Row | A | B | C | D | E |
| ---: | --- | --- | --- | --- | --- |
| 1 | f | Key | Comment | Value | Required/Optional |
| 2 | Retrieve |  |  |  |  |
| 3 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |
| 4 |  | process | LOSRetrieve, DailyRetrieve, LOSChangeRetrieve, DailyChangeRetrieve | LOSRetrieve, DailyRetrieve, LOSChangeRetrieve, DailyChangeRetrieve | Required |
| 5 |  | request_type | All,Change | string | Required |
| 6 |  | process_result | Success or Fail | string | Required |
| 7 |  | hotel_supplier | supplier hotel code | string | Required |
| 8 |  | hotel_derby | derby hotel code | string | Optional |
| 9 |  | echo_token | unique id for the request | string | Optional |
| 10 |  | supplier | derby supplier code | string | Required |
| 11 |  | channel | derby channel code | string | Optional |
| 12 |  | start_date | batch start date. Format is 2015-12-24 | string | Optional |
| 13 |  | end_date | batch end date. Format is 2015-12-26 | string | Optional |
| 14 |  | los | length of stay | number | Optional |
| 15 |  | iata | IATA send to supplier | number string | Optional |
| 16 |  | change_start_date | batch start date. Format is 2015-12-24 | string | Optional |
| 17 |  | change_end_date | batch end date. Format is 2015-12-26 | string | Optional |
| 18 |  | change_mask | 111110.0 | string | Optional |
| 19 |  | change_result | true/false | boolean | Optional |
| 20 |  | since | 2015-12-28T13:00:00.000Z | time | Required |
| 22 | Event | process_duration | total process time, unit is ms | number 1-999999999 | Required |
| 23 |  | process | AccessEvent | AccessEvent | Required |
| 24 |  | process_result | Success or Fail | string | Required |
| 25 |  | destination |  | string | Optional |
| 26 |  | user |  | string | Optional |
| 27 |  | event |  | string | Optional |
| 28 |  | event_detail |  | string | Optional |
| 29 |  | user_ip |  | string | Optional |
| 31 | ARI Consume |  |  |  |  |
| 32 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |
| 33 |  | process | ARIConsume | ARIConsume | Required |
| 34 |  | process_result | Success or Fail | string | Required |
| 35 |  | hotel_cnt | hotel count | number 1-999 | Required |
| 36 |  | message_cnt | total process message count | number 1-999 | Required |
| 37 |  | supplier | derby supplier code,upper case | string | Optional |
| 38 |  | channel | derby channel code,upper case | string | Optional |
