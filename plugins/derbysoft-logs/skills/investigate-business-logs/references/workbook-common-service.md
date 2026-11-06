# Common Service

Verbatim cell values from `Perf Log Process & Fields Standardization (1).xlsx`. The row number and column letters point to the original workbook; blank cells are left blank. Formulas are retained as formulas. The workbook contains draft, conflicting and deprecated entries; do not assume every row is deployed.

| Row | A | B | C | D | E |
| ---: | --- | --- | --- | --- | --- |
| 1 | Request | Key | Comment | Value | Required/Optional |
| 2 | CCS |  |  |  |  |
| 3 |  | process_duration | total process time, unit is ms |  | Required |
| 4 |  | process | derby process type | MUST BE:GetTopic<br>CreateTopic<br>DeleteTopic<br>Query<br>Get<br>Delete<br>Disable<br>Enable<br>AddOrUpdate<br>BatchAppend<br>GetAll<br>Cds<br>Export<br>ExportSubMapping | Required |
| 5 |  | process_result | process result | Success, Fail | Required |
| 6 |  | ccs_topic | the topic of the request |  | Required |
| 7 | Shuttle |  |  |  |  |
| 8 |  | process | 表示当前请求的Shuttle接口 | Must be one of following:<br>CreateQueue, UpdateQueue, GetQueue, DeleteQueue<br>ARITaskReFetch<br>GetPlan, CreatePlan, UpdatePlan, DeletePlan, ActivatePlan, DeactivatePlan<br>GetSchedule, SaveSchedule, DeleteSchedule, SaveHotelSchedule, ManualTriggerSchedule, ActivateFetchSchedule,DeactivateFetchSchedule,<br>FetchScheduler //Shuttle Internal process, execute every 30 seconds<br>RetryScheduler//Shuttle Internal process, execute every 5 minutes<br>CronTriggerSchedule //Shuttle Internal process, Schedule Triggered via cron expression<br>ScheduleExecuted //Shuttle Internal process, process to generate task and send to queue | Required |
| 9 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 10 |  | process_result | process result | Success, Fail | Required |
| 11 |  | err_code | error code | string | Required when process.result is Fail |
| 12 |  | err_msg | error message | string | Required when process.result is Fail. Max length is 1000. |
| 13 |  | err_code_inner_service | SLA define error code | String | Optional |
| 15 |  | task_generate_plan | Task generate plan name | String | Optional |
| 16 |  | supplier |  | String | Optional |
| 17 |  | channel |  | String | Optional |
| 18 |  | ext_arifetchplan |  | String | Optional |
| 19 |  | ext_trigger_failed_schedules |  | String | Optional |
| 21 | DRS Publisher |  | DRS publisher组件负责将DRS系统中的订单事件发送到Kafka消息中间件中 |  |  |
| 22 |  | process |  | MUST BE:<br>ReservationPublish | Required |
| 23 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 24 |  | process_result | process result | Success, Fail | Required |
| 25 |  | err_code | error code | string | Required when process.result is Fail |
| 26 |  | err_msg | error message | string | Required when process.result is Fail. Max length is 1000. |
| 27 |  | module | drs module | String | Required |
| 28 |  | drs_res_id | drs reservation id | String | Required |
| 29 |  | err_code_inner_service | SLA define error code | String | Optional |
| 30 |  | drs_topic | drs kafka topic | String | Optional |
| 31 |  | res_event_type | reservation event type | String | Optional |
| 33 | DRS Portal |  | DRS portal组件消费kafka中订单事件并将数据持久化下来，对外提供HTTP接口查询功能 |  |  |
| 34 |  | process |  | MUST BE:<br>ReservationsQuery,SaveEvent | Required |
| 35 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 36 |  | process_result | process result | Success, Fail | Required |
| 37 |  | err_code | error code | string | Required when process.result is Fail |
| 38 |  | err_msg | error message | string | Required when process.result is Fail. Max length is 1000. |
| 39 |  | module | drs module | String | Required |
| 40 |  | drs_res_id | drs reservation id | String | Required |
| 41 |  | process_http_path | process http path | String | Optional |
| 42 |  | process_http_method | process http method | String | Optional |
| 43 |  | process_http_code | process http code | String | Optional |
| 44 |  | err_code_inner_service | SLA define error code | String | Optional |
| 45 |  | drs_topic | drs kafka topic | String | Optional |
| 46 |  | res_event_type | reservation event type | String | Optional |
| 49 | SSO |  |  |  |  |
| 50 |  | process |  | MUST BE:<br>Login,Register, SendMail | Required |
| 51 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 52 |  | process_result | process result | Success, Fail | Required |
| 53 |  | user_id | request user id if need sign on | String | Optional |
| 54 |  | process_http_path | process http path | String | Optional |
| 55 |  | process_http_method | process http method | String | Optional |
| 56 |  | process_http_code | process http code | String | Optional |
| 57 |  | err_code_inner_service |  |  |  |
| 60 | finance-settlement |  |  |  |  |
| 61 |  | process | SyncInvoiceCDS:同步InvoiceData<br>RenderInvoice:渲染发票 | Must be one of following:<br>SyncInvoiceCDS<br>RenderInvoice | Required |
| 62 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 63 |  | process_result | process result | Success, Fail | Required |
| 64 |  | err_code | error code | string | Required when process.result is Fail |
| 65 |  | err_msg | error message | string | Required when process.result is Fail. Max length is 1000. |
| 66 |  | err_code_inner_service | SLA define error code | String | Optional |
| 67 |  | data_key | Invoice No.<br>发票号 | String | Required when process is RenderInvoice |
| 70 | finsettlement-invoicegenerator |  |  |  |  |
| 71 |  | process | derby process type | Must be one of following:<br>GenerateInvocie | required |
| 72 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 73 |  | process_result | process result | Success, Fail | Required |
| 74 |  | err_code | error code | string | Required when process.result is Fail |
| 75 |  | err_msg | error message | string | Required when process.result is Fail. Max length is 1000. |
| 76 |  | err_code_inner_service | SLA define error code | String | Optional |
| 77 |  | data_key | invoice config id | String | Required |
| 78 |  | trigger_source | who trigger the process | MUST BE: Auto, Manual<br>Auto: the action is trigger by cron<br>Manual: the action is trigger by user | Required |
| 79 |  | start_date | invoice计算的startDate | String | Required |
| 80 |  | end_date | invoice计算的endDate | String | Required |
| 83 | finsettlement-storage |  |  |  |  |
| 84 |  | process | derby process type | Must be one of following:<br>SaveSourceData，SaveS3DailyData, SaveS3PeriodicData | Required |
| 85 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 86 |  | process_result | process result | Success, Fail | Required |
| 87 |  | err_code | error code | string | Required when process.result is Fail |
| 88 |  | err_msg | error message | string | Required when process.result is Fail. Max length is 1000. |
| 89 |  | err_code_inner_service | SLA define error code | String | Optional |
| 90 |  | data_type | BusinessSourceDataSubject name, 表示业务源数据类型 | String | Required |
| 91 |  | data_cnt | 表示单次操作的source data count | number 1-9999999 | SaveSourceData，SaveS3DailyData, SaveS3PeriodicData |
| 92 |  | start_date | PeriodicData的start date<br>Or <br>DailyData的date<br>format:yyyyHHdd | string | Required when SaveS3DailyData, SaveS3PeriodicData |
| 93 |  | end_date | PeriodicData的end date<br>format:yyyyHHdd | string | Required when SaveS3PeriodicData |
| 96 | finsettlement-sourcedata-writer |  |  |  |  |
| 97 |  | process | SyncSourceDataCDS: CDS同步，调用数据源如DSwtichReservation cds 接口 <br>SyncSourceDataDaily: 每天的全量同步补偿<br>WriteSourceData:调用finsettlement-storage接口存储source data | Must be one of following:<br>SyncSourceDataCDS，<br>SyncSourceDataDaily,<br>WriteSourceData | Required |
| 98 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 99 |  | process_result | process result | Success, Fail | Required |
| 100 |  | err_code | error code | string | Required when process.result is Fail |
| 101 |  | err_msg | error message | string | Required when process.result is Fail. Max length is 1000. |
| 102 |  | err_code_inner_service | SLA define error code | String | Optional |
| 103 |  | cds_timestamp | cds start timestamp | long | Required when process is SyncSourceDataCDS |
| 104 |  | start_date | date for daily mode sync<br>format:yyyy-HH-dd | string | Required when process is SaveS3PeriodicData |
| 105 |  | data_type | 当process是SyncSourceDataCDS, SyncSourceDataDaily表示同步的数据类型：<br>DswitchReservation,DRSRervation,DisneyTicket,<br>Greservation<br>当Process是WriteSourceData<br>BusinessSourceDataSubject name, 表示业务源数据类型 | String | Required |
| 106 |  | data_cnt | 表示单次Sync的data count | number 1-9999 | Required |
| 110 | Credential-Manager |  | 凭证管理系统，负责管理和定时更新账号，密码等敏感数据 |  |  |
| 111 |  | process |  | MUST BE:<br>GetServiceCredential，app获取指定serviceId下，某一条credentialId对应的的凭证<br>ListServiceCredential，app获取指定service下可使用的一批凭证<br>RegisterUsedNode，app上报凭证的使用节点信息<br>CreateJwtAccessToken，EC2的场景下，提供给第三方app调用，以创建一个供app使用的API鉴权token<br>RotateJwtAccessToken，EC2的场景下，app内集成的client需要定时更新token | Required |
| 112 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 113 |  | process_result | process result | Success, Fail | Required |
| 114 |  | err_code | error code | string | Optional when process.result is Fail |
| 115 |  | err_msg | error message | string | Optional when process.result is Fail |
| 116 |  | cm_service_id | CM系统中service的id | string | Optional |
| 117 |  | cm_credential_id | CM系统中凭证的id | string | Optional |
| 118 |  | request_app_name | 发送请求的Client的AppName信息 | string | Optional |
| 121 | Customer Management - Event | Integrate with different system's event  |  |  |  |
| 122 |  | process |  | Must be:<br>HandleEvent | Required |
| 123 |  | event_source | event source: hubspot, monday, event-center | String | Required |
| 124 |  | event_id | id of the event | String | Required |
| 125 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 126 |  | process_result | process result, Fail or Success | String | Required |
| 127 |  | err_code | derby standard error code (System) | String | Optional |
| 128 |  | err_msg | Error Msg | String | Optional |
| 129 |  | echo_token | unique id for the request | String | Optional |
| 133 | Customer Management - Maintain Resource | Maintaining resources in CustomerDB |  |  |  |
| 134 |  | process |  | MUST BE: <br>MaintainCustomerDBResources | Required |
| 135 |  | process_resource_type | Resources in CustomerDB：<br><br>Company<br>CooperatedCompan<br>Service<br>CooperatedService<br>AccountIdentiy<br>Connection | String | Required |
| 136 |  | process_resource_maintain_type | operation type: CREATE,UPDATE,DELETE | String | Required |
| 137 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 138 |  | process_result | process result, Failor Success | String | Required |
| 139 |  | process_http_code | http code | 200,201, 400, 401,500 | Optional |
| 140 |  | process_http_path | http request path | String | Optional |
| 141 |  | process_http_method | http request method | GET,POST,PUT,PATCH,DELETE | Optional |
| 142 |  | err_code | derby standard error code (System) | String | Optional |
| 143 |  | err_msg | Error Msg | String | Optional |
| 144 |  | echo_token | unique id for the request | String | Optional |
| 147 | Synchronizer |  |  |  |  |
| 148 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 149 |  | process | derby process type | MUST BE:PopKey,GetChanges,ReportSuccess,ReportFail,GetKey | Required, not create log if process=PopKey,GetKey AND process.result=success AND no key in response |
| 150 |  | process_result | process result | Success, Fail | Required |
| 151 |  | supplier | derby supplier code | string,upper case | Optional，Required if process= GetChanges,ReportSuccess,ReportFail or PopKey is Success |
| 152 |  | channel | derby channel code | string,upper case | Required |
| 153 |  | hotel_supplier | supplier hotel code | string | Optional，Required if process= GetChanges,ReportSuccess,ReportFail or PopKey is Success |
| 154 |  | room_type_supplier | supplier room type code | string | Optional，Required if process= GetChanges,ReportSuccess,ReportFail or PopKey is Success |
| 155 |  | rate_plan_supplier | supplier rate plan code | string | Optional，Required if process= GetChanges,ReportSuccess,ReportFail or PopKey is Success |
| 156 |  | start_date | Start date,format is 2015-12-24 | string | Optional，Required if process= GetChanges,ReportSuccess,ReportFail or PopKey is Success |
| 157 |  | end_date | End date, format is 2015-12-24 | string | Optional，Required if process= GetChanges,ReportSuccess,ReportFail or PopKey is Success |
| 158 |  | pop_key | the key | string | Optional，Required if process= GetChanges,ReportSuccess,ReportFail or PopKey is Success |
| 159 |  | fail_code | for ReportFail | string | Required if process is ReportFail |
| 160 |  | fail_message | for ReportFail | string | Required if process is ReportFail |
| 161 |  | connection_type | identify EXCHANGE connection | MUST BE: Standard, Exchange | Optional |
| 162 | CDS |  |  |  |  |
| 163 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 164 |  | process | derby process type | MUST BE:HotelChange,LOSRateChange,DailyRateChange,InventoryChange,AvailStatusChange,LOSARIChange，HotelChangeDates,DailyARIChange | Required |
| 165 |  | process_result | process result | Success, Fail | Required |
| 166 |  | supplier | derby supplier code | string,upper case | Required |
| 167 |  | channel | derby channel code | string,upper case | Required |
| 168 |  | hotel_supplier | supplier hotel code | string | Required except HotelChange API |
| 169 |  | room_type_supplier | supplier room type code | string | Optional |
| 170 |  | rate_plan_supplier | supplier rate plan code | string | Optional |
| 171 |  | start_date | Start date,format is 2015-12-24 | string | Optional |
| 172 |  | end_date | End date, format is 2015-12-24 | string | Optional |
| 173 |  | cds_timestamp |  | long | Required except HotelChange API |
| 174 |  | hotel_cnt | hotel count | long | optional |
| 175 |  | storage_duration | backen storage/cache process duration | number | Optional |
| 176 |  | change_date_cnt | how many days are changed | number | Optional |
| 179 | API Layer/API Call |  |  |  |  |
| 180 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 181 |  | process | derby process type | MUST BE: APICall | Required |
| 182 |  | process_result | process result | Success, Fail | Required |
| 183 |  | api_id | identity of the api, name or id | string | Required |
| 184 |  | api_group | group of the api | string | Optional |
| 185 |  | api_listen_path | path that user is calling | string | Optional |
| 186 |  | api_target_path | path of the backend service | string | Optional |
| 187 |  | api_method | could be http method | Could be: GET, POST, PUT, DELETE | Optional |
| 188 |  | api_response_code | could be http response code | string | Optional |
| 189 |  | auth_user_id | user name or id who is calling the api | string | Optional |
| 190 |  | auth_token | token that identity of an user | string | Optional |
| 192 | Schdule Center |  |  |  |  |
| 193 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 194 |  | process | derby process type | MUST BE: CreateTasks, PopTasks, UpdateTaskStatus | Required |
| 195 |  | process_result | process result | Success, Fail | Required |
| 196 |  | queue_id | identity of the queue, the rule is category.template.method | string | Required |
| 197 |  | queue_consumer | the consumer of the queue | string | Optional |
| 198 |  | queue_pop_task_cnt | task count being pop from the queue per request | number 1-9999 | Required only if process is PopTasks |
| 199 |  | queue_create_task_cnt | task count being created to the queue per request | number 1-9999 | Required only if process is CreateTasks |
| 201 | Service Health Check |  |  |  |  |
| 202 |  | process | process | MUST BE: ServiceAvailCheck | Required |
| 203 |  | process_duration | total process time, unit is ms | number 1-999999999 | Required |
| 204 |  | process_result | process result | Success, Fail | Required |
| 205 |  | service_id | service ID standardization | string | Required |
| 206 |  | service_type | service ID standardization | string | Required |
| 207 |  | status_duration | unit ms, duration between last check and now | number | Required |
| 208 |  | err_code | err code | string | Optional |
| 209 |  | err_msg | err message | string | Optional |
| 210 |  | check_timestamp | timestamp of latest checking | string | Optional |
| 211 |  | pilot | set to pilot=true in 24hours after initiation | boolean | Optional |
| 214 | DDFS |  |  |  |  |
| 215 |  | process | process type | MUST BE: Retrieve, Publish, UploadFile<br>Retrieve: retrieve file according to retrieve topic config<br>Publish: publish file according to publish topic config<br>UploadFile: upload file to publish topic | Required |
| 216 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 217 |  | process_result | process result | Success, Fail | Required |
| 218 |  | trigger_source | who trigger the action | MUST BE: Auto, Manual<br>Auto: the action is trigger by cron(only when process is Retrieve or Publish)<br>Manual: the action is trigger by user(when process is Retrieve or Publish or UploadFile) | Required |
| 219 |  | err_code | error code | string | Optional |
| 220 |  | err_msg | error message | string | Optional |
| 223 | DRS |  |  |  |  |
| 224 |  | process | match with the RPC APIs of DRS | MUST BE: Identify, Create, CreateChildren, Confirm, Fail, Cancel, Update, FailResAction, PendingResAction, SuccessResAction, GetDetail, QueryDetail | Required |
| 225 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 226 |  | process_result | process result | Success, Fail | Required |
| 227 |  | err_code | error code | string | Required when process.result is Fail |
| 228 |  | err_msg | error message | string | Required when process.result is Fail. Max length is 1024. |
| 229 |  | echo_token | unique id for the request(taskId in request header) | string | Optional |
| 230 |  | supplier | supplier code | string,upper case | Required when Reservation exist |
| 231 |  | channel | channel code | string,upper case | Required when Reservation exist |
| 232 |  | supplier_hotel | supplier hotel code | string,upper case | Required when Reservation exist |
| 233 |  | check_in | checkin,format is 2015-12-24 | string | Required when Reservation exist |
| 234 |  | check_out | checkout, format is 2015-12-24 | string | Required when Reservation exist |
| 236 |  | drs_res_id | drs res id | string | Optional |
| 237 |  | drs_parent_res_id | drs parent res id | string | Required when is child res |
| 238 |  | drs_children_res_ids | drs child res ids | string | Required when is parent res, combine by comma |
| 239 |  | module_res_id | module res id, the unique identifier of a reservation.<br>can be ERSP when the res module is on supplier side, can be distributor reservation no when the res module is on distributor side.  | string | Required |
| 240 |  | module | module name | string | Required |
| 241 |  | res_id_derby | derbysoft res no, ersp | string | Optional |
| 242 |  | res_id_supplier | supplier res no | string | Optional |
| 243 |  | res_id_channel | channel res no | string | Optional |
| 244 |  | cancel_confirm_id | supplier cancellation no | string | Optional |
| 245 |  | res_status | derby res status | MUST BE: NEW, CONFIRMED, CONFIRMFAILED, CANCELLED, HOLDING, IGNORED<br><br>NEW: Initial Creating Res <br>CONFIRMED: The Res is confirmed <br>CONFIRMFAILED: The Res is confirm failed <br>CANCELLED: The Res is cancelled <br>HOLDING: The Res is Successfully Hold <br>IGNORED: The Res is Successfully Hold and then be ignored | Required when Reservation exist |
| 246 |  | res_action_type | the reservation related transaction action type | MUST BE: BOOK, QUOTE, HOLD, INITIATE, IGNORE, MODIFY, COMMIT, CANCEL, NOTIFY<br> | Required when process is Fail/FailResAction/PendingResAction/SuccessResAction |
| 247 |  | res_action_status | the reservation related transaction action status | MUST BE: SUCCESS, FAILED, PENDING, NONE | Required when process is Fail/FailResAction/PendingResAction/SuccessResAction |
| 248 |  | res_action_err_code | res action failed error code | string | Optional |
| 249 |  | res_action_err_msg | res action failed error msg, max length is 512. | string | Optional |
| 252 | HBC |  |  |  |  |
| 253 |  | component | type | hbc,hbc-portal | Required |
| 254 |  | process | derby process type | HBCAPICall, HBCApplyTopicRuleTask，HBCTopicMetricCalculateTask，HBCClientInstanceHealthCheckTask，HBCTopicSyncS3Task | Required |
| 255 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 256 |  | process_result | process result, Fail or success | String | Required |
| 257 |  | process_http_code | http code | 200, 400, 500 | Required |
| 258 |  | process_http_path | http request path | String | Required |
| 259 |  | process_http_method | http request method | GET,POST,PUT,PATCH,DELETE | Required |
| 260 |  | err_code_inner_service | SLA define error code | String | Optional |
| 261 |  | err_code | derby standard error code (System) | String | Optional |
| 262 |  | err_msg | Error Msg | String | Optional |
| 263 | Paladin |  |  |  |  |
| 264 |  | process | derby process type | MUST BE: GetProperty, SaveProperty, OverrideProperty, DeleteProperty, GetRoomType, SaveRoomTypes, OverrideRoomType, DeleteRoomType, GetRatePlan, SaveRatePlans, OverrideRatePlan, DeleteRatePlan, GetProduct, SaveProducts, OverrideProduct, DeleteProduct, GetPropertyChanges, GetPropertyChangeData | Required |
| 265 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 266 |  | process_result | process result, Fail or success | String | Required |
| 267 |  | supplier | supplier code | String | Required |
| 268 |  | err_code_inner_service | SLA define error code | String | Optional |
| 269 |  | err_code | derby standard error code (System) | String | Optional |
| 270 |  | err_msg | Error Msg | String | Optional |
| 272 | Roma |  |  |  |  |
| 274 |  | process | derby process type | Romanize | Required |
| 275 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 276 |  | process_result | process result, Fail or success | String | Required |
| 277 |  | process_http_code | http code | 200, 400, 500 | Required |
| 278 |  | version | version of the api | String | Optional |
| 279 |  | echo_token | unique id for the request, taskId in request header | string | Optional |
| 280 |  | call_google_detect | Indicate if the current request called goolge detect api: true/false | boolean | Required |
| 281 |  | call_google_translate | Indicate if the current request called goolge translate api: true/false | boolean | Required |
| 284 | Secure Store |  |  |  |  |
| 285 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 286 |  | process | derby process type | MUST BE:SaveSensitiveData,GetSensitiveData | Required |
| 287 |  | process_result | process result | Success, Fail | Required |
| 288 |  | echo_token | unique id for the request | string | Optional |
| 289 |  | data_key | the key of the data. Normally returned by SaveSensitiveData | string | Required |
| 290 |  | data_size | the size of the value | number 1-99999999999 | Optional |
| 291 |  | data_type | the type of the data. | Must be: Payment, Privacy, Other | Optional |
| 293 |  | supplier | derby supplier code. The application who call SDC/PDC is suggested to log it | string,upper case | Optional |
| 294 |  | channel | derby channel code. The application who call SDC/PDC is suggested to log it | string,upper case | Optional |
| 296 |  | res_id_derby | derbysoft res no. The application who call SDC/PDC is suggested to log it | string | Optional |
| 297 |  | res_id_supplier | supplier res no. The application who call SDC/PDC is suggested to log it | string | Optional |
| 298 |  | res_id_channel | channel res no.The application who call SDC/PDC is suggested to log it | string | Optional |
