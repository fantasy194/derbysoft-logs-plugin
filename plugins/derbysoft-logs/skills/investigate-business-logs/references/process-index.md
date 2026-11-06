# Process index

This is a navigational index of rows whose key is `process`; it preserves the workbook’s descriptions and process specifications, including typos, inconsistent delimiters, explanatory prose and incomplete examples. **Do not treat the index as a validated enumeration.** Open the linked sheet for the full field rows and verify the target index mapping and observed values. Request/response distinctions and descriptions may appear elsewhere in that sheet.

Use source sheet + row for traceability; normalize dotted field keys to underscores only for Perf Log V2. The exact value/capitalization of each process remains important. Pages marked deprecated or “will removed” are historical, not current guidance.

## [Common](workbook-common.md)

| Row | Scenario/context | Comment | Value / enumeration | Example (Flight only) |
| ---: | --- | --- | --- | --- |
| 26 | Check Queue size | CheckQueueSize | CheckQueueSize |  |
| 39 | Check Size | CheckSize |  |  |

## [Common Service](workbook-common-service.md)

| Row | Scenario/context | Comment | Value / enumeration | Example (Flight only) |
| ---: | --- | --- | --- | --- |
| 4 | CCS | derby process type | MUST BE:GetTopic<br>CreateTopic<br>DeleteTopic<br>Query<br>Get<br>Delete<br>Disable<br>Enable<br>AddOrUpdate<br>BatchAppend<br>GetAll<br>Cds<br>Export<br>ExportSubMapping |  |
| 8 | Shuttle | 表示当前请求的Shuttle接口 | Must be one of following:<br>CreateQueue, UpdateQueue, GetQueue, DeleteQueue<br>ARITaskReFetch<br>GetPlan, CreatePlan, UpdatePlan, DeletePlan, ActivatePlan, DeactivatePlan<br>GetSchedule, SaveSchedule, DeleteSchedule, SaveHotelSchedule, ManualTriggerSchedule, ActivateFetchSchedule,DeactivateFetchSchedule,<br>FetchScheduler //Shuttle Internal process, execute every 30 seconds<br>RetryScheduler//Shuttle Internal process, execute every 5 minutes<br>CronTriggerSchedule //Shuttle Internal process, Schedule Triggered via cron expression<br>ScheduleExecuted //Shuttle Internal process, process to generate task and send to queue |  |
| 22 | DRS Publisher |  | MUST BE:<br>ReservationPublish |  |
| 34 | DRS Portal |  | MUST BE:<br>ReservationsQuery,SaveEvent |  |
| 50 | SSO |  | MUST BE:<br>Login,Register, SendMail |  |
| 61 | finance-settlement | SyncInvoiceCDS:同步InvoiceData<br>RenderInvoice:渲染发票 | Must be one of following:<br>SyncInvoiceCDS<br>RenderInvoice |  |
| 71 | finsettlement-invoicegenerator | derby process type | Must be one of following:<br>GenerateInvocie |  |
| 84 | finsettlement-storage | derby process type | Must be one of following:<br>SaveSourceData，SaveS3DailyData, SaveS3PeriodicData |  |
| 97 | finsettlement-sourcedata-writer | SyncSourceDataCDS: CDS同步，调用数据源如DSwtichReservation cds 接口 <br>SyncSourceDataDaily: 每天的全量同步补偿<br>WriteSourceData:调用finsettlement-storage接口存储source data | Must be one of following:<br>SyncSourceDataCDS，<br>SyncSourceDataDaily,<br>WriteSourceData |  |
| 111 | Credential-Manager |  | MUST BE:<br>GetServiceCredential，app获取指定serviceId下，某一条credentialId对应的的凭证<br>ListServiceCredential，app获取指定service下可使用的一批凭证<br>RegisterUsedNode，app上报凭证的使用节点信息<br>CreateJwtAccessToken，EC2的场景下，提供给第三方app调用，以创建一个供app使用的API鉴权token<br>RotateJwtAccessToken，EC2的场景下，app内集成的client需要定时更新token |  |
| 122 | Customer Management - Event |  | Must be:<br>HandleEvent |  |
| 134 | Customer Management - Maintain Resource |  | MUST BE: <br>MaintainCustomerDBResources |  |
| 149 | Synchronizer | derby process type | MUST BE:PopKey,GetChanges,ReportSuccess,ReportFail,GetKey |  |
| 164 | CDS | derby process type | MUST BE:HotelChange,LOSRateChange,DailyRateChange,InventoryChange,AvailStatusChange,LOSARIChange，HotelChangeDates,DailyARIChange |  |
| 181 | API Layer/API Call | derby process type | MUST BE: APICall |  |
| 194 | Schdule Center | derby process type | MUST BE: CreateTasks, PopTasks, UpdateTaskStatus |  |
| 202 | Service Health Check | process | MUST BE: ServiceAvailCheck |  |
| 215 | DDFS | process type | MUST BE: Retrieve, Publish, UploadFile<br>Retrieve: retrieve file according to retrieve topic config<br>Publish: publish file according to publish topic config<br>UploadFile: upload file to publish topic |  |
| 224 | DRS | match with the RPC APIs of DRS | MUST BE: Identify, Create, CreateChildren, Confirm, Fail, Cancel, Update, FailResAction, PendingResAction, SuccessResAction, GetDetail, QueryDetail |  |
| 254 | HBC | derby process type | HBCAPICall, HBCApplyTopicRuleTask，HBCTopicMetricCalculateTask，HBCClientInstanceHealthCheckTask，HBCTopicSyncS3Task |  |
| 264 | Paladin | derby process type | MUST BE: GetProperty, SaveProperty, OverrideProperty, DeleteProperty, GetRoomType, SaveRoomTypes, OverrideRoomType, DeleteRoomType, GetRatePlan, SaveRatePlans, OverrideRatePlan, DeleteRatePlan, GetProduct, SaveProducts, OverrideProduct, DeleteProduct, GetPropertyChanges, GetPropertyChangeData |  |
| 274 | Roma | derby process type | Romanize |  |
| 286 | Secure Store | derby process type | MUST BE:SaveSensitiveData,GetSensitiveData |  |

