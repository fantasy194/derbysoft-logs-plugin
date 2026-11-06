# StreamLog fields

The following field table and limits are transcribed from `docs/Stream Log Standard(JSON).md` in this project. Optional fields and enum values vary by deployed service; check observed records and mappings. The source has inconsistent transaction-type lists in the main table and limits table; do not assume either is exhaustive.

### Log Fields Standard

| Field Name | Description | Type | Required/Optional |
| :---- | :---- | :---- | :---- |
| stream\_version | Version of stream log format. Now MUST be “2.0” | string | required |
| topic | Technical concept, Message queue topic log write into | string | required |
| ip | Technical concept, ip of the machine from what the log is produced | string | required |
| host | Technical concept, hostname of the machine from what the log is produced | string | required |
| app | Technical concept, name of application that produced the log | string | required |
| app\_version | Technical concept, version of application that produced the log | string | optional |
| sdk\_version | Technical concept, version of Log SDK | string | optional |
| region | Technical concept, AWS region where the application is deployed | string | optional |
| instance\_id | Technical concept, EC2 instance id where the application is deployed | string | optional |
| pod\_namespace | Technical concept, POD namespace the application pod located in kubernetes | string | optional |
| pod\_name | Technical concept, name of the POD in which the application is running in kubernetes | string | optional |
| pod\_ip | Technical concept, ip of the POD in which the application is running in kubernetes | string | optional |
| offset | Technical concept, streamlog byte offset in the log file for fast search | string | optional |
| length | Technical concept, streamlog byte length in the log file for fast search | string | optional |
| timestamp | The format of the timestamp MUST be "2013-10-01T23:34:33.456" and the timezone is UTC. The time should be the moment this action starts | string | required |
| transaction\_type | The unique transaction type of one application stream logs. | enum, options: Reservation LiveCheck ARI HotelContent Legacy Payment (支付相关) Marketing (广告/优惠券/活动) Member (会员/权益) HotelProduct TicketProduct | required |
| trace\_token | Used for trace request/response chain. Those steam logs which belong to a specific transaction should have the same value. No white space character in it. Should be the same as “transaction.id” if exists, otherwise MUST generate one. | string | required |
| stream\_type | Identify request and response. Enum string type, options: “RQ”, “RS”, “RQRS”. “RQ” means request, “RS” means response, “RQRS” means a pair of request and response. | enum, “RQ”, “RS”, “RQRS” | required |
| encoding | Identify what kind of encoding has been done on “message” value. Options: “RAW”, “GZIP+BASE64” “RAW” means do not do any encoding, keep raw value. “GZIP+BASE64” means first doing GZIP compression and then converting to BASE64 encoding, and string to binary encoding is UTF8. Default value is “RAW” | enum, "RAW" or "GZIP+BASE64" | required |
| message | The message that needs to be recorded. Convert to text(XML/JSON/...) if your protocol is a binary protocol. MUST be escaped to json string. Do tail trim if length exceeds limit. | string | required |
| process | Value refer definition from Perf Log Process & Fields Standardization . | string | optional |
| process\_result |  | enum, "Success" or "Fail" | optional |
| transaction\_id | A token string from payload. | string | optional |
| channel | Derby channel code,upper case. | string | optional |
| supplier | Derby supplier code,upper case. | string | optional |
| connection\_type | identify EXCHANGE connection, MUST BE: Standard, Exchange | string | optional |
| hotel | Hotel code | string | optional |
| hotels |  | array\<string\> | optional |
| hotels\_supplier |  | array\<string\> | optional |
| hotels\_channel |  | array\<string\> | optional |
| res\_id\_derby | Derbysoft res no. Strongly recommends logging it when it’s a reservation stream log. | string | optional |
| res\_id\_channel |  | string | optional |
| res\_id\_supplier |  | string | optional |
| res\_id\_exchange |  | string | optional |
| room\_cnt |  | integer | optional |
| check\_in |  | string | optional |
| check\_out |  | string | optional |
| rate\_plan |  | string | optional |
| rate\_plans |  | array\<string\> | optional |
| rate\_plans\_supplier |  | array\<string\> | optional |
| rate\_plans\_channel |  | array\<string\> | optional |
| room\_type |  | string | optional |
| room\_types |  | array\<string\> | optional |
| room\_types\_supplier |  | array\<string\> | optional |
| room\_types\_channel |  | array\<string\> | optional |
| start\_date | Min date in the message. Format is 2015-12-24. | string | optional |
| end\_date | Max date in the message. Format is 2015-12-26 | string | optional |
| stay\_dates | Generally used in ARI push/pull senario that he ARI date range is not consecutive. Split into an array of all dates. If the date range is consecutive, highly recommend using “start\_date”,”end\_date” instead. Example: \[“2023-12-01”, “2023-12-05”, “2023-12-08”, “2023-12-09”\] | array\<string\> | optional |
| ari\_types | ARI types, Examples: ‘Restriction’, ‘LosRate’, ‘DailyRate’, ‘Inventory’ | array\<string\> | optional |
| extra | Extra field reserved for special or uncommon index string. Not recommended, because no one except the log creator knows the meaning of it. | string | optional |
| client |  | string | optional |
| source | request source role, enum: ‘DerbySoft’, ‘Supplier’, ‘Distributor’ | string | optional |
| destination | request destination role, enum: ‘DerbySoft’, ‘Supplier’, ‘Distributor’ | string | optional |
| custom | Identity of a connectivity | string | optional |
| merchant\_no |  | string | optional |
| pay\_no | Payment serial number | string | optional |
| refund\_no |  | string | optional |
| member\_id |  | string | optional |
| campaign\_id |  | string | optional |
| coupon\_no |  | string | optional |
| request\_type | channel/supplier original request type | string | optional |
| los |  | integer | optional |
| availability\_result |  | string | optional |
| receive\_time | "receive\_time": datetime when DStorage received the ARI save request The format MUST be "2013-10-01T23:34:33.456" and the timezone is UTC. | string | optional |
| update\_time | "update\_time": datetime when the processor component finished the whole ARI save process (including DStorage time) The format MUST be "2013-10-01T23:34:33.456" and the timezone is UTC. | string | optional |
| err\_code | derbysoft standard error code | string | optional |
| err\_msg |  | string | optional |
| action\_type | Specific operations performed when interacting with channel product interfaces, like: Create, Update, Activate, Deactivate | string | optional |
| corporate\_supplier | Business travel only, The corporate code in supplier | string | optional |
| corporate\_channel | Business travel only, The corporate code in channel | string | optional |
| account\_code | flight, OTA 供应侧账号 | string | optional |
| airline\_offer\_id | flight, 航司侧的报价id | string | optional |
| api\_call\_duration | flight, 外部接口调用持续时间 | integer | optional |
| api\_call\_time | flight, 外部接口调用时间 | string | optional |
| api\_call\_url | flight, 外部接口调用url | string | optional |
| booking\_codes | flight, 舱位集合 | array\<string\> | optional |
| cache\_offer\_key | flight, offerPrice缓存Key | string | optional |
| cache\_shopping | flight, 是否缓存shopping, true/false | string | optional |
| cache\_shopping\_key | flight, shopping缓存键 | string | optional |
| currency | flight, 币种 | string | optional |
| gdn\_order\_id | flight, gdn订单id | string | optional |
| offer\_from | flight, 报价来源 | string | optional |
| offer\_id | flight, 机票报价id | string | optional |
| onward\_airline\_codes | flight, 去程航司二字码集合 | array\<string\> | optional |
| onward\_destination | flight, 去程目的地 | string | optional |
| onward\_origin | flight, 去程出发地 | string | optional |
| payment\_amount | flight, 支付金额 | string | optional |
| payment\_currency | flight, 支付币种 | string | optional |
| pnrs | flight, PNR集合 | array\<string\> | optional |
| price\_change | flight, 价格变动 | integer | optional |
| refund\_estimation\_id | flight, 退票报价的id | string | optional |
| refund\_type | flight, 退票类型 | string | optional |
| return\_airline\_codes | flight, 回程航司二字码集合 | array\<string\> | optional |
| return\_destination | flight, 回程目的地 | string | optional |
| return\_origin | flight, 回程出发地 | string | optional |
| seller\_code | flight, OTA账号 | string | optional |
| seller\_order\_id | flight, OTA订单号 | string | optional |
| solution\_cnt | flight, solution数量 | integer | optional |
| split\_pricing | flight, 是否拆单报价, true/false | string | optional |
| split\_shopping | flight, 是否拆单报价, true/false | string | optional |
| supplier\_group | flight, 供应组 | string | optional |
| supplier\_order\_id | flight, 供应订单id | string | optional |

### Log Record Limits {#log-record-limits}

To prevent the log system from blocking due to huge logs, all item value length **MUST** be limited.
Default Max Limit Of type:
string:  100
array\<string\>: item:100, max items: 1000

Special fields limit:

| JSON Key | Data Type | Max Limit(char length) |
| :---- | :---- | :---- |
| "ip" | string | 50 |
| "host" | string | 255 |
| "timestamp" | string | 23 |
| "transaction\_type" | enum | "Reservation","LiveCheck","ARI","HotelContent","Legacy" |
| "stream\_type" | enum | "RQ", "RS", "RQRS"  |
| "message" | string | 5000,000 (Do tail trim if length exceed limit) |
| "room\_cnt" | integer | 1-255 |
