# Hotel Content Service

Verbatim cell values from `Perf Log Process & Fields Standardization (1).xlsx`. The row number and column letters point to the original workbook; blank cells are left blank. Formulas are retained as formulas. The workbook contains draft, conflicting and deprecated entries; do not assume every row is deployed.

| Row | A | B | C | D | E |
| ---: | --- | --- | --- | --- | --- |
| 1 | Request | Key | Comment | Value | Required/Optional |
| 2 | Error |  |  |  |  |
| 3 |  | err_code | =HYPERLINK("http://218.242.214.85/wiki/en/Dswitch_Error_Code","derby standard error code") | string | Required when process.result is Fail |
| 4 |  | err_msg | error message | string | Required when process.result is Fail. Max length is 1000. |
| 5 |  | err_hotel_cnt | error hotel count | number 1-999999999 | Optional |
| 6 |  | err_hotel_codes | error hotel codes | string | Required when err.hotel.cnt is not empty. Max length is 1000 |
| 8 | Piculus |  |  |  |  |
| 9 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |
| 10 |  | process | CollectEvent, DigestEvent,<br>ValidateEvent, RegisterEvent, <br>UpdateEvent | string | Required |
| 11 |  | process_result | Success or Fail | string | Required |
| 12 |  | context_source | Target Context.Source | string | Required |
| 13 |  | hotel_cnt | process hotel total numebr | string | Required |
| 14 |  | start_time | process start time | string/datetime | Required |
| 15 |  | script_name | process scritp name | string | Required |
| 16 |  | version | correlation of deffrent process | string | Required |
| 17 |  | process_detail | process details | string/json | Optional |
| 20 | GHR |  |  |  |  |
| 21 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |
| 22 |  | process | ContentCollectionRequest | string | Required |
| 23 |  | sub_process  | GetCollectionIDs,GetCollections,FindCollectionsByID,PutCollectionIDs,RemoveCollectionIDs<br> |  |  |
| 24 |  | process_result | Success or Fail | string | Required |
| 25 |  | collection_name | collection name (Eg. for Synxis - chain code) | string | Required for PutCollectionIDs,RemoveCollectionIDs,GetCollectionIDs |
| 26 |  | hotel_supplier | context id, code for supplier | string | Required for FindCollectionsByID |
| 27 |  | content_source_group | context identifier name customized sub source | string | Optional |
| 28 |  | content_source | source eg:FTP,WS,SFTP | string | Optional |
| 29 |  | since | last modify date 2020-07-02 07:08:42 (UTC) | time | Optional |
| 30 |  | hotel_derby | ds hotel code | string | Optional |
| 31 |  | has_changes | changed or not | boolean | Required for PutCollectionIDs,RemoveCollectionIDs |
| 32 |  | requestor_ip | user ip | string | Required |
| 33 |  | supplier | context name, hotel supplier | string | Required |
| 36 |  | process | ContextHotelRequest | string | Required |
| 37 |  | sub_process  | RegisterHotel,PutHotel,GetHotelWithContext,GetHotel,FindChangeHotels,CompletePutHotel,GetConfiguratedHotel,GetConfiguratedHotels,GetContextHotel,GetContextHotels,GetSourceHotel,GetHotels |  |  |
| 38 |  | process_result | Success or Fail | string | Required |
| 39 |  | collection_name | collection name (Eg. for Synxis - chain code) | string | Optional |
| 40 |  | hotel_supplier | context id, code for supplier | string | Optional for GetContextHotels,GetHotels,FindChangeHotels,GetConfiguratedHotels |
| 41 |  | content_source_group | context identifier name customized sub source | string | Required for GetContextHotel |
| 42 |  | content_source | source | string | Required for GetSourceHotel,CompletePutHotel |
| 43 |  | since | last modify date 2020-07-02 07:08:42 (UTC) | time | Required for FindChangeHotels |
| 44 |  | hotel_derby | hotel code (ds) | string | Optional |
| 45 |  | has_changes | changed or not | boolean | Required for PutHotel |
| 46 |  | requestor_ip | user ip | string | Required |
| 47 |  | supplier | context name, hotel supplier | string | Required |
| 50 |  | process | ContentContextRequest | string | Required |
| 51 |  | sub_process  | AppendContext,t,CommitContext,IgnoreContext,RestoreContext,GetContextIDs,GetContextIDMap |  |  |
| 52 |  | process_result | Success or Fail | string | Required |
| 53 |  | collection_name | collection name (Eg. for Synxis - chain code) | string | Optional |
| 54 |  | hotel_supplier | context id | string | Optional for GetContextIDs,GetContextIDMap |
| 55 |  | content_source_group | context identifier name customized sub source | string | Optional |
| 56 |  | content_source | source | string | Optional |
| 57 |  | since | last modify date 2020-07-02 07:08:42 (UTC) | time | Optional |
| 58 |  | hotel_derby | hotel code (ds) | string | Required for CommitContext |
| 59 |  | has_changes | changed or not | boolean | Optional |
| 60 |  | requestor_ip | user ip | string | Required |
| 61 |  | supplier | context name | string | Required |
| 64 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |
| 65 |  | process | ContentSourceRequest | string | Required |
| 66 |  | sub_process  | GetHotelSources,GetContextSources |  |  |
| 67 |  | process_result | Success or Fail | string | Required |
| 68 |  | collection_name | collection name (Eg. for Synxis - chain code) | string | Optional |
| 69 |  | hotel_supplier | context id | string | Required |
| 70 |  | content_source_group | context identifier name customized sub source | string | Optional |
| 71 |  | content_source | source | string | Optional |
| 72 |  | since | last modify date 2020-07-02 07:08:42 (UTC) | time | Optional |
| 73 |  | hotel_derby | ds hotel code | string | Optional |
| 74 |  | has_changes | changed or not | boolean | Optional |
| 75 |  | requestor_ip | user ip | string | Required |
| 76 |  | supplier | context name, hotel supplier | string | Required |
| 78 | HDG |  |  |  |  |
| 79 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |
| 80 |  | process | ContentHotelSyncRequest | string | Required |
| 81 |  | sub_process | GetHotelDescriptiveInfo,GetChangeHotels |  |  |
| 82 |  | process_result | Success or Fail | string | Required |
| 83 |  | hotel_supplier | context hotel | string | Required for GetHotelDescriptiveInfo |
| 84 |  | changed_hotel_cnt | changed hotel count | number 1-999999999 | Optional |
| 85 |  | user_id | user name | string | Optional |
| 89 | Supplier Content Collection |  |  |  |  |
| 90 |  | process_duration |  | number 1-999999999 | Required |
| 91 |  | process | CollectProperties, CollectProperty, RegisterProperty,UpdateProperty,GetProperties,GetProperty | string | Required |
| 92 |  | echo_token | unique id for the request, taskId in request header | string | Required |
| 93 |  | process_result | Success or Fail | string | Required |
| 94 |  | context_code | context id, eg: HILTON_OFFICIAL | string | Required |
| 95 |  | hotel_supplier | hotel code of supplier | string | Optional |
| 96 |  | category | resource category, eg:Hotel, GuestRoom, RatePlan, Multimedia,Other | string | Required |
| 97 |  | content_provider | content provider, eg: Supplier Official, Leonardo, Iceportal | string | Required |
| 98 |  | hotel_derby | ds hotel code | string | Optional |
| 99 |  | supplier | eg: HILTON, MARRIOTT | string | Required |
| 101 | Supplier Content Change |  |  |  |  |
| 102 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |
| 103 |  | process | CollectPropertyChange | string | Required |
| 104 |  | echo_token | unique id for the request | string | Required |
| 105 |  | category | resource category, eg:Hotel, GuestRoom, RatePlan, Multimedia,Other | string | Required |
| 106 |  | content_provider | content provider, eg: Supplier Official, Leonardo, Iceportal | string | Required |
| 107 |  | process_result | Success or Fail | string | Required |
| 108 |  | context_code | context id, eg: HILTON_OFFICIAL | string | Required |
| 109 |  | hotel_supplier | hotel code of supplier | string | Optional |
| 110 |  | since | last modify date 2020-07-02 07:08:42 (UTC) | time | Optional |
| 111 |  | change_hotel_cnt | change hotel count | number 1-999999999 | Required |
| 112 |  | change_details | change detail message | string/json | Optional |
| 113 |  | supplier | eg: HILTON, MARRIOTT | string | Required |
| 115 | Supplier Content Standardization |  |  |  |  |
| 116 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |
| 117 |  | process | StandardizeProperty | string | Required |
| 118 |  | echo_token | unique id for the request | string | Required |
| 119 |  | category | resource category, eg:Hotel, GuestRoom, RatePlan, Multimedia,Other | string | Required |
| 120 |  | content_provider | content provider, eg: Supplier Official, Leonardo, Iceportal | string | Optional |
| 121 |  | content_target_app | for which serivce, eg. GHR, Content Suite,Content Solutions | string | Optional |
| 122 |  | process_result | Success or Fail | string | Required |
| 123 |  | context_code | context id, eg: HILTON_OFFICAL | string | Required |
| 124 |  | hotel_supplier | hotel code of supplier | string | Required |
| 125 |  | hotel_derby | ds hotel code | string | Optional |
| 126 |  | supplier | eg: HILTON, MARRIOTT | string | Required |
| 128 | Distributor Content Shop |  |  |  |  |
| 129 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |
| 130 |  | process | GetProperties,GetProperty | string | Required |
| 131 |  | echo_token | unique id for the request | string | Required |
| 132 |  | content_target_app | for which serivce, eg. GHR, Content Suite,Content Solutions | string | Optional |
| 133 |  | process_result | Success or Fail | string | Required |
| 134 |  | context_code | context id, eg: HILTON_OFFICIAL | string | Required |
| 135 |  | hotel_supplier | hotel code of supplier | string | Optional |
| 136 |  | hotel_derby | ds hotel code | string | Optional |
| 137 |  | hotel_cnt | shop property count | number 1-999999999 | Optional |
| 138 |  | channel | eg: CTRIP | string | Optional |
| 139 |  | supplier | eg: HILTON, MARRIOTT | string | Required |
| 140 |  | user_id | request user id | string | Required |
| 142 | Distributor Content CDS |  |  |  |  |
| 143 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |
| 144 |  | process | GetPropertyChange | string | Required |
| 145 |  | echo_token | unique id for the request | string | Required |
| 146 |  | category | resource category, eg:Hotel, GuestRoom, RatePlan, Multimedia,Other | string | Optional |
| 147 |  | content_target_app | for which serivce, eg. GHR, Content Suite,Content Solutions | string | Optional |
| 148 |  | process_result | Success or Fail | string | Required |
| 149 |  | context_code | context id, eg: HILTON_OFFICIAL | string | Required |
| 150 |  | hotel_supplier | hotel code of supplier | string | Optional |
| 151 |  | since | last modify date 2020-07-02 07:08:42 (UTC) | time | Optional |
| 152 |  | change_hotel_cnt | change hotel count | number 1-999999999 | Required |
| 153 |  | change_details | change detail message | string/json | Optional |
| 154 |  | channel | eg: CTRIP | string | Optional |
| 155 |  | supplier | eg: HILTON, MARRIOTT | string | Required |
| 156 |  | user_id | request user id | string | Required |
| 159 | Object Management |  |  |  |  |
| 160 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |
| 161 |  | process | UpdateObject, CheckObject, ListObjects, GetObject,DeleteObject,CopyObject | string | Required |
| 162 |  | echo_token | unique id for the request | string | Required |
| 163 |  | process_result | Success or Fail | string | Required |
| 164 |  | object_key | file path | string | Required |
| 165 |  | category | resource category , eg: Property,Room,Image | string | Optional |
| 166 |  | object_scope | eg: private, public | string | Required |
| 167 |  | content_target_app | for which serivce, eg. GHR, Content Suite,Content Solutions | string | Optional |
| 168 |  | context_code | context id | string | Optional |
| 169 |  | hotel_supplier | hotel code of supplier | string | Optional |
| 170 |  | hotel_derby | ds hotel code | string | Optional |
| 171 |  | channel | eg: CTRIP | string | Optional |
| 172 |  | supplier | eg: HILTON, MARRIOTT | string | Optional |