## [Hotel Connectivity](workbook-hotel-connectivity.md)

| Row | Scenario/context | Comment | Value / enumeration | Example (Flight only) |
| ---: | --- | --- | --- | --- |
| 4 | GetAvailability/SaveAvailability | derby process type | MUST BE:GetAvailability, SaveAvailability |  |
| 32 | Live Check | derby process type | MUST BE:LiveCheck |  |
| 67 | Single Push To Channel or Push From Supplier | ARIRequest | ARIRequest |  |
| 90 | Push To Channel or Push From Supplier Ack | ARIAck | ARIAck |  |
| 102 | Batch Push to Channel | BatchARIRequest | BatchARIRequest |  |
| 122 | CDS | SingleCDSFetch | SingleCDSFetch |  |
| 144 | Supplier Request | derby process type | MUST BE:SupplierRequest |  |
| 164 | Single ARI Process | SingleARIProcess | SingleARIProcess |  |
| 181 | Batch ARI Process | BatchARIProcess | BatchARIProcess |  |
| 198 | Trigger ARI Refresh Process | TriggerARIRefresh | Must BE:TriggerARIRefresh |  |
| 211 | Process Policy | PolicyProcess | PolicyProcess |  |
| 228 | Distributor ARI Push Process | SyncerARIProcess | SyncerARIProcess |  |
| 251 | Reservation Task Queue | derby process type | SaveTask, PopSerialId, ConsumeTask, ReportResult |  |
| 260 | SearchHotels | process type | Must be: SearchHotels |  |
| 273 | ARI Tracing | process type | Must be: ARIOperation |  |
| 290 | LivecheckDiff | derby process type | MUST BE:LivecheckDiff |  |
| 317 | MT | derby process type | SaveAuditLog |  |
| 345 | Online | derby process type | MUST BE:DistributorOnlineHotels, SupplierOnlineHotels |  |
| 357 | Plugin | derby process type | MUST BE:GetChange, GetAvailabilityChange,GetDailyChange |  |
| 370 | SyncData | derby process type | MUST BE:SyncProfile, SyncCCS, SyncCurrency |  |
| 383 | Get Products | GetProducts | GetProduct |  |
| 394 | PropertyManagement | process type | PropertyManagement |  |
| 411 | Distributor ARI Push Process | SyncerARIProcess | SyncerARIProcess |  |
| 436 | Get Product Process | GetProduct | GetProduct |  |
| 447 | Get Policy Process | GetPolicy | GetPolicy |  |
| 463 | DProduct Storage | derby process type | GetHotelContent, SaveHotelContent, UpdateHotelStatus, GetRoomTypeContent, SaveRoomTypeContent, UpdateRoomTypeStatus, GetRatePlanContent, SaveRatePlanContent, UpdateRatePlanStatus, GetProductContent, SaveProductContent, UpdateProductStatus,<br>GetHotelContentChange, GetHotelContentChangeData |  |
| 483 | Reservation | derby process type | MUST BE:Book, Modify, Cancel, Hold, Commit, ModifyHold, ModifyCommit, Ignore, BookNotify,ModifyNotify,CancelNotify, Preview,QueryRes,PostCheck, Rollback |  |
| 541 | Res Retrieve | derby process type | MUST BE:Book, Modify, Cancel, Hold, Commit, ModifyHold, ModifyCommit, Ignore, BookNotify,ModifyNotify,CancelNotify, Preview,QueryRes,PostCheck, Rollback |  |
| 570 | Res Ack/Report | derby process type | MUST BE:BookReport, ModifyReport, CancelReport, HoldReport, CommitReport, ModifyHoldReport, ModifyCommitReport, IgnoreReport, RollbackReport |  |
| 596 | Reservation Credit Card Payment | derby process type | ResPayment |  |
| 620 | PushResStay | derby process type | MUST BE:PushResStay |  |
| 644 | Reservation Disburse | Reservation Disburse | ReservationDisburse |  |
| 656 | Expedia Content | derby process type | MUST BE:AddHotel ModifyHotel DeleteHotel AddRoom ModifyRoom DeleteRoom AddRatePlan ModifyRatePlan DeleteRatePlan |  |

