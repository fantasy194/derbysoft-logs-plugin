# AMEX Project

Verbatim cell values from `Perf Log Process & Fields Standardization (1).xlsx`. The row number and column letters point to the original workbook; blank cells are left blank. Formulas are retained as formulas. The workbook contains draft, conflicting and deprecated entries; do not assume every row is deployed.

| Row | A | B | C | D | E |
| ---: | --- | --- | --- | --- | --- |
| 1 | Request | Key | Comment | Value | Required/Optional |
| 2 | SearchHotels |  |  |  |  |
| 3 |  | process | search the primary hotel list based on the specified criteria | MUST BE:SearchHotels | Required |
| 4 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 5 |  | err_code |  | string | Optional |
| 6 |  | err_msg |  | string | Optional |
| 7 |  | err_code_inner_service |  | string | Optional |
| 8 |  | process_result |  | Success, Fail | Required |
| 9 |  | process_duration |  | number 1-99999999999 | Required |
| 10 |  | client_type | client type, such as OBT and NTC | string | Optional |
| 11 |  | channel | derby channel code,upper case | string | Optional |
| 12 |  | corporate_supplier | The corporate code in supplier | string | Optional |
| 13 |  | corporate_derby | The corporate code in derby | string | Optional |
| 14 |  | corporate_channel | The corporate code in channel | string | Optional |
| 15 |  | country_code | country code | string | Optional |
| 16 |  | city_code | city code | string | Optional |
| 17 |  | city_type | city library types | string | Optional |
| 18 |  | check_in |  | string | Optional |
| 19 |  | check_out |  | string | Optional |
| 20 |  | adult_cnt |  | number 1-999999 | Optional |
| 21 |  | children_cnt |  | number 1-999999 | Optional |
| 22 |  | room_cnt |  | number 1-999999 | Optional |
| 23 |  | match_hotel_cnt | number of hotels hit by search engine | number 1-999999 | Optional |
| 24 |  | no_mapping_cnt | no mapping hotels number | number 1-999999 | Optional |
| 25 |  | no_ari_cnt | no ari hotels number | number 1-999999 | Optional |
| 26 |  | page_index | The page number specified in the request | number 1-999999 | Optional |
| 27 |  | page_size | The number per page specified in the request | number 1-999999 | Optional |
| 28 |  | corp_contract_condition | request corp hotel or not | boolean | Optional |
| 29 |  | preferred_hotel_condition | request preferred hotel or not | boolean | Optional |
| 30 |  | noncorp_contract_condition | request noncorp hotel or not | boolean | Optional |
| 31 |  | hotel_cnt | The number of hotels that match the requirements | number 1-999999 | Optional |
| 33 | SingleHotelQuery |  |  |  |  |
| 34 |  | process | gets the product list of all associated supplier hotels for the specified master hotel, based on the criteria | MUST BE:SingleHotelQuery | Required |
| 35 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 36 |  | err_code |  | string | Optional |
| 37 |  | err_msg |  | string | Optional |
| 38 |  | err_code_inner_service |  | string | Optional |
| 39 |  | process_result |  | Success, Fail | Required |
| 40 |  | process_duration |  | number 1-99999999999 | Required |
| 41 |  | client_type | client type, such as OBT and NTC | string | Optional |
| 42 |  | channel | derby channel code,upper case | string | Optional |
| 43 |  | corporate_supplier | The corporate code in supplier | string | Optional |
| 44 |  | corporate_derby | The corporate code in derby | string | Optional |
| 45 |  | corporate_channel | The corporate code in channel | string | Optional |
| 46 |  | check_in |  | string | Optional |
| 47 |  | check_out |  | string | Optional |
| 48 |  | adult_cnt |  | number 1-999999 | Optional |
| 49 |  | children_cnt |  | number 1-999999 | Optional |
| 50 |  | room_cnt |  | number 1-999999 | Optional |
| 51 |  | hotel_channel | primary hotel code | string | Optional |
| 52 |  | hotel_supplier | code of all supplier hotels associated with the primary hotel, separated by comma | string | Optional |
| 53 |  | product_cnt | The number of products that match the requirements | number 1-999999 | Optional |
| 54 |  | corp_contract_condition | request corp hotel or not | boolean | Optional |
| 55 |  | preferred_hotel_condition | request preferred hotel or not | boolean | Optional |
| 56 |  | noncorp_contract_condition | request noncorp hotel or not | boolean | Optional |
| 58 | HotelsPrompt |  |  |  |  |
| 59 |  | process | search hotels on index information according to the keyword conditions quickly; | MUST BE:HotelsPrompt | Required |
| 60 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 61 |  | err_code |  | string | Optional |
| 62 |  | err_msg |  | string | Optional |
| 63 |  | err_code_inner_service |  | string | Optional |
| 64 |  | process_result |  | Success, Fail | Required |
| 65 |  | process_duration |  | number 1-99999999999 | Required |
| 66 |  | client_type | client type, such as OBT and NTC | string | Optional |
| 67 |  | channel | derby channel code,upper case | string | Optional |
| 68 |  | corporate_supplier | The corporate code in supplier | string | Optional |
| 69 |  | corporate_derby | The corporate code in derby | string | Optional |
| 70 |  | corporate_channel | The corporate code in channel | string | Optional |
| 71 |  | country_code | country code | string | Optional |
| 72 |  | city_code | city code | string | Optional |
| 73 |  | city_type | city library types | string | Optional |
| 74 |  | keyword_type | keyword type | string | Optional |
| 75 |  | keyword_value | keyword value | string | Optional |
| 76 |  | match_hotel_cnt | number of hotels hit by search engine | number 1-999999 | Optional |
| 77 |  | hotel_cnt_limit | number of hotels requested by the customer | number 1-999999 | Optional |
| 78 |  | hotel_cnt | number of valid hotels | number 1-999999 | Optional |
| 80 | FetchARI |  |  |  |  |
| 81 |  | process | batch get ari from supplier | MUST BE:FetchARI | Required |
| 82 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 83 |  | process_duration |  | number 1-999999 | Required |
| 84 |  | duration_details |  | string | Required |
| 85 |  | process_result |  | Success, Fail | Required |
| 86 |  | echo_token_derby | unique id for the request | string | Optional |
| 87 |  | channel | derby channel code,upper case | string | Optional |
| 88 |  | supplier | derby supplier code,upper case | string | Optional |
| 89 |  | hotel_supplier | supplier hotel code | string | Optional |
| 90 |  | check_in | checkin,format is 2015-12-24 | string | Optional |
| 91 |  | check_out | checkout, format is 2015-12-24 | string | Optional |
| 92 |  | adult_cnt | adult cout | number 1-999999 | Optional |
| 93 |  | corporate_supplier | The corporate code in supplier | string | Optional |
| 94 |  | corporate_derby | The corporate code in derby | string | Optional |
| 95 |  | corporate_channel | The corporate code in channel | string | Optional |
| 96 |  | task_priority | task priority | string | Optional |
| 97 |  | trigger_source | who triggers the request | Must BE:Atomic Task,Manual | Optional |
| 98 |  | hotel_cnt | hotel count by request | number 1-999999 | Optional |
| 99 |  | suppler_hotel_cnt | hotel count from supplier | number 1-999999 | Optional |
| 101 | SaveRawStorage |  |  |  |  |
| 102 |  | process | save data to RawStorage | MUST BE:SaveRawStorage | Required |
| 103 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 104 |  | process_duration |  | number 1-999999 | Required |
| 105 |  | duration_details |  | string | Required |
| 106 |  | process_result |  | Success, Fail | Required |
| 107 |  | adult_cnt | adult count | number 1-999999 | Optional |
| 108 |  | change_mask |  | number 1-999999;1:change,0:not change | Optional |
| 109 |  | channel | derby channel code,upper case | string | Optional |
| 110 |  | check_in | checkin,format is 2015-12-24 | string | Optional |
| 111 |  | check_out | checkout, format is 2015-12-24 | string | Optional |
| 112 |  | data_key | messageId from RawStorage | string | Optional |
| 113 |  | echo_token_derby | unique id for the request | string | Optional |
| 114 |  | hotel_supplier | supplier hotel code | string | Optional |
| 115 |  | pop_key | taskId from RawStorage | string | Optional |
| 116 |  | supplier |  | string | Optional |
| 117 |  | data_type | data type | string | Optional |
| 119 | FetchHotelContent |  |  |  |  |
| 120 |  | process | get hotel content from supplier | MUST BE:FetchHotelContent | Required |
| 121 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 122 |  | process_duration |  | number 1-999999 | Required |
| 123 |  | duration_details |  | string | Required |
| 124 |  | process_result |  | Success, Fail | Required |
| 125 |  | echo_token_derby | unique id for the request | string | Optional |
| 126 |  | channel | derby channel code,upper case | string | Optional |
| 127 |  | supplier |  | string | Optional |
| 128 |  | hotel_supplier |  | string | Optional |
| 129 |  | pop_key | taskId from RawStorage | string | Optional |
| 130 |  | data_key | messageId from RawStorage | string | Optional |
| 133 | CreateTasks |  |  |  |  |
| 134 |  | process | create task | MUST BE:CreateTasks | Required |
| 135 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 136 |  | process_duration |  | number 1-999999 | Required |
| 137 |  | duration_details |  | string | Required |
| 138 |  | process_result |  | Success, Fail | Required |
| 139 |  | echo_token_derby | unique id for the request | string | Optional |
| 140 |  | task_priority | task priority | string | Optional |
| 141 |  | task_type | task type,for example,Ari or Content | string | Optional |
| 142 |  | max_los | max los for this batch | number 1-999999 | Optional |
| 143 |  | max_adults | max adults for this batch | number 1-999999 | Optional |
| 144 |  | max_days | max days for this batch | number 1-999999 | Optional |
| 145 |  | start_date | min date for this batch. Format is 2015-12-24 | string | Optional |
| 146 |  | trigger_source | who triggers the request | Must BE:Atomic Task,Manual | Optional |
| 147 |  | supplier |  | string | Optional |
| 148 |  | channel | derby channel code,upper case | string | Optional |
| 149 |  | hotel_no_negotiated_cnt | no negotiated hotel count | number 1-999999 | Optional |
| 150 |  | hotel_negotiated_cnt | negotiated hotel count | number 1-999999 | Optional |
| 151 |  | since | last modify date 2020-07-02 07:08:42 (UTC) | string | Optional |
| 152 |  | data_cnt | total number of hotels that need to generate tasks | number 1-999999 | Optional |
| 153 | CloseHotelContent |  |  |  |  |
| 154 |  | process | receive hotel offline tasks | MUST BE:CloseHotelContent | Required |
| 155 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 156 |  | process_duration |  | number 1-999999 | Required |
| 157 |  | duration_details |  | string | Required |
| 158 |  | process_result |  | Success, Fail | Required |
| 159 |  | echo_token_derby | unique id for the request | string | Optional |
| 160 |  | channel | derby channel code,upper case | string | Optional |
| 161 |  | supplier |  | string | Optional |
| 162 |  | hotel_supplier |  | string | Optional |
| 163 |  | pop_key | taskId from RawStorage | string | Optional |
| 164 |  | data_key | messageId from RawStorage | string | Optional |
| 166 | ConsumeHotelContent |  |  |  |  |
| 167 |  | process | get hotel info from rawstorage | MUST BE:ConsumeHotelContent | Required |
| 168 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 169 |  | process_duration |  | number 1-999999 | Required |
| 170 |  | duration_details |  | string | Required |
| 171 |  | process_result |  | Success, Fail | Required |
| 172 |  | echo_token_derby | unique id for the request | string | Optional |
| 173 |  | channel | derby channel code,upper case | string | Optional |
| 174 |  | supplier |  | string | Optional |
| 175 |  | pop_key | taskId from RawStorage | string | Optional |
| 176 |  | data_key | messageId from RawStorage | string | Optional |
| 177 |  | hotel_supplier |  | string | Optional |
| 178 |  | hotel_channel_validated | valid by channel judging condition | boolean | Optional |
| 180 | CloseHotelContentProcess |  |  |  |  |
| 181 |  | process | process close hotel task | MUST BE:CloseHotelContentProcess | Required |
| 182 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 183 |  | process_duration |  | number 1-999999 | Required |
| 184 |  | duration_details |  | string | Required |
| 185 |  | process_result |  | Success, Fail | Required |
| 186 |  | echo_token_derby | unique id for the request | string | Optional |
| 187 |  | channel | derby channel code,upper case | string | Optional |
| 188 |  | supplier |  | string | Optional |
| 189 |  | pop_key | taskId from RawStorage | string | Optional |
| 190 |  | data_key | messageId from RawStorage | string | Optional |
| 191 |  | hotel_supplier | supplier hotel code | string | Optional |
| 193 | ConsumeARI |  |  |  |  |
| 194 |  | process | get ari from rawstorage | MUST BE:ConsumeARI | Required |
| 195 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 196 |  | process_duration |  | number 1-999999 | Required |
| 197 |  | duration_details |  | string | Required |
| 198 |  | process_result |  | Success, Fail | Required |
| 199 |  | echo_token_derby | unique id for the request | string | Optional |
| 200 |  | channel | derby channel code,upper case | string | Optional |
| 201 |  | supplier |  | string | Optional |
| 202 |  | pop_key | taskId from RawStorage | string | Optional |
| 203 |  | data_key | messageId from RawStorage | string | Optional |
| 204 |  | hotel_supplier | supplier hotel code | string | Optional |
| 206 | GetChanges |  |  |  |  |
| 207 |  | process | get hotel list of ari changes | MUST BE:GetChanges | Required |
| 208 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 209 |  | process_duration |  | number 1-999999 | Required |
| 210 |  | duration_details |  | string | Required |
| 211 |  | process_result |  | Success, Fail | Required |
| 212 |  | echo_token_derby | unique id for the request | string | Optional |
| 213 |  | check_in | checkin,format is 2015-12-24 | string | Optional |
| 214 |  | task_priority | task priority | string | Optional |
| 215 |  | channel | derby channel code,upper case | string | Optional |
| 216 |  | supplier |  | string | Optional |
| 217 |  | data_cnt | the total number of hotel for this batch | number 1-999999 | Optional |
| 218 |  | corporate_supplier | The corporate code in supplier | string | Optional |
| 219 |  | corporate_derby | The corporate code in derby | string | Optional |
| 220 |  | corporate_channel | The corporate code in channel | string | Optional |
| 221 |  | max_los | max los for this batch | number 1-999999 | Optional |
| 222 |  | max_adults | max adults for this batch | number 1-999999 | Optional |
| 223 |  | max_days | max days for this batch | number 1-999999 | Optional |
| 224 |  | data_change_cnt | number of change ari data | number 1-999999 | Optional |
| 225 |  | data_no_change_cnt | number of no change ari data | number 1-999999 | Optional |
| 227 | GetHotels |  |  |  |  |
| 228 |  | process | get Hotel from supplier website,sync to storage medium | MUST BE:GetHotels | Required |
| 229 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 230 |  | process_duration |  | number 1-999999 | Required |
| 231 |  | duration_details |  | string | Required |
| 232 |  | process_result |  | Success, Fail | Required |
| 233 |  | echo_token_derby | unique id for the request | string | Optional |
| 234 |  | data_cnt | the total number of hotel | number 1-999999 | Optional |
| 235 |  | supplier |  | string | Optional |
| 237 | SingleHotelContentProcess |  |  |  |  |
| 238 |  | process | process hotel task | MUST BE:SingleHotelContentProcess | Required |
| 239 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 240 |  | process_duration |  | number 1-999999 | Required |
| 241 |  | duration_details |  | string | Required |
| 242 |  | process_result |  | Success, Fail | Required |
| 243 |  | echo_token_derby | unique id for the request | string | Optional |
| 244 |  | channel | derby channel code,upper case | string | Optional |
| 245 |  | supplier |  | string | Optional |
| 246 |  | pop_key | taskId from RawStorage | string | Optional |
| 247 |  | data_key | messageId from RawStorage | string | Optional |
| 248 |  | hotel_supplier | supplier hotel code | string | Optional |
| 249 |  | hotel_channel_validated | valid by channel judging condition | boolean |  |
| 252 | SingleARIProcess |  |  |  |  |
| 253 |  | process | process ari task | MUST BE:SingleARIProcess | Required |
| 254 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 255 |  | process_duration |  | number 1-999999 | Required |
| 256 |  | duration_details |  | string | Required |
| 257 |  | process_result |  | Success, Fail | Required |
| 258 |  | echo_token_derby | unique id for the request | string | Optional |
| 259 |  | channel | derby channel code,upper case | string | Optional |
| 260 |  | supplier |  | string | Optional |
| 261 |  | pop_key | taskId from RawStorage | string | Optional |
| 262 |  | data_key | messageId from RawStorage | string | Optional |
| 263 |  | hotel_supplier | supplier hotel code | string | Optional |
| 265 | CloseAriProcess |  |  |  |  |
| 266 |  | process | process close ari task | MUST BE:CloseAriProcess | Required |
| 267 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 268 |  | process_duration |  | number 1-999999 | Required |
| 269 |  | duration_details |  | string | Required |
| 270 |  | process_result |  | Success, Fail | Required |
| 271 |  | echo_token_derby | unique id for the request | string | Optional |
| 272 |  | channel | derby channel code,upper case | string | Optional |
| 273 |  | supplier |  | string | Optional |
| 274 |  | hotel_supplier | supplier hotel code | string | Optional |
| 275 |  | check_in | checkin,format is 2015-12-24 | string | Optional |
| 276 |  | adult_cnt | adult cout | number 1-999999 | Optional |
| 277 |  | max_los | max los for this batch | number 1-999999 | Optional |
| 278 |  | corporate_supplier | The corporate code in supplier | string | Optional |
| 279 |  | corporate_derby | The corporate code in derby | string | Optional |
| 280 |  | corporate_channel | The corporate code in channel | string | Optional |
| 281 |  | ari_closed_type | ALL，Nego，Non-Nego | string | Optional |
| 283 | PublishEvent |  |  |  |  |
| 284 |  | process | publish event | MUST BE:PublishEvent | Required |
| 285 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 286 |  | process_duration |  | number 1-999999 | Required |
| 287 |  | duration_details |  | string | Required |
| 288 |  | process_result |  | Success, Fail | Required |
| 289 |  | channel | derby channel code,upper case | string | Optional |
| 290 |  | supplier |  | string | Optional |
| 291 |  | hotel_channel | primary hotel code | string | Optional |
| 292 |  | sub_process | the sub operation in process | string | Optional |
| 293 |  | event_topic | event topic | string | Optional |
| 294 |  | event_type | event type | string | Optional |
| 296 | ConsumeEvent |  |  |  |  |
| 297 |  | process | consume event | MUST BE:ConsumeEvent | Required |
| 298 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 299 |  | process_duration |  | number 1-999999 | Required |
| 300 |  | duration_details |  | string | Required |
| 301 |  | process_result |  | Success, Fail | Required |
| 302 |  | channel | derby channel code,upper case | string | Optional |
| 303 |  | supplier |  | string | Optional |
| 304 |  | hotel_channel | primary hotel code | string | Optional |
| 305 |  | sub_process | the sub operation in process | string | Optional |
| 306 |  | event_topic | event topic | string | Optional |
| 307 |  | event_type | event type | string | Optional |
| 309 | GetAvailability |  |  |  |  |
| 310 |  | process | derby process type | MUST BE:GetAvailability | Required |
| 311 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 312 |  | process_duration |  | number 1-999999 | Required |
| 313 |  | duration_details |  | string | Required |
| 314 |  | process_result |  | Success, Fail | Required |
| 315 |  | corporate_supplier | The corporate code in supplier | string | Optional |
| 316 |  | corporate_derby | The corporate code in derby | string | Optional |
| 317 |  | corporate_channel | The corporate code in channel | string | Optional |
| 318 |  | supplier |  | string | Optional |
| 319 |  | channel |  | string | Optional |
| 320 |  | hotel_channel | primary hotel code | string | Optional |
| 321 |  | hotel_supplier | supplier hotel code | string | Optional |
| 322 |  | room_type_supplier | supplier room type code | string | Optional |
| 323 |  | rate_plan_supplier | supplier rate plan code | string | Optional |
| 324 |  | room_cnt | room count | number 1-999999 | Optional |
| 325 |  | adult_cnt | adult cout | number 1-999999 | Optional |
| 326 |  | check_in | checkin,format is 2015-12-24 | string | Optional |
| 327 |  | check_out | checkout, format is 2015-12-24 | string | Optional |
| 328 |  | start_date | ari start date | string | Optional |
| 329 |  | los | length of stay for ari | number 1-999999 | Optional |
| 330 |  | trigger_source | who triggers the request | string | Optional |
| 332 | Book/Modify/Cancel/QueryRes |  |  |  |  |
| 333 |  | process | derby process type | MUST BE:Book/Modify/Cancel/QueryRes | Required |
| 334 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 335 |  | process_duration |  | number 1-999999 | Required |
| 336 |  | duration_details |  | string | Required |
| 337 |  | process_result |  | Success, Fail | Required |
| 338 |  | corporate_supplier | The corporate code in supplier | string | Optional |
| 339 |  | corporate_derby | The corporate code in derby | string | Optional |
| 340 |  | corporate_channel | The corporate code in channel | string | Optional |
| 341 |  | supplier |  | string | Optional |
| 342 |  | channel |  | string | Optional |
| 343 |  | res_id_channel | channel res no | string | Optional |
| 344 |  | res_id_derby | derbysoft res no | string | Optional |
| 345 |  | drs_res_id | drs reservation id | string | Optional |
| 346 |  | hotel_channel | primary hotel code | string | Optional |
| 347 |  | hotel_supplier | supplier hotel code | string | Optional |
| 348 |  | room_type_supplier | supplier room type code | string | Optional |
| 349 |  | rate_plan_supplier | supplier rate plan code | string | Optional |
| 350 |  | room_cnt | room count | number 1-999999 | Optional |
| 351 |  | adult_cnt | adult cout | number 1-999999 | Optional |
| 352 |  | check_in | checkin,format is 2015-12-24 | string | Optional |
| 353 |  | check_out | checkout, format is 2015-12-24 | string | Optional |
| 354 |  | currency_code | currency code | string | Optional |
| 355 |  | guarantee_type | supplier guarantee type. No derby standard | string | Optional |
| 356 |  | payment_type | payment type | string | Optional |
| 357 |  | total_amount | total amount | number | Optional |
| 358 |  | order_status_supplier | supplier orde status | string | Optional |
| 360 | SaveHotelContent |  |  |  |  |
| 361 |  | process | save hotel content | MUST BE:SaveHotelContent | Required |
| 362 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 363 |  | process_duration |  | number 1-999999 | Required |
| 364 |  | duration_details |  | string | Required |
| 365 |  | process_result |  | Success, Fail | Required |
| 366 |  | channel |  | string | Optional |
| 367 |  | supplier |  | string | Optional |
| 368 |  | hotel_supplier | supplier hotel code | string | Optional |
| 369 |  | room_type_supplier | supplier room type code | string | Optional |
| 370 |  | room_type_cnt | room type count | number 1-999999 | Optional |
| 371 |  | increment | incremental update(diff company own  hotel diff products ) | boolean | Optional |
| 372 |  | trigger_source | who triggers the request | string | Optional |
| 373 |  | hotel_content_status | supplier hotel status | Active, Deactive | Optional |
| 374 |  | hotel_name_supplier | supplier hotel name | string | Optional |
| 375 |  | location_latitude_supplier | supplier hotel location latitude | number | Optional |
| 376 |  | location_longitude_supplier | supplier hotel location longitude | number | Optional |
| 378 | SaveRoomTypeContent |  |  |  |  |
| 379 |  | process | save hotel roomType | MUST BE:SaveRoomTypeContent | Required |
| 380 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 381 |  | process_duration |  | number 1-999999 | Required |
| 382 |  | duration_details |  | string | Required |
| 383 |  | process_result |  | Success, Fail | Required |
| 384 |  | supplier |  | string | Optional |
| 385 |  | hotel_supplier | supplier hotel code | string | Optional |
| 386 |  | room_type_supplier | supplier room type code | string | Optional |
| 387 |  | room_type_cnt | room type count | number 1-999999 | Optional |
| 388 |  | trigger_source | who triggers the request | string | Optional |
| 390 | UpdateHotelStatus | process | update hotel status | MUST BE:UpdateHotelStatus | Required |
| 391 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 392 |  | process_duration |  | number 1-999999 | Required |
| 393 |  | duration_details |  | string | Required |
| 394 |  | process_result |  | Success, Fail | Required |
| 395 |  | hotel_content_status | content status | Active, Deactive | Optional |
| 396 |  | hotel_supplier | supplier hotel code | string | Optional |
| 398 | GetHotelContent |  |  |  |  |
| 399 |  | process | get hotel content | MUST BE:GetHotelContent | Required |
| 400 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 401 |  | process_duration |  | number 1-999999 | Required |
| 402 |  | duration_details |  | string | Required |
| 403 |  | process_result |  | Success, Fail | Required |
| 404 |  | channel |  | string | Optional |
| 405 |  | supplier |  | string | Optional |
| 406 |  | keyword_type | keyword type | string | Optional |
| 407 |  | keyword_value | keyword value | string | Optional |
| 408 |  | sub_process | the sub operation in process | string | Optional |
| 409 |  | hotel_supplier | supplier hotel code | string | Optional |
| 410 |  | country_code | country code | string | Optional |
| 411 |  | city_code | city code | string | Optional |
| 413 | SaveDistributorHotel |  |  |  |  |
| 414 |  | process | save distributor hotel | MUST BE:SaveDistributorHotel | Required |
| 415 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 416 |  | process_duration |  | number 1-999999 | Required |
| 417 |  | duration_details |  | string | Required |
| 418 |  | process_result |  | Success, Fail | Required |
| 419 |  | channel |  | string | Optional |
| 420 |  | supplier |  | string | Optional |
| 421 |  | hotel_supplier | supplier hotel code | string | Optional |
| 422 |  | hotel_status_channel | channel hotel status | Active, Deactive | Optional |
| 424 | SaveARI |  |  |  |  |
| 425 |  | process | save hotel ari | MUST BE:SaveARI | Required |
| 426 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 427 |  | process_duration |  | number 1-999999 | Required |
| 428 |  | duration_details |  | string | Required |
| 429 |  | process_result |  | Success, Fail | Required |
| 430 |  | channel |  | string | Optional |
| 431 |  | supplier |  | string | Optional |
| 432 |  | hotel_supplier | supplier hotel code | string | Optional |
| 433 |  | rate_plan_supplier | supplier rate plan code | string | Optional |
| 434 |  | rate_plan_cnt | supplier rate plan count | number 1-999999 | Optional |
| 435 |  | room_type_supplier | supplier room type code | string | Optional |
| 436 |  | room_type_cnt | supplier room type count | number 1-999999 | Optional |
| 437 |  | start_date | ari start date | string | Optional |
| 438 |  | los | length of stay | number 1-999999 | Optional |
| 439 |  | adult_cnt | adult cout | number 1-999999 | Optional |
| 440 |  | trigger_source | who triggers the request | string | Optional |
| 442 | CloseARI |  |  |  |  |
| 443 |  | process | deactivate hotel ari | MUST BE:CloseARI | Required |
| 444 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 445 |  | process_duration |  | number 1-999999 | Required |
| 446 |  | duration_details |  | string | Required |
| 447 |  | process_result |  | Success, Fail | Required |
| 448 |  | channel |  | string | Optional |
| 449 |  | supplier |  | string | Optional |
| 450 |  | hotel_supplier | supplier hotel code | string | Optional |
| 451 |  | check_in | checkin,format is 2015-12-24 | string | Optional |
| 452 |  | adult_cnt | adult cout | number 1-999999 | Optional |
| 453 |  | los | the length of stay |  | Optional |
| 454 |  | ari_closed_type | ALL，Nego，Non-Nego | string | Optional |
| 455 |  | corporate_supplier | The corporate code in supplier | string | Optional |
| 456 |  | corporate_derby | The corporate code in derby | string | Optional |
| 457 |  | corporate_channel | The corporate code in channel | string | Optional |
| 458 |  | start_date | ari start date | string | Optional |
| 459 |  | max_los | max los for this batch | number 1-999999 |  |
| 460 |  | max_adults | max adults for this batch | number 1-999999 | Optional |
| 461 |  | max_days | max days for this batch | number 1-999999 | Optional |
| 463 | GetARISummary |  |  |  |  |
| 464 |  | process | get hotel ari summary  | MUST BE:GetARISummary | Required |
| 465 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 466 |  | process_duration |  | number 1-999999 | Required |
| 467 |  | duration_details |  | string | Required |
| 468 |  | process_result |  | Success, Fail | Required |
| 469 |  | channel |  | string | Optional |
| 470 |  | supplier |  | string | Optional |
| 471 |  | hotel_supplier | supplier hotel code | string | Optional |
| 472 |  | start_date | ari start date | string | Optional |
| 473 |  | adult_cnt | adult count | number 1-999999 | Optional |
| 474 |  | los | length of stay for ari | number 1-999999 | Optional |
| 475 |  | trigger_source | who triggers the request | string | Optional |
