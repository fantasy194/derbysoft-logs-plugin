# Hotel Marketing Service

Verbatim cell values from `Perf Log Process & Fields Standardization (1).xlsx`. The row number and column letters point to the original workbook; blank cells are left blank. Formulas are retained as formulas. The workbook contains draft, conflicting and deprecated entries; do not assume every row is deployed.

| Row | A | B | C | D | E | F |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | MSM |  |  |  |  |  |
| 2 | Bidding |  |  |  |  |  |
| 3 |  | process_duration | total process time, unit is ms | number 1-99999999999 | require |  |
| 4 |  | process |  | Bidding | require |  |
| 5 |  | process_result |  | Sucess/Fail | require |  |
| 6 |  | supplier |  | HILTON/VEGAS.... | require |  |
| 7 |  | channel |  | GOOGLE/TRIPADVISOR | require |  |
| 8 |  | process_channel |  | GoogleHPAApi or TripAdvisorFTP or KayakSFTP | require |  |
| 10 |  | bidding_model |  | Full/Partial/Mixed | require |  |
| 11 |  | bidding_format |  | xml/csv/excel | require |  |
| 12 |  | bidding_type |  | bucket/cpc | require |  |
| 13 |  | message_size |  | total size |  |  |
| 14 |  | hotel_cnt |  |  |  |  |
| 17 | Check Bidding Process |  |  |  |  |  |
| 18 |  | process_duration+ | total process time, unit is ms | number 1-99999999999 | require |  |
| 19 |  | process |  | Bidding | require |  |
| 20 |  | process_result |  | Sucess/Fail | require |  |
| 21 |  | supplier |  | HILTON/VEGAS.... | require |  |
| 22 |  | channel |  | GOOGLE/TRIPADVISOR | require |  |
| 23 |  | process_channel |  | GoogleHPAApi or TripAdvisorFTP or KayakSFTP | require |  |
| 25 | LinkCenter |  |  |  |  |  |
| 26 | Click |  |  |  |  |  |
| 27 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |  |
| 28 |  | process | derby process type | MUST BE: Click | Required |  |
| 29 |  | process_result | process result | Success, Fail | Required |  |
| 30 |  | supplier | derby supplier code | string,upper case | Required |  |
| 31 |  | channel | derby channel code | string,upper case | Required |  |
| 32 |  | hotel_supplier | supplier hotel code | string | Required |  |
| 33 |  | catalog_id | Indicates diferent types of click | string,lowercase v2,v3 | Required |  |
| 34 |  | request_type | Indicates whether are real clicks | string,lowercase yes,no | Required |  |
| 35 |  | room_type_supplier | supplier room type code | string | Optional |  |
| 36 |  | rate_plan_supplier | supplier rate plan code | string | Optional |  |
| 37 |  | hotel_derby | derby hotel code | string | Required |  |
| 38 |  | room_type_derby | derby room type code | string | Optional |  |
| 39 |  | rate_plan_derby | derby rate plan code | string | Optional |  |
| 40 |  | echo_token | unique id for the request | string | Required |  |
| 41 |  | availability_result |  | MUST BE: NoAvail | Required |  |
| 42 |  | check_in | checkin,format is 2015-12-24 | string | Required | should be Optional |
| 43 |  | check_out | checkout, format is 2015-12-24 | string | Required | should be Optional |
| 44 |  | adult_cnt | adult cout | number 1-9 | Optional |  |
| 45 |  | children_cnt | children count | number 1-9 | Optional |  |
| 46 |  | children_ages | children ages. Format is 10,6 | string | Optional |  |
| 47 |  | room_cnt | room count | number 1-99 | Optional |  |
| 48 |  | los | length of stay | number | Required | should be Optional |
| 50 |  | advance_day |  | number 0-999999999 | Required | should be Optional |
| 51 |  | user_cookie_id |  | string | Required |  |
| 52 |  | user_device |  | Could be: 1) desktop 2) tablet 3) mobile 4) unknown | Required | Required? |
| 53 |  | user_currency |  | string | Optional |  |
| 54 |  | user_country |  | string | Optional |  |
| 55 |  | user_ip |  | string | Required |  |
| 56 |  | user_language |  | string | Optional |  |
| 57 |  | user_agent |  | string | Optional |  |
| 58 |  | url_request |  | string | Required |  |
| 59 |  | site |  | string | Optional |  |
| 60 |  | click_type | Indicates whether the user clicked on an ad for a hotel or for a Room Bundle | Could be: 1) hotel 2) room 3)unknown | Required | should be Optional |
| 61 |  | date_type | Indicates whether the user selected the default date or specified a date when searching. Possible values are | Could be: 1) default 2) selected 3)unknown | Required | should be Optional |
| 62 |  | package_id |  | string | Optional |  |
| 63 |  | rate_rule_id |  | string | Optional |  |
| 64 |  | price_displayed_tax | The amount of tax displayed to the user in the user's local currency | string | Optional |  |
| 65 |  | price_displayed_total | The total cost of the room that is displayed to the user in the user's local currency. | string | Optional |  |
| 66 |  | price_derby_total |  | string | Optional |  |
| 67 |  | price_derby_currency |  | string | Optional |  |
| 68 |  | payment_id |  | string | Optional |  |
| 69 |  | click_referer | http referer | string | Optional |  |
| 72 | TrackingBooking |  |  |  |  |  |
| 73 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |  |
| 74 |  | process | derby process type | MUST BE: TrackingBooking | Required |  |
| 75 |  | process_result | process result | Success, Fail | Required |  |
| 76 |  | supplier | derby supplier code | string,upper case | Required |  |
| 77 |  | channel | derby channel code | string,upper case | Optional |  |
| 78 |  | hotel_supplier | supplier hotel code | string | Required |  |
| 79 |  | catalog_id | Indicates diferent types of tracking | string,lowercase tag,pixel | Required |  |
| 80 |  | room_type_supplier | supplier room type code | string | Optional |  |
| 81 |  | rate_plan_supplier | supplier rate plan code | string | Optional |  |
| 82 |  | hotel_derby | derby hotel code | string | Optional |  |
| 83 |  | room_type_derby | derby room type code | string | Optional |  |
| 84 |  | rate_plan_derby | derby rate plan code | string | Optional |  |
| 85 |  | echo_token | unique id for the request | string | Required |  |
| 86 |  | check_in | checkin,format is 2015-12-24 | string | Optional |  |
| 87 |  | check_out | checkout, format is 2015-12-24 | string | Optional |  |
| 88 |  | adult_cnt | adult cout | number 1-9 | Optional |  |
| 89 |  | children_cnt | children count | number 1-9 | Optional |  |
| 90 |  | children_ages | children ages. Format is 10,6 | string | Optional |  |
| 91 |  | room_cnt | room count | number 1-99 | Optional |  |
| 92 |  | los | length of stay | number | Optional |  |
| 93 |  | booking_time | The time of booking made | ISO UTC time | Required |  |
| 94 |  | res_amount_net |  | double | Optional |  |
| 95 |  | res_amount_total |  | double | Required |  |
| 96 |  | res_currency |  | string | Required |  |
| 97 |  | derby_account_code |  | string | Required |  |
| 98 |  | advance_day |  | number 0-999999999 | Required |  |
| 99 |  | user_cookie_id |  | string | Optional |  |
| 100 |  | user_device |  | Could be: 1) desktop 2) tablet 3) mobile 4) unknow | Required |  |
| 101 |  | user_currency |  | string | Optional |  |
| 102 |  | user_country |  | string | Optional |  |
| 103 |  | user_ip |  | string | Required |  |
| 104 |  | user_language |  | string | Optional |  |
| 105 |  | user_agent |  | string | Optional |  |
| 106 |  | url_request |  | string | Required |  |
| 107 |  | site |  | string | Optional |  |
| 110 | Google Private Rate |  |  |  |  |  |
| 111 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |  |
| 112 |  | process | derby process type | MUST BE: GooglePrivateRate | Required |  |
| 113 |  | process_result | process result | Success, Fail | Required |  |
| 114 |  | echo_token | unique id for the request | string | Required |  |
| 115 |  | channel | derby channel code | string,upper case | Required |  |
| 116 |  | supplier | derby supplier code | string,upper case | Optional |  |
| 117 |  | partner_code | Google partner code | string | Required |  |
| 118 |  | rate_rule_id | Google private rule id | string | Required |  |
| 119 |  | derby_account_code | Derby account code | string | Required |  |
| 121 | Price Accuracy Report |  |  |  |  |  |
| 122 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |  |
| 123 |  | process | derby process type | MUST BE: AccuracyReport | Required |  |
| 124 |  | process_result | process result | Success, Fail | Required |  |
| 125 |  | channel | derby channel code | string,upper case | Optional |  |
| 126 |  | supplier | derby supplier code | string,upper case | Optional |  |
| 127 |  | partner_code | Channel partner code | string | Optional |  |
| 128 |  | report_type | report type | Channel, Derby2CRS, Channel2CRS | Required |  |
| 129 |  | channel_accuracy | channel accuracy | EXCELLENT, GOOD, POOR, AT_RISK | Optional |  |
| 130 |  | mismatch_rate | mismatch rate | double | Optional |  |
| 131 |  | record_cnt | QA record count | number 1-99999999999 | Optional |  |
| 132 |  | record_mismatch_cnt | QA record mismatch count | number 1-99999999999 | Optional |  |
| 134 | Facebook Push |  |  |  |  |  |
| 135 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |  |
| 136 |  | process | derby process type | PushRoomType, PushPrice, CheckRoomType, CheckPrice | Required |  |
| 137 |  | process_result | Success or Fail | string | Required |  |
| 138 |  | supplier | derby supplier code,upper case | string | Required |  |
| 139 |  | catalog_id | facebook catalog id | string | Required |  |
| 140 |  | echo_token | facebook handle | string | Required |  |
| 141 |  | retry_cnt | retry times | number 1-99 | Required |  |
| 143 | Facebook Sync Hotel |  |  |  |  |  |
| 144 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |  |
| 145 |  | process | derby process type | SyncHotel | Required |  |
| 146 |  | process_result | Success or Fail | string | Required |  |
| 147 |  | catalog_id | facebook catalog id | string | Required |  |
| 148 |  | hotel_cnt | hotel numbers | number 1-999999999 | Required |  |
| 150 | SearchFeed Channel Log |  |  |  |  |  |
| 151 |  | process_duration | total process time, unit is ms |  | Required |  |
| 152 |  | process | derby process type | GetAvailability on channel end.<br>ARIFetch on supplier end. | Required |  |
| 153 |  | process_result | process result | Success, Fail | Required |  |
| 154 |  | availability_result | if there are no any room is available, should be NoAvail, if process.type is Fail, should be NoAvail | Avail or NoAvail | Required |  |
| 155 |  | request_type | channel/supplier orginal request type | string | Required |  |
| 156 |  | channel | derby channel code | string,upper case | Required on channel end |  |
| 157 |  | supplier | derby supplier code,upper case | string | Required on supplier end |  |
| 158 |  | cache | cache get availability | True or False | Optional |  |
| 159 |  | hotel_derby | derby hotel code | string | Optional |  |
| 160 |  | echo_token | unique id for the request | string | Optional |  |
| 161 |  | check_in | checkin,format is 2015-12-24 | string | Optional |  |
| 162 |  | check_out | checkout, format is 2015-12-24 | string | Optional |  |
| 163 |  | adult_cnt | adult count | number 1-9 | Optional |  |
| 164 |  | children_cnt | children count | number 1-9 | Optional |  |
| 165 |  | children_ages | children ages. Format is 10,6 | string | Optional |  |
| 166 |  | hotel_cnt | hotel numbers | number 1-999999999 | Required |  |
| 167 |  | room_cnt | room count | number 1-99 | Optional |  |
| 168 |  | los | length of stay | number | Optional |  |
| 169 |  | has_country | true/false | boolean | Required |  |
| 170 |  | has_language | true/false | boolean | Required |  |
