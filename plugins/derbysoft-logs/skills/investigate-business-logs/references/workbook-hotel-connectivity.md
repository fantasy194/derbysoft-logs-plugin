# Hotel Connectivity

Verbatim cell values from `Perf Log Process & Fields Standardization (1).xlsx`. The row number and column letters point to the original workbook; blank cells are left blank. Formulas are retained as formulas. The workbook contains draft, conflicting and deprecated entries; do not assume every row is deployed.

| Row | A | B | C | D | E | F |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | Request | Key | Comment | Value | Required/Optional |  |
| 2 | GetAvailability/SaveAvailability |  | SaveAvailibility is for caching availability result |  |  |  |
| 3 |  | process_duration | total process time, unit is ms |  | Required |  |
| 4 |  | process | derby process type | MUST BE:GetAvailability, SaveAvailability | Required |  |
| 5 |  | process_supplier | supplier process type | For Exampel: OTA_GetAvail | Optional |  |
| 6 |  | process_channel | channel process type | For Exampel: OTA_GetAvail | Optional |  |
| 7 |  | process_result | process result | Success, Fail | Required |  |
| 8 |  | availability_result | if there are no any room is available, should be NoAvail, if process.type is Fail, should be NoAvail | Avail or NoAvail | Required |  |
| 9 |  | cache | cache get availability | True or False | Optional |  |
| 10 |  | supplier | derby supplier code | string,upper case | Required on supplier end |  |
| 11 |  | channel | derby channel code | string,upper case | Required on channel end |  |
| 12 |  | hotel_supplier | supplier hotel code | string | Required on supplier end for single hotel |  |
| 13 |  | hotel_channel | channel hotel code | string | Required on channel end for single hotel |  |
| 14 |  | hotel_derby | derby hotel code | string | Optional |  |
| 15 |  | echo_token | unique id for the request | string | Optional |  |
| 16 |  | check_in | checkin,format is 2015-12-24 | string | Optional |  |
| 17 |  | check_out | checkout, format is 2015-12-24 | string | Optional |  |
| 18 |  | adult_cnt | adult count | number 1-9 | Optional |  |
| 19 |  | children_cnt | children count | number 1-9 | Optional |  |
| 20 |  | children_ages | children ages. Format is 10,6 | string | Optional |  |
| 21 |  | room_cnt | room count | number 1-99 | Optional |  |
| 22 |  | los | length of stay | number | Optional |  |
| 23 |  | iata | IATA send to supplier | number string | Optional |  |
| 24 |  | storage_duration | backen storage/cache process duration | number | Optional |  |
| 25 |  | corporate_supplier | BTS only, The corporate code in supplier | string | Optional |  |
| 26 |  | corporate_derby | BTS only, The corporate code in derby | string | Optional |  |
| 27 |  | corporate_channel | BTS only, The corporate code in channel | string | Optional |  |
| 28 |  | connection_type | identify EXCHANGE connection | MUST BE: Standard, Exchange | Optional |  |
| 30 | Live Check |  |  |  |  |  |
| 31 |  | process_duration | total process time, unit is ms |  | Required |  |
| 32 |  | process | derby process type | MUST BE:LiveCheck | Required |  |
| 33 |  | process_supplier | supplier process type | For Exampel: OTA_GetAvail | Optional |  |
| 34 |  | process_channel | channel process type | For Exampel: OTA_GetAvail | Optional |  |
| 35 |  | process_result | process result | Success, Fail | Required |  |
| 36 |  | availability_result | if there are no any room is available, should be NoAvail, if process.type is Fail, should be NoAvail | Avail or NoAvail | Optional |  |
| 37 |  | supplier | derby supplier code | string,upper case | Required on supplier end |  |
| 38 |  | channel | derby channel code | string,upper case | Required on channel end |  |
| 39 |  | hotel_channel | channel hotel code | string | Required on channel end |  |
| 40 |  | room_type_channel | channel room type code | string | Optional |  |
| 41 |  | rate_plan_channel | channel rate plan code | string | Optional |  |
| 42 |  | hotel_supplier | supplier hotel code | string | Optional |  |
| 43 |  | room_type_supplier | supplier room type code | string | Optional |  |
| 44 |  | rate_plan_supplier | supplier rate plan code | string | Optional |  |
| 45 |  | hotel_derby | derby hotel code | string | Optional |  |
| 46 |  | room_type_derby | derby room type code | string | Optional |  |
| 47 |  | rate_plan_derby | derby rate plan code | string | Optional |  |
| 48 |  | echo_token_channel | unique id for the request | string | Optional |  |
| 49 |  | echo_token_derby | unique id for the request | string | Optional |  |
| 50 |  | check_in | checkin,format is 2015-12-24 | string | Optional |  |
| 51 |  | check_out | checkout, format is 2015-12-24 | string | Optional |  |
| 52 |  | adult_cnt | adult cout | number 1-9 | Optional |  |
| 53 |  | children_cnt | children count | number 1-9 | Optional |  |
| 54 |  | children_ages | children ages. Format is 10,6 | string | Optional |  |
| 55 |  | room_cnt | room count | number 1-99 | Optional |  |
| 56 |  | los | length of stay | number | Optional |  |
| 57 |  | rate_amount | amount information. Like ABT:100.00 USD, AAT 120.00 USD TOTAL: 240 USD | string | Optional |  |
| 58 |  | iata | IATA send to supplier | number string | Optional |  |
| 59 |  | corporate_supplier | BTS only, The corporate code in supplier | string | Optional |  |
| 60 |  | corporate_derby | BTS only, The corporate code in derby | string | Optional |  |
| 61 |  | corporate_channel | BTS only, The corporate code in channel | string | Optional |  |
| 62 |  | connection_type | identify EXCHANGE connection | MUST BE: Standard, Exchange | Optional |  |
| 63 |  | request_ip | request's IP address | string | Optional |  |
| 65 | Single Push To Channel or Push From Supplier |  |  |  |  |  |
| 66 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |  |
| 67 |  | process | ARIRequest | ARIRequest | Required |  |
| 68 |  | request_type | channel/supplier orginal request type | string | Required |  |
| 69 |  | process_result | Success or Fail | string | Required |  |
| 70 |  | supplier | derby supplier code,upper case | string | Required on supplier end |  |
| 71 |  | channel | derby channel code,upper case | string | Required on channel end |  |
| 72 |  | hotel_channel | channel hotel code | string | Required on channel end |  |
| 73 |  | hotel_supplier | supplier hotel code | string | Required on supplier end |  |
| 74 |  | hotel_derby | derby hotel code | string | Optional |  |
| 75 |  | echo_token | unique id for the request | string | Optional |  |
| 76 |  | room_type_channel | channel room type code | string | Optional |  |
| 77 |  | rate_plan_channel | channel rate plan code | string | Optional |  |
| 78 |  | room_type_derby | derby room type code | string | Optional |  |
| 79 |  | rate_plan_derby | derby rate plan code | string | Optional |  |
| 80 |  | room_type_supplier | supplier room type code | string | Optional |  |
| 81 |  | rate_plan_supplier | supplier rate plan code | string | Optional |  |
| 82 |  | start_date | min date in the message. Format is 2015-12-24 | string | Optional |  |
| 83 |  | end_date | max date in the message. Format is 2015-12-26 | string | Optional |  |
| 84 |  | original_timestamp | timestamp in xml message2015-12-28T13:00:00.000Z | string | Optional |  |
| 85 |  | manual_operation | Manual push type | Must be: OfflineRatePlan,OfflineRoomType,OfflineRoomRate | Optional |  |
| 86 |  | data_size | request data size, unit: bytes | number 1-999999999 | Optional |  |
| 87 |  | connection_type | identify EXCHANGE connection | MUST BE: Standard, Exchange | Optional |  |
| 88 | Push To Channel or Push From Supplier Ack |  |  |  |  |  |
| 89 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |  |
| 90 |  | process | ARIAck | ARIAck | Required |  |
| 91 |  | request_type | channel orginal request type | string | Required |  |
| 92 |  | process_result | Success or Fail | string | Required |  |
| 93 |  | supplier | derby supplier code,upper case | string | Required on supplier end |  |
| 94 |  | channel | derby channel code,upper case | string | Required on channel end |  |
| 95 |  | hotel_channel | channel hotel code | string | Required on channel end |  |
| 96 |  | hotel_supplier | supplier hotel code | string | Required on supplier end |  |
| 97 |  | hotel_derby | derby hotel code |  | Optional |  |
| 98 |  | echo_token | same a supplier request echo.token | string | Optional |  |
| 99 |  | manual_operation | Manual push type | Must be: OfflineRatePlan,OfflineRoomType,OfflineRoomRate | Optional |  |
| 100 | Batch Push to Channel |  |  |  |  |  |
| 101 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |  |
| 102 |  | process | BatchARIRequest | BatchARIRequest | Required |  |
| 103 |  | request_type | channel orginal request type | string | Optional |  |
| 104 |  | process_result | Success or Fail | string | Required |  |
| 105 |  | hotel_channel | channel hotel code | string | Optional |  |
| 106 |  | hotel_derby | derby hotel code | string | Optional |  |
| 107 |  | supplier | derby supplier code,upper case | string | Optional |  |
| 108 |  | channel | derby channel code,upper case | string | Required |  |
| 109 |  | wait_duration | wait time in queue. unit is ms | number 1-999999999 | Optional |  |
| 110 |  | message_cnt | total process message count | number 1-999 | Required |  |
| 111 |  | message_fail_cnt | fail process message count | number 1-999 | Required |  |
| 112 |  | message_duration_min | min process message duration | number 1-999999999 | Required |  |
| 113 |  | message_duration_max | max process message count | number 1-999999999 | Required |  |
| 114 |  | message_duration_avg | avg process message count | number 1-999999999 | Required |  |
| 115 |  | start_date | batch start date. Format is 2015-12-24 | string | Optional |  |
| 116 |  | end_date | batch end date. Format is 2015-12-26 | string | Optional |  |
| 117 |  | min_los | min los for this batch | number | Optional |  |
| 118 |  | max_los | max los for this batch | number | Optional |  |
| 120 | CDS | one request to supplier |  |  |  |  |
| 121 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |  |
| 122 |  | process | SingleCDSFetch | SingleCDSFetch | Required |  |
| 123 |  | request_type | supplier orginal request type | string | Required |  |
| 124 |  | process_result | Success or Fail | string | Required |  |
| 125 |  | echo_token | unique id for the request | string | Optional |  |
| 126 |  | supplier | derby supplier code | string | Required |  |
| 127 |  | channel | derby channel code | string | Optional |  |
| 128 |  | hotel_channel | channel hotel code | string | Optional |  |
| 129 |  | hotel_supplier | supplier hotel code | string | Required |  |
| 130 |  | hotel_derby | derby hotel code |  | Optional |  |
| 131 |  | start_date | batch start date. Format is 2015-12-24 | string | Optional |  |
| 132 |  | end_date | batch end date. Format is 2015-12-26 | string | Optional |  |
| 133 |  | los | max los | number | Optional |  |
| 134 |  | iata | IATA send to supplier | number string | Optional |  |
| 135 |  | change_start_date | batch start date. Format is 2015-12-24 | string | Optional |  |
| 136 |  | change_end_date | batch end date. Format is 2015-12-26 | string | Optional |  |
| 137 |  | change_date_cnt |  | number | Optional |  |
| 138 |  | change_mask | 111110.0 | string | Optional |  |
| 139 |  | change_result | true/false | boolean | Optional |  |
| 140 |  | since | 2015-12-28T13:00:00.000Z  UTC Time | time | Required |  |
| 142 | Supplier Request | The request we send to supplier_ |  |  |  |  |
| 143 |  | process_duration | total process time, unit is ms |  | Required |  |
| 144 |  | process | derby process type | MUST BE:SupplierRequest | Required |  |
| 145 |  | process_supplier | supplier process type | For Example: OTA_HotelAvail | Required |  |
| 146 |  | process_result | process result | Success, Fail | Required |  |
| 147 |  | availability_result | if there are no any room is available, should be NoAvail, if process.type is Fail, should be NoAvail | Avail or NoAvail | Optional |  |
| 148 |  | supplier | derby supplier code | string,upper case | Required |  |
| 149 |  | channel | derby channel code | string,upper case | Optional |  |
| 150 |  | hotel_supplier | supplier hotel code | string | Required for single hotel request |  |
| 151 |  | echo_token | unique id for the request | string | Optional |  |
| 152 |  | check_in | checkin,format is 2015-12-24 | string | Optional |  |
| 153 |  | check_out | checkout, format is 2015-12-24 | string | Optional |  |
| 154 |  | adult_cnt | adult count | number 1-9 | Optional |  |
| 155 |  | children_cnt | children count | number 1-9 | Optional |  |
| 156 |  | children_ages | children ages. Format is 10,6 | string | Optional |  |
| 157 |  | room_cnt | room count | number 1-99 | Optional |  |
| 158 |  | los | length of stay | number | Optional |  |
| 159 |  | iata | IATA send to supplier | number string | Optional |  |
| 160 |  | trigger_source | who triggers the request | Must BE:Reservation,Manual | Optional |  |
| 162 | Single ARI Process |  |  |  |  |  |
| 163 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |  |
| 164 |  | process | SingleARIProcess | SingleARIProcess | Required |  |
| 165 |  | request_type | supplier orginal request type | string | Optional |  |
| 166 |  | process_result | Success or Fail | string | Required |  |
| 167 |  | hotel_supplier | supplier hotel code | string | Required for single hotel |  |
| 168 |  | echo_token | same a supplier request echo.token | string | Optional |  |
| 169 |  | room_type_supplier | room type. Format is "STD,TWIN" | string | Optional |  |
| 170 |  | rate_plan_supplier | rate plan. Format is "BAR,AP" | string | Optional |  |
| 171 |  | start_date | min date in the message. Format is 2015-12-24 | string | Optional |  |
| 172 |  | end_date | max date in the message. Format is 2015-12-26 | string | Optional |  |
| 173 |  | supplier | derby supplier code,upper case | string | Required |  |
| 174 |  | channel | derby channel code,upper case | string | Optional |  |
| 175 |  | wait_duration | wait in the queue time. unit is ms | number 1-999999999 | Required |  |
| 176 |  | original_timestamp | timestamp in xml message2015-12-28T13:00:00.000Z | string | Optional |  |
| 177 |  | received_timestamp | 2015-12-28T13:00:00.000Z | string | Optional |  |
| 179 | Batch ARI Process |  |  |  |  |  |
| 180 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |  |
| 181 |  | process | BatchARIProcess | BatchARIProcess | Required |  |
| 182 |  | request_type | supplier orginal request type | string | Optional |  |
| 183 |  | process_result | Success or Fail | string | Required |  |
| 184 |  | hotel_supplier | supplier hotel code | string | Optional |  |
| 185 |  | supplier | derby supplier code,upper case | string | Required |  |
| 186 |  | channel | derby channel code,upper case | string | Optional |  |
| 187 |  | wait_duration_min | minimum wait duration. unit is ms | number 1-999999999 | Required |  |
| 188 |  | wait_duration_max | maximum wait duration. unit is ms | number 1-999999999 | Required |  |
| 189 |  | wait_duration_avg | average wait duration. unit is ms | number 1-999999999 | Required |  |
| 190 |  | message_cnt | total process message count | number 1-999 | Required |  |
| 191 |  | message_fail_cnt | fail process message count | number 1-999 | Required |  |
| 192 |  | start_date | min date in all message. Format is 2015-12-24 | string | Optional |  |
| 193 |  | end_date | max date in all message. Format is 2015-12-26 | string | Optional |  |
| 194 |  | connection_type | identify EXCHANGE connection | MUST BE: Standard, Exchange | Optional |  |
| 196 | Trigger ARI Refresh Process | Call DerbySoft's internal API to trigger a ARI refresh to Supplier/Channel |  |  |  |  |
| 197 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |  |
| 198 |  | process | TriggerARIRefresh | Must BE:TriggerARIRefresh | Required |  |
| 199 |  | process_result | Success or Fail | string | Required |  |
| 200 |  | supplier | derby supplier code,upper case | string | Required |  |
| 201 |  | channel | derby channel code,upper case | string | Required |  |
| 202 |  | hotel_channel | channel hotel code | string | Optional |  |
| 203 |  | hotel_supplier | supplier hotel code | string | Optional |  |
| 204 |  | start_date | min date in the message. Format is 2015-12-24 | string | Optional |  |
| 205 |  | end_date | max date in the message. Format is 2015-12-26 | string | Optional |  |
| 206 |  | trigger_source | who triggers the request | Must BE:Reservation,Manual | Optional |  |
| 207 |  | task_id | batch trigger task id | string | Optional |  |
| 208 |  | refresh_status | trigger refresh status | string | Optional |  |
| 209 | Process Policy | Process Policy from Supplier by Email/FTP/API |  |  |  |  |
| 210 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |  |
| 211 |  | process | PolicyProcess | PolicyProcess | Required |  |
| 212 |  | process_result | Success or Fail | string | Required |  |
| 213 |  | supplier | derby supplier code,upper case | string | Required |  |
| 214 |  | channel | derby channel code,upper case | string | Required |  |
| 215 |  | hotel_channel | channel hotel code | string | Optional |  |
| 216 |  | hotel_supplier | supplier hotel code | string | Optional |  |
| 217 |  | room_type_channel | channel room type code | string | Optional |  |
| 218 |  | rate_plan_channel | channel rate plan code | string | Optional |  |
| 219 |  | room_type_supplier | supplier room type code | string | Optional |  |
| 220 |  | rate_plan_supplier | supplier rate plan code | string | Optional |  |
| 221 |  | start_date | min date in the message. Format is 2015-12-24 | string | Optional |  |
| 222 |  | end_date | max date in the message. Format is 2015-12-26 | string | Optional |  |
| 223 |  | policy_type | policy type | MUST BE: MealPlan, CancelPolicy, Fee, Guarantees, MaxOccupancy, ChildPolicy | Required |  |
| 226 | Distributor ARI Push Process | Record DerbySoft's Push Process(include Pull data internally and Push data to Channel) |  |  |  |  |
| 227 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |  |
| 228 |  | process | SyncerARIProcess | SyncerARIProcess | Required |  |
| 229 |  | process_result | Success or Fail | string | Required |  |
| 230 |  | supplier | derby supplier code,upper case | string | Required |  |
| 231 |  | channel | derby channel code,upper case | string | Required |  |
| 232 |  | hotel_channel | channel hotel code | string | Optional |  |
| 233 |  | hotel_supplier | supplier hotel code | string | Required |  |
| 234 |  | room_type_channel | channel room type code | string | Optional |  |
| 235 |  | rate_plan_channel | channel rate plan code | string | Optional |  |
| 236 |  | room_type_supplier | supplier room type code | string | Required |  |
| 237 |  | rate_plan_supplier | supplier rate plan code | string | Required |  |
| 238 |  | start_date | min date in the message. Format is 2015-12-24 | string | Optional |  |
| 239 |  | end_date | max date in the message. Format is 2015-12-26 | string | Optional |  |
| 240 |  | pop_key | synchronizer pop key value | string | Optional |  |
| 241 |  | synchronizer_duration | sum of all the durations between pusher and synchronizer | number 1-999999999 | Required |  |
| 242 |  | pop_key_duration | pop key duration, unit is ms | number 1-999999999 | Required |  |
| 243 |  | get_changes_duration | get changes duration, unit is ms | number 1-999999999 | Optional |  |
| 244 |  | report_success_duration | report success duration, unit is ms | number 1-999999999 | Optional |  |
| 245 |  | report_fail_duration | report fail duration, unit is ms | number 1-999999999 | Optional |  |
| 246 |  | ari_request_duration | air request duration, unit is ms | number 1-999999999 | Optional |  |
| 247 |  | push_skipped | true/false, true means the ARI is not pushed to distributor caused by mapping missing | boolean | Optional |  |
| 248 |  | skip_reason | the reason of the skip, could be RoomNotFound/RatePlanNotFound etc | string | Optional |  |
| 250 | Reservation Task Queue | Warrior team's reservation task queue |  |  |  |  |
| 251 |  | process | derby process type | SaveTask, PopSerialId, ConsumeTask, ReportResult | Required | 使用过程，<br>1. SaveTask, 保存一个新的任务<br>2. PopSerialId，获取一个任务队列id<br>3. ConsumeTask，根据队列id获取一个任务<br>4. ReportResult， 报告任务的结果<br>接口名称有些不合理，不过鉴于开发工程师已经达成共识，所以Process不做变更，和接口保持一致 |
| 252 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |  |
| 253 |  | process_result | process result, Fail or success | string | Required |  |
| 254 |  | echo_token | unique id for the request | string | Required |  |
| 255 |  | supplier | supplier code | string | Required |  |
| 256 |  | channel | channel code | string | Optional |  |
| 257 |  | message_type | message type | string | Required |  |
| 259 | SearchHotels |  |  |  |  |  |
| 260 |  | process | process type | Must be: SearchHotels | Required |  |
| 261 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |  |
| 262 |  | process_result | process result, Fail or success | String | Required |  |
| 263 |  | search_type | search type，Campaign,City,Brand | MUST BE：Campaign,City,Brand | Required |  |
| 264 |  | search_value | user search value for search type | String | Optional |  |
| 265 |  | check_in | checkin,format is 2015-12-24 | string | Optional |  |
| 266 |  | check_out | checkout, format is 2015-12-24 | string | Optional |  |
| 267 |  | hotel_cnt | hotel count | number 1-9999 | Optional |  |
| 268 |  | user_id | request user id if need sign on | String | Optional |  |
| 269 |  | supplier | supplier | String | Optional |  |
| 270 |  | channel | channel | String | Optional |  |
| 272 | ARI Tracing |  | ARI tracing log to trace ARI changes across different systems inside derbysoft |  |  |  |
| 273 |  | process | process type | Must be: ARIOperation | Required |  |
| 274 |  | supplier | derby supplier code | string,upper case | Required |  |
| 275 |  | channel | derby channel code | string,upper case | Optional |  |
| 276 |  | hotel_supplier | supplier hotel code | string | Required |  |
| 277 |  | room_type_supplier | supplier room type code | string | Required |  |
| 278 |  | rate_plan_supplier | supplier rate plan code | number 1-9999 | Required |  |
| 279 |  | ari_type | ari type | string | Required |  |
| 280 |  | ari_date | air date | string | Required |  |
| 281 |  | trace_id | pattern is "{supplier}\|{channel}\|{hotel.supplier}\|{room.type.supplier}\|{rate.plan.supplier}\|{ari.type}\|{ari.date}", <br>when channel do not exists, {channel} MUST BE "*"<br><br>Example A: "S1\|C1\|SH1\|SRT1\|SRP1\|DailyRate\|2023-03-08"<br>Example B: "S1\|*\|SH1\|SRT1\|SRP1\|DailyRate\|2023-03-08" | string | Required |  |
| 282 |  | ari_value | any format of string | string | Required |  |
| 283 |  | parent_trace_ids | Element pattern is "{supplier}\|{channel}\|{hotel.supplier}\|{room.type.supplier}\|{rate.plan.supplier}\|{ari.type}\|{ari.date}", <br><br>Example:<br><br>[<br>  "S1\|C1\|SH1\|SRT1\|SRP1\|DailyRate\|2023-03-08", <br>  "S2\|C2\|SH2\|SRT2\|SRP2\|DailyInventory\|2023-03-11"<br>] | array<string> | Optional |  |
| 284 |  | hotel_channel | channel hotel code | string | Optional |  |
| 285 |  | room_type_channel | channel room type code | string | Optional |  |
| 286 |  | rate_plan_channel | channel rate plan code | string | Optional |  |
| 287 |  | product | GO，PC，BUILD | string | Required |  |
| 289 | LivecheckDiff | BTS can calculate the difference between nocache and cache when it receive a LiveCheck request from TMC, then produces this log_ |  |  |  |  |
| 290 |  | process | derby process type | MUST BE:LivecheckDiff | Required |  |
| 291 |  | echo_token | unique id for the request, taskId in request header | string | Required |  |
| 292 |  | process_duration |  | number 1-999999 | Required |  |
| 293 |  | duration_details |  | string | Required |  |
| 294 |  | process_result |  | Success, Fail | Required |  |
| 295 |  | corporate_supplier | The corporate code in supplier | string | Optional |  |
| 296 |  | corporate_channel | The corporate code in channel | string | Optional |  |
| 297 |  | supplier |  | string | Optional |  |
| 298 |  | channel |  | string | Optional |  |
| 299 |  | hotel_channel | primary hotel code | string | Optional |  |
| 300 |  | hotel_supplier | supplier hotel code | string | Optional |  |
| 301 |  | room_type_supplier | supplier room type code | string | Optional |  |
| 302 |  | rate_plan_supplier | supplier rate plan code | string | Optional |  |
| 303 |  | room_cnt | room count | number 1-999999 | Optional |  |
| 304 |  | adult_cnt | adult cout | number 1-999999 | Optional |  |
| 305 |  | check_in | checkin,format is 2015-12-24 | string | Optional |  |
| 306 |  | check_out | checkout, format is 2015-12-24 | string | Optional |  |
| 307 |  | los | length of stay for ari | number 1-999999 | Optional |  |
| 308 |  | accurate | The accuracy of the cache | true,false | Required |  |
| 309 |  | accurate_amount_before_tax | The accuracy of the cached price（before tax） | true,false | Optional |  |
| 310 |  | accurate_amount_after_tax | The accuracy of the cached price（after tax） | true,false | Optional |  |
| 311 |  | accurate_availability_result | The accuracy of the cached avaiability | true,false | Optional |  |
| 312 |  | cache_source | source of lead rate cache | RegularFetch, ReservationRefresh, LivecheckRefresh, <br>LiveQueryRefresh, ProactiveFetch | Optional |  |
| 313 |  | cache_update_time | updatetime of lead rate cache | string | Optional |  |
| 315 | MT | Management Tool for AMEX operator，supporting Hotel Mapping，Corp Management，Negotiated Rate Management___ |  |  |  |  |
| 316 |  | process_duration | total process time, unit is ms |  | Required |  |
| 317 |  | process | derby process type | SaveAuditLog | Required |  |
| 318 |  | process_result | process result | Success, Fail | Required |  |
| 319 |  | category | refrence | string | Optional |  |
| 320 |  | action |  | string | Required |  |
| 321 |  | err_code |  | string | Optional |  |
| 322 |  | err_msg |  | string | Optional |  |
| 323 |  | err_code_inner_service |  | string | Optional |  |
| 324 |  | operation_user | the user name of the operation | string | Required |  |
| 325 |  | echo_token | unique id for the request | string | Required |  |
| 326 |  | supplier | supplier code | string | Optional |  |
| 327 |  | channel | channel code | string | Optional |  |
| 328 |  | hotel_supplier | supplier hotel code | string | Optional |  |
| 329 |  | hotel_derby | derby hotel code | string | Optional |  |
| 330 |  | hotel_channel | channel hotel code | string | Optional |  |
| 331 |  | corporate_supplier | The corporate code in supplier | string | Optional |  |
| 332 |  | corporate_derby | The corporate code in derby | string | Optional |  |
| 333 |  | corporate_channel | The corporate code in channel | string | Optional |  |
| 334 |  | hotel_cnt | The number of hotels that match the requirements | number 1-999999 | Optional |  |
| 335 |  | corporate_cnt | The number of corporates that match the requirements | number 1-999999 | Optional |  |
| 336 |  | product_cnt | The number of products that match the requirements | number 1-999999 | Optional |  |
| 337 |  | room_type_channel | channel room type code | string | Optional |  |
| 338 |  | rate_plan_channel | channel rate plan code | string | Optional |  |
| 339 |  | room_type_supplier | supplier room type code | string | Optional |  |
| 340 |  | rate_plan_supplier | supplier rate plan code | string | Optional |  |
| 343 | Online |  | Go Distributor online/offline hotels, codes separate by comma. |  |  |  |
| 344 |  | process_duration | total process time, unit is ms |  | Required |  |
| 345 |  | process | derby process type | MUST BE:DistributorOnlineHotels, SupplierOnlineHotels | Required |  |
| 346 |  | process_supplier | supplier process type |  | Optional |  |
| 347 |  | process_channel | channel process type |  | Optional |  |
| 348 |  | process_result | process result | Success, Fail | Required |  |
| 349 |  | supplier | derby supplier code | string,upper case | Required on supplier side |  |
| 350 |  | channel | derby channel code | string,upper case | Required on channel side |  |
| 351 |  | hotel_channel | channel hotel code | string | Optional |  |
| 352 |  | hotel_supplier | supplier hotel code | string | Optional |  |
| 355 | Plugin |  |  |  |  |  |
| 356 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |  |
| 357 |  | process | derby process type | MUST BE:GetChange, GetAvailabilityChange,GetDailyChange | Required |  |
| 358 |  | process_result | process result | Success, Fail | Required |  |
| 359 |  | supplier | derby supplier code | string,upper case | Required |  |
| 360 |  | channel | derby channel code | string,upper case | Required |  |
| 361 |  | hotel_supplier | supplier hotel code | string | Required |  |
| 362 |  | room_type_supplier | supplier room type code | string | Optional |  |
| 363 |  | rate_plan_supplier | supplier rate plan code | string | Optional |  |
| 364 |  | hotel_channel | supplier hotel code | string | Required |  |
| 365 |  | room_type_channel | supplier room type code | string | Optional |  |
| 366 |  | rate_plan_channel | supplier rate plan code | string | Optional |  |
| 368 | SyncData |  |  |  |  |  |
| 369 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |  |
| 370 |  | process | derby process type | MUST BE:SyncProfile, SyncCCS, SyncCurrency | Required |  |
| 371 |  | process_result | process result | Success, Fail | Required |  |
| 372 |  | supplier | derby supplier code | string,upper case | Optional |  |
| 373 |  | channel | derby channel code | string,upper case | Optional |  |
| 374 |  | hotel_supplier | supplier hotel code | string | Optional |  |
| 375 |  | task_name | name of the sync task | string | Optional |  |
| 376 |  | task_update_count | add or modify count | long | Optional |  |
| 377 |  | task_delete_count | delete count | long | Optional |  |
| 381 | Get Products | Call Supplier/Channel's API to get hotel's product list |  |  |  |  |
| 382 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |  |
| 383 |  | process | GetProducts | GetProduct | Required |  |
| 384 |  | process_result | Success or Fail | string | Required |  |
| 385 |  | supplier | derby supplier code,upper case | string | Required |  |
| 386 |  | channel | derby channel code,upper case | string | Required |  |
| 387 |  | hotel_channel | channel hotel code | string | Optional |  |
| 388 |  | hotel_supplier | supplier hotel code | string | Required |  |
| 392 | PropertyManagement | DerbySoft push hotel/roomType/ratePlan/product to channels |  |  |  |  |
| 393 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |  |
| 394 |  | process | process type | PropertyManagement | Required |  |
| 395 |  | request_type | channel orginal request type | string | Optional |  |
| 396 |  | process_result | Success or Fail | string | Required |  |
| 397 |  | supplier | derby supplier code,upper case | string | Required |  |
| 398 |  | channel | derby channel code,upper case | string | Required |  |
| 399 |  | hotel_channel | channel hotel code | string | Optional |  |
| 400 |  | hotel_supplier | supplier hotel code | string | Required |  |
| 401 |  | room_type_channel | channel room type code | string | Optional |  |
| 402 |  | rate_plan_channel | channel rate plan code | string | Optional |  |
| 403 |  | room_type_supplier | supplier room type code | string | Optional |  |
| 404 |  | rate_plan_supplier | supplier rate plan code | string | Optional |  |
| 405 |  | echo_token_channel | unique id for the request | string | Optional |  |
| 406 |  | echo_token_derby | unique id for the request | string | Optional |  |
| 407 |  | action_type | Specific operations performed when interacting with channel product interfaces, like:<br>Create, Update, Activate, Deactivate | string | Optional |  |
| 409 | Distributor ARI Push Process | Record DerbySoft's Push Process(include Pull data internally and Push data to Channel) |  |  |  |  |
| 410 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |  |
| 411 |  | process | SyncerARIProcess | SyncerARIProcess | Required |  |
| 412 |  | process_result | Success or Fail | string | Required |  |
| 413 |  | supplier | derby supplier code,upper case | string | Required |  |
| 414 |  | channel | derby channel code,upper case | string | Required |  |
| 415 |  | hotel_channel | channel hotel code | string | Optional |  |
| 416 |  | hotel_supplier | supplier hotel code | string | Required |  |
| 417 |  | room_type_channel | channel room type code | string | Optional |  |
| 418 |  | rate_plan_channel | channel rate plan code | string | Optional |  |
| 419 |  | room_type_supplier | supplier room type code | string | Required |  |
| 420 |  | rate_plan_supplier | supplier rate plan code | string | Required |  |
| 421 |  | start_date | min date in the message. Format is 2015-12-24 | string | Optional |  |
| 422 |  | end_date | max date in the message. Format is 2015-12-26 | string | Optional |  |
| 423 |  | pop_key | synchronizer pop key value | string | Optional |  |
| 424 |  | synchronizer_duration | sum of all the durations between pusher and synchronizer | number 1-999999999 | Required |  |
| 425 |  | pop_key_duration | pop key duration, unit is ms | number 1-999999999 | Required |  |
| 426 |  | get_changes_duration | get changes duration, unit is ms | number 1-999999999 | Optional |  |
| 427 |  | report_success_duration | report success duration, unit is ms | number 1-999999999 | Optional |  |
| 428 |  | report_fail_duration | report fail duration, unit is ms | number 1-999999999 | Optional |  |
| 429 |  | ari_request_duration | air request duration, unit is ms | number 1-999999999 | Optional |  |
| 430 |  | push_skipped | true/false, true means the ARI is not pushed to distributor caused by mapping missing | boolean | Optional |  |
| 434 | Get Product Process | Call Supplier/Channel's API to get hotel's product list |  |  |  |  |
| 435 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |  |
| 436 |  | process | GetProduct | GetProduct | Required |  |
| 437 |  | process_result | Success or Fail | string | Required |  |
| 438 |  | supplier | derby supplier code,upper case | string | Required |  |
| 439 |  | channel | derby channel code,upper case | string | Required |  |
| 440 |  | hotel_channel | channel hotel code | string | Optional |  |
| 441 |  | hotel_supplier | supplier hotel code | string | Optional |  |
| 445 | Get Policy Process | Get Policy from Supplier by Email/FTP/API |  |  |  |  |
| 446 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |  |
| 447 |  | process | GetPolicy | GetPolicy | Required |  |
| 448 |  | process_result | Success or Fail | string | Required |  |
| 449 |  | supplier | derby supplier code,upper case | string | Required |  |
| 450 |  | channel | derby channel code,upper case | string | Required |  |
| 451 |  | hotel_channel | channel hotel code | string | Optional |  |
| 452 |  | hotel_supplier | supplier hotel code | string | Optional |  |
| 453 |  | room_type_channel | channel room type code | string | Optional |  |
| 454 |  | rate_plan_channel | channel rate plan code | string | Optional |  |
| 455 |  | room_type_supplier | supplier room type code | string | Optional |  |
| 456 |  | rate_plan_supplier | supplier rate plan code | string | Optional |  |
| 457 |  | start_date | min date in the message. Format is 2015-12-24 | string | Optional |  |
| 458 |  | end_date | max date in the message. Format is 2015-12-26 | string | Optional |  |
| 459 |  | policy_type | policy type | MUST BE: MealPlan, CancelPolicy, Fee | Required |  |
| 462 | DProduct Storage | Warrior team's content storage module |  |  |  |  |
| 463 |  | process | derby process type | GetHotelContent, SaveHotelContent, UpdateHotelStatus, GetRoomTypeContent, SaveRoomTypeContent, UpdateRoomTypeStatus, GetRatePlanContent, SaveRatePlanContent, UpdateRatePlanStatus, GetProductContent, SaveProductContent, UpdateProductStatus,<br>GetHotelContentChange, GetHotelContentChangeData | Required |  |
| 464 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |  |
| 465 |  | process_result | process result, Fail or success | string | Required |  |
| 466 |  | echo_token | unique id for the request | string | Required |  |
| 467 |  | supplier | supplier code | string | Required |  |
| 468 |  | channel | channel | string | Required |  |
| 469 |  | hotel_supplier | supplier hotel code | string | Optional |  |
| 470 |  | room_type_supplier | supplier room type code | string | Optional |  |
| 471 |  | rate_plan_supplier | supplier rate plan code | string | Optional |  |
| 472 |  | content_status | for update content status process | Active, Deactive | Optional |  |
| 473 |  | cds_timestamp | cds timestamp | long | Optional |  |
| 474 |  | hotel_cnt | hotel count | number 1-9999 | Optional |  |
| 475 |  | room_type_cnt | room type count | number 1-9999 | Optional |  |
| 476 |  | rate_plan_cnt | rate plan count | number 1-9999 | Optional |  |
| 477 |  | product_cnt | product count | number 1-9999 | Optional |  |
| 478 |  | products | product list | array<string> | Optional |  |
| 481 | Reservation |  |  |  |  |  |
| 482 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |  |
| 483 |  | process | derby process type | MUST BE:Book, Modify, Cancel, Hold, Commit, ModifyHold, ModifyCommit, Ignore, BookNotify,ModifyNotify,CancelNotify, Preview,QueryRes,PostCheck, Rollback | Required |  |
| 484 |  | process_supplier | supplier process type | For Exampel: OTA_HotelRes, OTA_HotelResNotify | Optional |  |
| 485 |  | process_channel | channel process type | For Exampel: OTA_HotelRes, OTA_HotelResNotify | Optional |  |
| 486 |  | process_internal | internal system process type | internal process type, define by app team | Optional |  |
| 487 |  | process_original | original derby process type. For example, supplier adapter receive a Modify from channel. The implementation is cancel and rebook. We need to send cancel fisrt then send booking. The first cancel perf log should be: process=Cancel, process.supplier=OTA_Cancel,process.original=Modify | MUST BE:Book, Modify, Cancel, Hold, Commit, ModifyHold, ModifyCommit, Ignore, BookNotify,ModifyNotify,CancelNotify, Preview,QueryRes | Optional |  |
| 488 |  | process_result | process result | Success, Fail | Required |  |
| 489 |  | echo_token | unique id for the request | string | Optional |  |
| 491 |  | supplier | derby supplier code | string,upper case | Required on supplier end |  |
| 492 |  | channel | derby channel code | string,upper case | Required on channel end and supplier end |  |
| 494 |  | res_id_derby | derbysoft res no | string | Optional |  |
| 495 |  | res_id_supplier | supplier res no | string | Required on supplier end |  |
| 496 |  | res_id_channel | channel res no | string | Required on channel end and supplier end |  |
| 497 |  | res_id_exchange | EXCHANGE res no | string | Optional |  |
| 498 |  | cancel_confirm_id | supplier cancellation confirmation no | string | Optional |  |
| 500 |  | hotel_supplier | supplier hotel code | string | Required on supplier end |  |
| 501 |  | hotel_channel | channel hotel code | string | Required on channel end， could be empty for cancellation if we can not find the res |  |
| 503 |  | room_type_supplier | supplier room type code | string | Optional |  |
| 504 |  | rate_plan_supplier | supplier rate plan code | string | Optional |  |
| 506 |  | room_type_channel | channel room type code | string | Optional |  |
| 507 |  | rate_plan_channel | channel rate plan code | string | Optional |  |
| 509 |  | hotel_derby | derby hotel code | string | Optional |  |
| 510 |  | room_type_derby | derby room type code | string | Optional |  |
| 511 |  | rate_plan_derby | derby rate plan code | string | Optional |  |
| 513 |  | check_in | checkin,format is 2015-12-24 | string | Optional |  |
| 514 |  | check_out | checkout, format is 2015-12-24 | string | Optional |  |
| 515 |  | adult_cnt | adult cout | number 1-9 | Optional |  |
| 516 |  | children_cnt | children count | number 1-9 | Optional |  |
| 517 |  | children_ages | children ages. Format is 10,6 | string | Optional |  |
| 518 |  | room_cnt | room count | number 1-99 | Optional |  |
| 519 |  | los | length of stay | number | Optional |  |
| 521 |  | iata | IATA send to supplier | number string | Optional |  |
| 522 |  | guarantee_type | supplier guarantee type. No derby standard | string | Optional |  |
| 523 |  | card_code | see Card Code sheet | value in Card Code Sheet | Optional |  |
| 524 |  | avail_room_cnt | available room count | number | Optional |  |
| 525 |  | force_sell | is force sell or not | boolean | Optional |  |
| 526 |  | rate_override | is rate override or not | boolean | Optional |  |
| 527 |  | currency_code | currency code | string | Optional |  |
| 528 |  | total_amount | total amount | number | Optional |  |
| 529 |  | rate_amount | amount information. Like ABT:100.00 USD, AAT 120.00 USD TOTAL: 240 USD | string | Optional |  |
| 530 |  | is_customize_rate | the rate in the reservation is channel customized rate | boolean | Optional |  |
| 531 |  | order_status | Pending, Confirmed, ConfirmFailed, ModifyPending, ModifyConfirmed, ModifyFailed, CancelPending, Cancelled,CancelFailed | string | Optional |  |
| 532 |  | payment_status | MUST BE:PayWaiting,PaySuccess,PayFailed,RefundWaiting,RefundSuccess,RefundFailed | string | Optional |  |
| 533 |  | corporate_supplier | BTS only, The corporate code in supplier | string | Optional |  |
| 534 |  | corporate_derby | BTS only, The corporate code in derby | string | Optional |  |
| 535 |  | corporate_channel | BTS only, The corporate code in channel | string | Optional |  |
| 536 |  | connection_type | identify EXCHANGE connection | MUST BE: Standard, Exchange | Optional |  |
| 537 |  | request_ip | request's IP address | string | Optional |  |
| 539 | Res Retrieve |  |  |  |  |  |
| 540 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |  |
| 541 |  | process | derby process type | MUST BE:Book, Modify, Cancel, Hold, Commit, ModifyHold, ModifyCommit, Ignore, BookNotify,ModifyNotify,CancelNotify, Preview,QueryRes,PostCheck, Rollback | Required |  |
| 542 |  | process_supplier | supplier process type | For Exampel: OTA_HotelRes, OTA_HotelResNotify | Optional |  |
| 543 |  | process_channel | channel process type | For Exampel: OTA_HotelRes, OTA_HotelResNotify | Optional |  |
| 544 |  | process_original | original derby process type. For example, supplier adapter receive a Modify from channel. The implementation is cancel and rebook. We need to send cancel fisrt then send booking. The first cancel perf log should be: process=Cancel, process.supplier=OTA_Cancel,process.original=Modify | MUST BE:Book, Modify, Cancel, Hold, Commit, ModifyHold, ModifyCommit, Ignore, BookNotify,ModifyNotify,CancelNotify, Preview,QueryRes | Optional |  |
| 545 |  | process_result | process result | Success, Fail | Required |  |
| 546 |  | echo_token | unique id for the request | string | Optional |  |
| 548 |  | supplier | derby supplier code | string,upper case | Required on supplier end |  |
| 549 |  | channel | derby channel code | string,upper case | Required on channel end and supplier end |  |
| 551 |  | res_id_derby | derbysoft res no | string | Optional |  |
| 552 |  | res_id_supplier | supplier res no | string | Required on supplier end for single reservation |  |
| 553 |  | res_id_channel | channel res no | string | Required on channel end and supplier end for single reservation |  |
| 554 |  | res_id_exchange | EXCHANGE res no | string | Optional |  |
| 555 |  | cancel_confirm_id | cancellation id | string | Optional |  |
| 557 |  | hotel_supplier | supplier hotel code | string | Required on supplier end for single reservation |  |
| 558 |  | hotel_channel | channel hotel code | string | Required on channel end and supplier end for single reservation |  |
| 560 |  | book_cnt | booking count in response |  | Optional |  |
| 561 |  | cancel_cnt | cancellation count in response |  | Optional |  |
| 562 |  | modify_cnt | modification count in response |  | Optional |  |
| 564 |  | rate_amount | amount information. Like ABT:100.00 USD, AAT 120.00 USD TOTAL: 240 USD | string | Optional |  |
| 565 |  | connection_type | identify EXCHANGE connection | MUST BE: Standard, Exchange | Optional |  |
| 566 |  | request_ip | request's IP address | string | Optional |  |
| 568 | Res Ack/Report |  |  |  |  |  |
| 569 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |  |
| 570 |  | process | derby process type | MUST BE:BookReport, ModifyReport, CancelReport, HoldReport, CommitReport, ModifyHoldReport, ModifyCommitReport, IgnoreReport, RollbackReport | Required |  |
| 571 |  | process_supplier | supplier process type | For Exampel: OTA_HotelRes, OTA_HotelResNotify | Optional |  |
| 572 |  | process_channel | channel process type | For Exampel: OTA_HotelRes, OTA_HotelResNotify | Optional |  |
| 573 |  | process_original | original derby process type. For example, supplier adapter receive a Modify from channel. The implementation is cancel and rebook. We need to send cancel fisrt then send booking. The first cancel perf log should be: process=Cancel, process.supplier=OTA_Cancel,process.original=Modify | MUST BE:Book, Modify, Cancel, Hold, Commit, ModifyHold, ModifyCommit, Ignore, BookNotify,ModifyNotify,CancelNotify, Preview,QueryRes | Optional |  |
| 574 |  | process_result | process result | Success, Fail | Required |  |
| 575 |  | echo_token | unique id for the request | string | Optional |  |
| 577 |  | supplier | derby supplier code | string,upper case | Required on supplier end |  |
| 578 |  | channel | derby channel code | string,upper case | Required on channel end and supplier end |  |
| 580 |  | res_id_derby | derbysoft res no | string | Optional |  |
| 581 |  | res_id_supplier | supplier res no | string | Required on supplier end for single reservation |  |
| 582 |  | res_id_channel | channel res no | string | Required on channel end and supplier end for single reservation |  |
| 583 |  | res_id_exchange | EXCHANGE res no | string | Optional |  |
| 585 |  | hotel_supplier | supplier hotel code | string | Required on supplier end for single reservation |  |
| 586 |  | hotel_channel | channel hotel code | string | Required on channel end and supplier end for single reservation |  |
| 588 |  | book_cnt | booking count in response |  | Optional |  |
| 589 |  | cancel_cnt | cancellation count in response |  | Optional |  |
| 590 |  | modify_cnt | modification count in response |  | Optional |  |
| 591 |  | connection_type | identify EXCHANGE connection | MUST BE: Standard, Exchange | Optional |  |
| 592 |  | request_ip | request's IP address | string | Optional |  |
| 594 | Reservation Credit Card Payment |  |  |  |  |  |
| 595 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |  |
| 596 |  | process | derby process type | ResPayment | Required |  |
| 597 |  | process_result | process result | Success, Fail | Required |  |
| 598 |  | payment_op_code | payment operation code | enum | Required: must be Create,Modify, Delete, Commit |  |
| 599 |  | echo_token | unique id for the request | string | Optional |  |
| 601 |  | supplier | derby supplier code | string,upper case | Required on supplier end |  |
| 602 |  | channel | derby channel code | string,upper case | Required on channel end and supplier end |  |
| 604 |  | res_id_derby | derbysoft res no | string | Optional |  |
| 605 |  | res_id_supplier | supplier res no | string | Required on supplier end |  |
| 606 |  | res_id_channel | channel res no | string | Required on channel end and supplier end |  |
| 607 |  | res_id_exchange | EXCHANGE res no | string | Optional |  |
| 608 |  | cancel_confirm_id | supplier cancellation confirmation no | string | Optional |  |
| 610 |  | hotel_supplier | supplier hotel code | string | Required on supplier end |  |
| 611 |  | hotel_channel | channel hotel code | string | Required on channel end |  |
| 612 |  | payment_id | payment id | string | Required |  |
| 613 |  | currency_code | currency code | string | Optional |  |
| 614 |  | total_amount | total amount | number | Optional |  |
| 615 |  | connection_type | identify EXCHANGE connection | MUST BE: Standard, Exchange | Optional |  |
| 618 | PushResStay |  | GO will push reservation stay information to GO distributors, if suppliers give the stay change info |  |  |  |
| 619 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |  |
| 620 |  | process | derby process type | MUST BE:PushResStay | Required |  |
| 621 |  | process_result | process result | Success, Fail | Required |  |
| 622 |  | echo_token | unique id for the request | string | Optional |  |
| 624 |  | supplier | derby supplier code | string,upper case | Required on supplier end |  |
| 625 |  | channel | derby channel code | string,upper case | Required on channel end and supplier end |  |
| 627 |  | res_id_derby | derbysoft res no | string | Optional |  |
| 628 |  | res_id_supplier | supplier res no | string | Required on supplier end |  |
| 629 |  | res_id_channel | channel res no | string | Required on channel end and supplier end |  |
| 630 |  | res_id_exchange | EXCHANGE res no | string | Optional |  |
| 631 |  | hotel_supplier | supplier hotel code | string | Required on supplier end |  |
| 632 |  | hotel_channel | channel hotel code | string | Required on channel end， could be empty for cancellation if we can not find the res |  |
| 635 |  | check_in | checkin,format is 2015-12-24 | string | Optional |  |
| 636 |  | check_out | checkout, format is 2015-12-24 | string | Optional |  |
| 638 |  | room_status | NO_SHOW, CHECK_IN, CHECK_OUT | string | Optional |  |
| 639 |  | connection_type | identify EXCHANGE connection | MUST BE: Standard, Exchange | Optional |  |
| 642 | Reservation Disburse | MarriottMP need to record perf log for disburseFailed reservations |  |  |  |  |
| 643 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |  |
| 644 |  | process | Reservation Disburse | ReservationDisburse | Required |  |
| 645 |  | process_result | Success or Fail | string | Required |  |
| 646 |  | res_id_channel | reservation id | string | Required |  |
| 647 |  | disburse_id | reservation disburse id | string | Required |  |
| 648 |  | disburse_transaction_id | reservation disburse transaction id | string | Required |  |
| 649 |  | disburse_status | disburse status | UNDO<br>PROCESSING<br>SUCCESS<br>FAILED<br>COMMISSION_PROCESSING<br>COMMISSION_SUCCESS<br>COMMISSION_FAILED | Required |  |
| 650 |  | disburse_amount | disburse amount | double | Required |  |
| 654 | Expedia Content |  |  |  |  |  |
| 655 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |  |
| 656 |  | process | derby process type | MUST BE:AddHotel ModifyHotel DeleteHotel AddRoom ModifyRoom DeleteRoom AddRatePlan ModifyRatePlan DeleteRatePlan | Required |  |
| 657 |  | process_result | process result | Success, Fail | Required |  |
| 658 |  | supplier | derby supplier code | string,upper case | Required |  |
| 659 |  | channel | derby channel code | string,upper case | Required |  |
| 660 |  | hotel_supplier | supplier hotel code | string | Required |  |
| 661 |  | room_type_supplier | supplier room type code | string | Optional |  |
| 662 |  | rate_plan_supplier | supplier rate plan code | string | Optional |  |
| 663 |  | hotel_channel | supplier hotel code | string | Required |  |
| 664 |  | room_type_channel | supplier room type code | string | Optional |  |
| 665 |  | rate_plan_channel | supplier rate plan code | string | Optional |  |