## [Hotel BTS Connectivity](workbook-hotel-bts-connectivity.md)

| Row | Scenario/context | Comment | Value / enumeration | Example (Flight only) |
| ---: | --- | --- | --- | --- |
| 5 | GetMasterHotelAvailability | derby process type | MUST BE: GetMasterHotelAvailability |  |
| 30 | LeadRateDiff | derby process type | MUST BE: LeadRateDiff |  |

## [Hotel Marketing Service](workbook-hotel-marketing-service.md)

| Row | Scenario/context | Comment | Value / enumeration | Example (Flight only) |
| ---: | --- | --- | --- | --- |
| 4 | Bidding |  | Bidding |  |
| 19 | Check Bidding Process |  | Bidding |  |
| 28 | Click | derby process type | MUST BE: Click |  |
| 74 | TrackingBooking | derby process type | MUST BE: TrackingBooking |  |
| 112 | Google Private Rate | derby process type | MUST BE: GooglePrivateRate |  |
| 123 | Price Accuracy Report | derby process type | MUST BE: AccuracyReport |  |
| 136 | Facebook Push | derby process type | PushRoomType, PushPrice, CheckRoomType, CheckPrice |  |
| 145 | Facebook Sync Hotel | derby process type | SyncHotel |  |
| 152 | SearchFeed Channel Log | derby process type | GetAvailability on channel end.<br>ARIFetch on supplier end. |  |

## [Hotel Content Service](workbook-hotel-content-service.md)

| Row | Scenario/context | Comment | Value / enumeration | Example (Flight only) |
| ---: | --- | --- | --- | --- |
| 10 | Piculus | CollectEvent, DigestEvent,<br>ValidateEvent, RegisterEvent, <br>UpdateEvent | string |  |
| 22 | GHR | ContentCollectionRequest | string |  |
| 36 | GHR | ContextHotelRequest | string |  |
| 50 | GHR | ContentContextRequest | string |  |
| 65 | GHR | ContentSourceRequest | string |  |
| 80 | HDG | ContentHotelSyncRequest | string |  |
| 91 | Supplier Content Collection | CollectProperties, CollectProperty, RegisterProperty,UpdateProperty,GetProperties,GetProperty | string |  |
| 103 | Supplier Content Change | CollectPropertyChange | string |  |
| 117 | Supplier Content Standardization | StandardizeProperty | string |  |
| 130 | Distributor Content Shop | GetProperties,GetProperty | string |  |
| 144 | Distributor Content CDS | GetPropertyChange | string |  |
| 161 | Object Management | UpdateObject, CheckObject, ListObjects, GetObject,DeleteObject,CopyObject | string |  |

