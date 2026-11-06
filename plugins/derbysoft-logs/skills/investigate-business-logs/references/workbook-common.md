# Common

Verbatim cell values from `Perf Log Process & Fields Standardization (1).xlsx`. The row number and column letters point to the original workbook; blank cells are left blank. Formulas are retained as formulas. The workbook contains draft, conflicting and deprecated entries; do not assume every row is deployed.

| Row | A | B | C | D | E |
| ---: | --- | --- | --- | --- | --- |
| 1 |   | Key | Comment | Value | Required/Optional |
| 2 | Duration | duration_details |  |  | Optional |
| 3 |  | db_duration |  |  |  |
| 4 | Error |  |  |  |  |
| 5 |  | err_code | derby standard error code | string | Required when process.result is Fail |
| 6 |  | err_msg | error message | string | Required when process.result is Fail. Max length is 1000. |
| 8 |  | err_code_supplier | supplier error code | string | Optional |
| 9 |  | err_msg_supplier | supplier error code and message | string | Optional. Max length is 1000. |
| 10 |  | err_code_channel | channel error code | string | Optional |
| 11 |  | err_msg_channel | channel error message | string | Optional. Max length is 1000. |
| 13 |  | err_source | the source of the error | string | Optional |
| 14 |  | err_code_inner_service | other service inner derby case the error (service dependency) | string | Optional |
| 16 |  | warn_code | warning code. same as err.code | string | Optional |
| 17 |  | warn_msg | warning message | string | Optional |
| 18 | Size |  |  |  |  |
| 19 |  | write_data_size | the data size that write to db/file for a request | number | Optional |
| 20 |  | read_data_size | the data size that read from db/file for a request | number | Optional |
| 21 |  | response_msg_size | the response message size for a request | number | Optional |
| 22 | Count |  |  |  |  |
| 23 |  | process_item_cnt | processed item count, like roomrate count | number | Optional |
| 24 |  | response_item_cnt | response to requestor item count, like the roomrate count after filter | number | Optional |
| 25 | Check Queue size |  |  |  |  |
| 26 |  | process | CheckQueueSize | CheckQueueSize | Required |
| 27 |  | process_result | Success or Fail(when it can not access queue information) | string | Required |
| 28 |  | supplier | derby supplier code,upper case | string | For supplier queue size, required |
| 29 |  | channel | derby channel code,upper case | string | For channel queue size, required |
| 30 |  | message_cnt | total message count in queue | number 1-99999 | Required |
| 31 |  | message_type | queue type | string | Optional |
| 32 |  | message_oldest_age | age of oldest message, unit is ms | number 1-999999999 | Required |
| 33 |  | message_running_cnt | total running message count in queue | number 1-9999 | Optional |
| 34 |  | message_waiting_cnt | total waiting message count in queue | number 1-99999 | Optional |
| 35 |  | message_scheduled_cnt | total scheduled message count in queue | number 1-99999 | Optional |
| 38 | Check Size |  |  |  |  |
| 39 |  | process | CheckSize |  | Required |
| 40 |  | process_result | Success or Fail(when it can not access queue information) | string | Required |
| 41 |  | supplier | derby supplier code,upper case | string | Optional |
| 42 |  | channel | derby channel code,upper case | string | Optional |
| 43 |  | data_cnt | total data count | number 1-99999999 | Required |
| 44 |  | data_type | data type | string | Required |
| 45 |  | data_oldest_age | age of oldest ata, unit is ms | number 1-999999999 | Optional |
| 47 | Connect Different Business scenarios |  |  |  |  |
| 48 |  | scenario_correlation_id | A unique identifier used to link multiple related requests, events, or logs that belong to the same business scenario or end-to-end business flow. | string | Optional |
