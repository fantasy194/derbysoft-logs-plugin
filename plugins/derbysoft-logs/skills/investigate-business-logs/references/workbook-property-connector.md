# Property Connector

Verbatim cell values from `Perf Log Process & Fields Standardization (1).xlsx`. The row number and column letters point to the original workbook; blank cells are left blank. Formulas are retained as formulas. The workbook contains draft, conflicting and deprecated entries; do not assume every row is deployed.

| Row | A | B | C | D | E |
| ---: | --- | --- | --- | --- | --- |
| 1 | Request | Key | Comment | Value | Required/Optional |
| 2 | ReceiveMessage |  |  |  |  |
| 3 |  | process | It is used to record the basic information of messages received from PMS and set hotel level alarms | MUST BE:ReceiveMessage | Required |
| 4 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 5 |  | process_result | process result | Success, Fail | Required |
| 6 |  | endpoint_id | hotel system endpoint id | string | Required |
| 7 |  | hotel_chain_supplier | supplier hotel chain id | string | Optional |
| 8 |  | hotel_supplier | supplier hotel id | string | Required |
| 9 |  | message_type_supplier | supplier message type | string | Optional |
| 10 |  | message_id_derby | derby message id | string | Optional |
| 12 | ConvertARITask |  |  |  |  |
| 13 |  | process | It is used to record ARI conversion and set hotel level alarms | MUST BE:ConvertPushCache,ConvertFetchCache | Required |
| 14 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 15 |  | process_result | process result | Success, Fail | Required |
| 16 |  | hotel_chain_supplier | supplier hotel chain id | string | Optional |
| 17 |  | hotel_supplier | supplier hotel id | string | Required |
| 18 |  | system_supplier | supplier system id | string | Required |
| 19 |  | hotel_derby | derby hotel id | string | Required |
| 20 |  | message_start_time | convert start.date | string(yyyy-MM-ddTHH:mm:ss.SSSZ) | Optional |
| 21 |  | message_end_time | convert end date | string(yyyy-MM-ddTHH:mm:ss.SSSZ) | Optional |
| 22 |  | convert_rate_count | convert rate count | number 1-999999 | Optional |
| 23 |  | convert_inventory_count | convert inventory count | number 1-999999 | Optional |
| 24 |  | convert_restriction_count | convert restriction count | number 1-999999 | Optional |
| 27 | ProduceMessage/ConsumeMessage |  |  |  |  |
| 28 |  | process | It is used to record the basic information of kafka messages to send | MUST BE:ProduceMessage,ConsumeMessage | Required |
| 29 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 30 |  | process_result | process result | Success, Fail | Required |
| 31 |  | err_code | derby standard error code | string | Optional when process.result is Fail |
| 32 |  | err_msg | error message | string | Optional when process.result is Fail. Max length is 1000. |
| 33 |  | message_topic | message topic | string | Required |
| 34 |  | message_id_derby | derby message id | string | Optional |
| 35 |  | message_id_console | console id | string | Optional |
| 36 |  | message_key | message key | string | Optional |
| 37 |  | message_type | message type | string | Optional |
| 38 |  | channel | derby channel code | string | Optional |
| 39 |  | hotel_channel | channel hotel code | string | Optional |
| 40 |  | supplier | derby supplier code,upper case | string | Optional |
| 41 |  | hotel_chain_supplier | supplier hotel chain id | string | Optional |
| 42 |  | hotel_supplier | supplier hotel code | string | Optional |
| 43 |  | hotel_derby | derby hotel code | string | Optional |
| 45 | GetHotelInfo/ChangeHotelInfo |  |  |  |  |
| 46 |  | process | It is used to record the basic information from pc-console | MUST BE:GetHotelInfo、ChangeHotelInfo | Required |
| 47 |  | process_type | internal system process type, method name | string | Required |
| 48 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 49 |  | process_result | process result | Success, Fail | Required |
| 50 |  | err_code | derby standard error code | string | Optional when process.result is Fail |
| 51 |  | err_msg | error message | string | Optional when process.result is Fail. Max length is 1000. |
| 52 |  | message_id_derby | uuid for the request | string | Optional |
| 53 |  | source_id | connectionManagerId | string | Optional |
| 54 |  | supplier | derby supplier code,upper case | string | Optional |
| 55 |  | channel | derby channel code | string | Optional |
| 56 |  | hotel_derby | derby hotel id | string | Required |
| 57 |  | hotel_chain_supplier | supplier hotel chain id | string | Optional |
| 58 |  | hotel_supplier | supplier hotel code | string | Optional |
| 59 |  | hotel_channel | channel hotel code | string | Optional |
| 61 | OperaCloudWhiteLabel |  |  |  |  |
| 62 |  | process | Used to record OperaCloud-pushed Onboard Notifications | MUST BE:<br>OperaNotifications,OperaHandleEvent,<br>OperaBatchTaskExec,OperaTaskExec | Required |
| 63 |  | connection_id | Connection ID of the sender on PC | string | Required |
| 64 |  | hotel_derby | derby hotel id | string | Optional |
| 65 |  | hotel_supplier | supplier hotel id | string | Required |
| 66 |  | message_id_derby | derby message id | string | Optional |
| 67 |  | message_id_supplier | supplier message id | string | Optional |
| 68 |  | transaction_id | The id of a transaction is different from the messageId | string | Optional |
| 69 |  | message_type | Notification message type of the push | string | Required |
| 70 |  | message_key | message key | string | Optional |
| 71 |  | message_topic | message topic | string | Optional |
| 72 |  | action_type | Action type processed in the notification message | string | Optional |
| 73 |  | action_level | Action type level | string | Optional |
| 74 |  | channel_id | channel id | string | Optional |
| 75 |  | room_type_derby | derby room type id | string | Optional |
| 76 |  | room_type_supplier | supplier room type id | string | Optional |
| 77 |  | room_type_channel | channel room type id | string | Optional |
| 78 |  | rate_plan_derby | derby rate plan id | string | Optional |
| 79 |  | rate_plan_supplier | supplier rate plan id | string | Optional |
| 80 |  | rate_plan_channel | channel rate plan id | string | Optional |
| 81 |  | record_cnt | The number of tasks in a batch | number 1-99999999999 | Optional |
| 82 |  | process_result | process result | Success, Fail,Ignore,Warn | Required |
| 83 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 84 |  | err_code | derby standard error code | string | Optional |
| 85 |  | err_msg | error message | string | Optional |
| 88 | CheckRateDependency |  |  |  |  |
| 89 |  | process | Used to record derived Rate check result | MUST BE:<br>CheckRateDependency | Required |
| 90 |  | process_type | internal system process type, method name | string | Optional |
| 91 |  | hotel_derby | derby hotel id | string | Required |
| 92 |  | rate_plan_derby | derby rate plan id | string | Required |
| 93 |  | parent_rate_plan | parent rate plan id | string | Optional |
| 94 |  | derived_rate_plan | derived rate plan id | string | Optional |
| 95 |  | process_result | process result | Success, Fail,Ignore,Warn | Required |
| 96 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 97 |  | err_code | derby standard error code | string | Optional |
| 98 |  | err_msg | error message | string | Optional |
