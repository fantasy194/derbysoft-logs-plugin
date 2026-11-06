# US Engineering - will removed

Verbatim cell values from `Perf Log Process & Fields Standardization (1).xlsx`. The row number and column letters point to the original workbook; blank cells are left blank. Formulas are retained as formulas. The workbook contains draft, conflicting and deprecated entries; do not assume every row is deployed.

| Row | A | B | C | D | E |
| ---: | --- | --- | --- | --- | --- |
| 1 | Request | Key | Comment | Value | Required/Optional |
| 2 | Portal |  |  |  |  |
| 3 |  | admin | admin users email  | string |  |
| 4 |  | app_id | uuid of the app  | string |  |
| 5 |  | app_name | name of the app | string | required |
| 6 |  | change_msg | change message (for audit) | string |  |
| 7 |  | change_type | type of change (for audit) | string |  |
| 8 |  | channel | channel code / id | string |  |
| 9 |  | channel_id | uuid of the channel from the db | string |  |
| 10 |  | channel_time | time spent processing channel data | long or string |  |
| 11 |  | channel_time_total | total time spent processing channel data | long |  |
| 12 |  | count | counter | long |  |
| 13 |  | dashboard_interval | interval of the dashboard in time | string |  |
| 14 |  | dashboard_period | time period of the dashboard data | string |  |
| 15 |  | dashboard_txn | transaction type within the dashboard | string |  |
| 16 |  | dashboard_type | type of dashboard being rendered | string |  |
| 17 |  | db_time | time to perform db operations | long or string |  |
| 18 |  | db_time_total | total db time | long |  |
| 19 |  | echo_token | uuid of the request | string |  |
| 20 |  | end_date | end date | string |  |
| 21 |  | err_code | error code | string | required if process=Fail |
| 22 |  | err_code_channel | channel error code | string |  |
| 23 |  | err_code_supplier | supplier error code | string |  |
| 24 |  | err_msg | error message | string | required if process=Fail |
| 25 |  | err_msg_channel | channel error message | string |  |
| 26 |  | err_msg_supplier | supplier error message | string |  |
| 27 |  | es_cached | if the data from es is cached | boolean |  |
| 28 |  | es_time | time to query es | long or string |  |
| 29 |  | es_time_total | total time to query es | long |  |
| 30 |  | es_timeout | if there was an es timeout | boolean |  |
| 31 |  | form_action | action on the form | string |  |
| 32 |  | form_page | page # of the form for pagination | string |  |
| 33 |  | form_params | parameters from the form | string |  |
| 34 |  | function_time | time to execute a function | long or string |  |
| 35 |  | function_time_total | total function time | long |  |
| 36 |  | host | hostname  | string |  |
| 37 |  | hotel_channel | channel hotel code | string |  |
| 38 |  | hotel_derby | derbysoft hotel code | string |  |
| 39 |  | hotel_supplier | supplier hotel code | string |  |
| 40 |  | ip | ip address of the server | string |  |
| 41 |  | mail_sent | if a mail was sent | boolean |  |
| 42 |  | mail_time | time to send a mail | long or string |  |
| 43 |  | mail_time_total | total time to send mails | long |  |
| 44 |  | map_time | time to do mapping | long or string |  |
| 45 |  | map_time_total | total mapping time | long |  |
| 46 |  | message_cnt | message counts | long |  |
| 47 |  | mode | mode of the application (dev, qa, prod) | string |  |
| 48 |  | parse_time | time to parse xml / json results | long or string |  |
| 49 |  | parse_time_total | total parsing time | long |  |
| 50 |  | process | name of the process | string | required |
| 51 |  | process_duration | total processing time | long | required |
| 52 |  | process_result | success / fail | string | required |
| 53 |  | process_type | type of process (avail, res, etc) | string |  |
| 54 |  | report_id | uuid of the report | string |  |
| 55 |  | report_saved | if the report was saved or not | boolean |  |
| 56 |  | report_time | time to process the report | long or string |  |
| 57 |  | report_time_total | total time to process the reports | long |  |
| 58 |  | report_type | report type | string |  |
| 59 |  | request_time | time to process the request | long or string |  |
| 60 |  | request_time_total | total time to process the request | long |  |
| 61 |  | request_type | type of request | string |  |
| 62 |  | role | role of the user | string |  |
| 63 |  | service | service being executed | string |  |
| 64 |  | start_date | start date | string |  |
| 65 |  | startup | when the app started | string |  |
| 66 |  | supplier | supplier name | string |  |
| 67 |  | supplier_id | uuid of the supplier from the db | string |  |
| 68 |  | supplier_time | time to process supplier data | long or string |  |
| 69 |  | supplier_time_total | total time to process supplier data | long |  |
| 70 |  | timeout | if a timeout occurred | boolean |  |
| 71 |  | uptime | uptime of the app | string |  |
| 72 |  | user_agent | users browser | string |  |
| 73 |  | user_email | users email address | string |  |
| 74 |  | user_id | users uuid | string |  |
| 75 |  | user_ip | users ip address | string |  |
| 76 |  | user_name | users name | string |  |
| 77 |  | version | version of the app | string |  |
| 78 |  | wait_time | wait time  | long or string |  |
| 79 |  | wait_time_total | total wait time | long |  |