## [Flight Connectivity](workbook-flight-connectivity.md)

| Row | Scenario/context | Comment | Value / enumeration | Example (Flight only) |
| ---: | --- | --- | --- | --- |
| 5 | AirShopping | AirShopping/OrderReShop | String | AirShopping |
| 37 | OfferPrice |  | String | OfferPrice |
| 91 | ServiceList |  | String | ServiceList |
| 116 | SeatAvailability |  | String | SeatAvailability |
| 135 | Order |  | String | OrderCreate |
| 158 | queryAirShoppingCache | CacheAirShopping | String | CacheAirShopping |

## [AI Voice](workbook-ai-voice.md)

| Row | Scenario/context | Comment | Value / enumeration | Example (Flight only) |
| ---: | --- | --- | --- | --- |
| 2 | AI Voice Backend | process  | MUST BE: <br>CreateCallRequest, CancelCallRequest,<br>GetCallRequestResult, ExecuteCallAttempt<br>GenerateCallAttempt,ReceiveCallAttemptOutcome |  |

## [Payment](workbook-payment.md)

| Row | Scenario/context | Comment | Value / enumeration | Example (Flight only) |
| ---: | --- | --- | --- | --- |
| 5 | Payment | derby process type | MUST BE:Pay/Refund/PayQuery/RefundQuery/PayNotify/RefundNotify/SyncNotify/AsyncNotify |  |

## [Property Connector](workbook-property-connector.md)

| Row | Scenario/context | Comment | Value / enumeration | Example (Flight only) |
| ---: | --- | --- | --- | --- |
| 3 | ReceiveMessage | It is used to record the basic information of messages received from PMS and set hotel level alarms | MUST BE:ReceiveMessage |  |
| 13 | ConvertARITask | It is used to record ARI conversion and set hotel level alarms | MUST BE:ConvertPushCache,ConvertFetchCache |  |
| 28 | ProduceMessage/ConsumeMessage | It is used to record the basic information of kafka messages to send | MUST BE:ProduceMessage,ConsumeMessage |  |
| 46 | GetHotelInfo/ChangeHotelInfo | It is used to record the basic information from pc-console | MUST BE:GetHotelInfo、ChangeHotelInfo |  |
| 62 | OperaCloudWhiteLabel | Used to record OperaCloud-pushed Onboard Notifications | MUST BE:<br>OperaNotifications,OperaHandleEvent,<br>OperaBatchTaskExec,OperaTaskExec |  |
| 89 | CheckRateDependency | Used to record derived Rate check result | MUST BE:<br>CheckRateDependency |  |

## [AMEX Project](workbook-amex-project.md)

| Row | Scenario/context | Comment | Value / enumeration | Example (Flight only) |
| ---: | --- | --- | --- | --- |
| 3 | SearchHotels | search the primary hotel list based on the specified criteria | MUST BE:SearchHotels |  |
| 34 | SingleHotelQuery | gets the product list of all associated supplier hotels for the specified master hotel, based on the criteria | MUST BE:SingleHotelQuery |  |
| 59 | HotelsPrompt | search hotels on index information according to the keyword conditions quickly; | MUST BE:HotelsPrompt |  |
| 81 | FetchARI | batch get ari from supplier | MUST BE:FetchARI |  |
| 102 | SaveRawStorage | save data to RawStorage | MUST BE:SaveRawStorage |  |
| 120 | FetchHotelContent | get hotel content from supplier | MUST BE:FetchHotelContent |  |
| 134 | CreateTasks | create task | MUST BE:CreateTasks |  |
| 154 | CloseHotelContent | receive hotel offline tasks | MUST BE:CloseHotelContent |  |
| 167 | ConsumeHotelContent | get hotel info from rawstorage | MUST BE:ConsumeHotelContent |  |
| 181 | CloseHotelContentProcess | process close hotel task | MUST BE:CloseHotelContentProcess |  |
| 194 | ConsumeARI | get ari from rawstorage | MUST BE:ConsumeARI |  |
| 207 | GetChanges | get hotel list of ari changes | MUST BE:GetChanges |  |
| 228 | GetHotels | get Hotel from supplier website,sync to storage medium | MUST BE:GetHotels |  |
| 238 | SingleHotelContentProcess | process hotel task | MUST BE:SingleHotelContentProcess |  |
| 253 | SingleARIProcess | process ari task | MUST BE:SingleARIProcess |  |
| 266 | CloseAriProcess | process close ari task | MUST BE:CloseAriProcess |  |
| 284 | PublishEvent | publish event | MUST BE:PublishEvent |  |
| 297 | ConsumeEvent | consume event | MUST BE:ConsumeEvent |  |
| 310 | GetAvailability | derby process type | MUST BE:GetAvailability |  |
| 333 | Book/Modify/Cancel/QueryRes | derby process type | MUST BE:Book/Modify/Cancel/QueryRes |  |
| 361 | SaveHotelContent | save hotel content | MUST BE:SaveHotelContent |  |
| 379 | SaveRoomTypeContent | save hotel roomType | MUST BE:SaveRoomTypeContent |  |
| 390 | UpdateHotelStatus | update hotel status | MUST BE:UpdateHotelStatus |  |
| 399 | GetHotelContent | get hotel content | MUST BE:GetHotelContent |  |
| 414 | SaveDistributorHotel | save distributor hotel | MUST BE:SaveDistributorHotel |  |
| 425 | SaveARI | save hotel ari | MUST BE:SaveARI |  |
| 443 | CloseARI | deactivate hotel ari | MUST BE:CloseARI |  |
| 464 | GetARISummary | get hotel ari summary  | MUST BE:GetARISummary |  |

