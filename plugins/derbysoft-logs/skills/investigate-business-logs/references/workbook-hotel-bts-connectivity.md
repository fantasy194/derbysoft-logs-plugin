# Hotel BTS Connectivity

Verbatim cell values from `Perf Log Process & Fields Standardization (1).xlsx`. The row number and column letters point to the original workbook; blank cells are left blank. Formulas are retained as formulas. The workbook contains draft, conflicting and deprecated entries; do not assume every row is deployed.

| Row | A | B | C | D | E |
| ---: | --- | --- | --- | --- | --- |
| 1 |   | Key | Comment | Value | Required/Optional |
| 3 | GetMasterHotelAvailability |  | GetMasterHotelAvailability is for master hotels availability result |  |  |
| 4 |  | process_duration | total process time, unit is ms |  | Required |
| 5 |  | process | derby process type | MUST BE: GetMasterHotelAvailability | Required |
| 6 |  | process_supplier | supplier process type | string | Optional |
| 7 |  | process_channel | channel process type | string | Optional |
| 8 |  | process_result | process result | Success, Fail | Required |
| 9 |  | availability_result | if there are no any room is available, should be NoAvail, if process.result is Fail, should be NoAvail | Avail or NoAvail | Required |
| 10 |  | channel | derby channel code | string,upper case | Required |
| 11 |  | hotel_master | channel master hotel code | string array | Required |
| 12 |  | hotel_derby | derby hotel code | string array | Optional |
| 13 |  | echo_token | unique id for the request | string | Optional |
| 14 |  | check_in | checkin,format is 2024-01-05 | string | Optional |
| 15 |  | check_out | checkout, format is 2024-01-05 | string | Optional |
| 16 |  | adult_cnt | adult count | number 1-9 | Optional |
| 17 |  | children_cnt | children count | number 1-9 | Optional |
| 18 |  | children_ages | children ages. Format is 10,6 | number array 1-9： [4,6] | Optional |
| 19 |  | room_cnt | room count | number 1-9 | Optional |
| 20 |  | los | length of stay | number | Optional |
| 21 |  | hotel_cnt | masterhotel request count | number | Optional |
| 22 |  | mapping_hotel | exists mapping masterhotel codes | masterhotel codes array：<br>[“M001”,”M002”] | Optional |
| 23 |  | no_mapping_cnt | no mapping masterhotel count | number | Optional |
| 24 |  | no_mapping_hotel | no mapping masterhotel codes | masterhotel codes array：<br>[“M001”,”M002”] | Optional |
| 25 |  | corporate_supplier | BTS only, The corporate code in supplier | string | Optional |
| 26 |  | corporate_channel | BTS only, The corporate code in channel | string | Optional |
| 29 | LeadRateDiff | BTS can calculate the difference between the hotel's lead rate and the lowest price in the GetAvailability result when receiving a GetAvailability request, then produces this log_ |  |  |  |
| 30 |  | process | derby process type | MUST BE: LeadRateDiff | Required |
| 31 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 32 |  | process_duration |  | number 1-999999 | Required |
| 33 |  | duration_details |  | string | Required |
| 34 |  | process_result |  | Success, Fail | Required |
| 35 |  | corporate_channel | The corporate code in channel | string | Optional |
| 36 |  | supplier |  | string | Optional |
| 37 |  | channel |  | string | Optional |
| 38 |  | hotel_channel | primary hotel code | string | Optional |
| 39 |  | room_cnt | room count | number 1-999999 | Optional |
| 40 |  | adult_cnt | adult cout | number 1-999999 | Optional |
| 41 |  | check_in | checkin,format is 2015-12-24 | string | Optional |
| 42 |  | check_out | checkout, format is 2015-12-24 | string | Optional |
| 43 |  | los | length of stay for ari | number 1-999999 | Optional |
| 44 |  | accurate | The accuracy of the lead rate | true,false | Required |
| 45 |  | lead_rate_type | The type of the lead rate | FixedRate, Summary, HistorySummary | Required |
| 46 |  | cache_source | source of lead rate cache | RegularFetch, ReservationRefresh, LivecheckRefresh, <br>LiveQueryRefresh, ProactiveFetch | Optional |
| 47 |  | cache_update_time | updatetime of lead rate cache | string | Optional |