## [GPS](workbook-gps.md)

| Row | Scenario/context | Comment | Value / enumeration | Example (Flight only) |
| ---: | --- | --- | --- | --- |
| 4 | Content | ContentRetrieve, ContentReceive | ContentRetrieve, ContentReceive |  |
| 10 | Action | SendEmail,MakeFile | SendEmail,MakeFile |  |
| 15 | Member | EnrollMember,QueryMember,UpdateMember,QueryAllCoupon,QueryAvailCoupon | EnrollMember,QueryMember,UpdateMember,QueryAllCoupon,QueryAvailCoupon |  |
| 22 | Reservation notify | PayNotify | PayNotify |  |

## [Rover](workbook-rover.md)

| Row | Scenario/context | Comment | Value / enumeration | Example (Flight only) |
| ---: | --- | --- | --- | --- |
| 13 | Hotel | HotelInfo | string |  |
| 19 | Authentication | GetAccessToken |  |  |
| 22 | Marketing | ListAdvertises/GetCampaign |  |  |
| 25 | Login/User | process type | WechatLogin, UserBind |  |

## [Disney](workbook-disney.md)

| Row | Scenario/context | Comment | Value / enumeration | Example (Flight only) |
| ---: | --- | --- | --- | --- |
| 2 | Disney TTC Rservation | derby process type | MUST BE: TicketBook, TicketModify, TicketCancel,TicketQueryRes |  |
| 31 | Disney TTC GetAvailability/LiveCheck | derby process type | MUST BE: <br>TicketGetAvailability<br>TicketLiveCheck |  |
| 56 | Disney TTC Get Product  List | derby process type | MUST BE: TicketGetProductList |  |
| 72 | Disney TTC Get Product | derby process type | MUST BE: TicketGetProduct |  |
| 92 | Disney TTC Token | derby process type | MUST BE: GetAuthToken |  |
| 100 | Disney TTC SupplierRequest | derby process type | MUST BE: TicketSupplierRequest |  |
| 122 | TTC CDS | derby process type | MUST BE: TicketSingleCDSFetch |  |

## [US Engineering - will removed](workbook-us-engineering-will-removed.md)

| Row | Scenario/context | Comment | Value / enumeration | Example (Flight only) |
| ---: | --- | --- | --- | --- |
| 50 | Portal | name of the process | string |  |

## [Deprecated -Drizzt Team](workbook-deprecated-drizzt-team.md)

| Row | Scenario/context | Comment | Value / enumeration | Example (Flight only) |
| ---: | --- | --- | --- | --- |
| 4 | Retrieve | LOSRetrieve, DailyRetrieve, LOSChangeRetrieve, DailyChangeRetrieve | LOSRetrieve, DailyRetrieve, LOSChangeRetrieve, DailyChangeRetrieve |  |
| 23 | Event | AccessEvent | AccessEvent |  |
| 33 | ARI Consume | ARIConsume | ARIConsume |  |
