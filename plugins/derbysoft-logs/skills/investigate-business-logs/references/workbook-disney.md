# Disney

Verbatim cell values from `Perf Log Process & Fields Standardization (1).xlsx`. The row number and column letters point to the original workbook; blank cells are left blank. Formulas are retained as formulas. The workbook contains draft, conflicting and deprecated entries; do not assume every row is deployed.

| Row | A | B | C | D | E |
| ---: | --- | --- | --- | --- | --- |
| 1 | Disney TTC Rservation | Disney ticket reservation |  |  |  |
| 2 |  | process | derby process type | MUST BE: TicketBook, TicketModify, TicketCancel,TicketQueryRes | Required |
| 3 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 4 |  | process_result | process result | Success, Fail | Required |
| 5 |  | echo_token | unique id for the request | string | Required |
| 6 |  | supplier | derby supplier code | string | Required |
| 7 |  | channel | derby channel code | string | Required for distributor request |
| 8 |  | res_id_channel | distributor reservation id | string | Optional |
| 9 |  | res_id_derby | derby reservation id | string | Optional |
| 10 |  | res_id_supplier | supplier reservation id | string | Optional |
| 11 |  | cancel_confirm_id | supplier cancel id | string | Optional |
| 12 |  | channel_supplier | supplier distributor id | string | Optional |
| 13 |  | chain_disney | disney chain id | string | Optional |
| 14 |  | brand_disney | disney brand id, a brand means an attraction | string | Required |
| 15 |  | brand_channel | channel brand id, a brand means an attraction | string | Optional |
| 16 |  | brand_supplier | supplier brand id, a brand means an attraction | string | Optional |
| 17 |  | office_id_supplier | channel reginal office id that DS passes to Disney | string | Optional |
| 18 |  | office_id_channel | channel reginal office id that channel passes to DS | string | Optional |
| 19 |  | affiliation | Disney discount groups | string | Optional |
| 20 |  | Products Info |  |  |  |
| 21 |  | product_code | supplier product code | string | Optional |
| 22 |  | quantity | product quantity | string | Optional |
| 23 |  | admission_date | reservation date | string | Required |
| 24 |  | duration_days | ticket duration days, how many days the ticket can be used | string | Optional |
| 25 |  | usage_buffer_days | besides duration dyas, ticket has the usage buffer days, it means the ticket can be used within the duration.days+usage.buffer.days<br>e.g. a ticket's duration.days=3, usage.buffer.days=2; it meas you can use the ticket 3 days within 5(3+2) days | string | Optional |
| 26 |  | product_age_type | product age type | string Enum MUST BE: Adult, Child | Optional |
| 27 |  | Products Info End |  |  |  |
| 28 |  | start_date | query reservation start date | date | Optional |
| 29 |  | end_date | query reservation end date | date | Optional |
| 30 | Disney TTC GetAvailability/LiveCheck | Disney ticket livecheck |  |  |  |
| 31 |  | process | derby process type | MUST BE: <br>TicketGetAvailability<br>TicketLiveCheck | Required |
| 32 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 33 |  | process_result | process result | Success, Fail | Required |
| 34 |  | echo_token | unique id for the request | string | Required |
| 35 |  | supplier | derby supplier code | string | Required |
| 36 |  | channel | derby channel code | string | Required for distributor request |
| 37 |  | channel_supplier | supplier distributor id | string | Optional |
| 38 |  | chain_disney | disney chain id | string | Optional |
| 39 |  | brand_disney | disney brand id, a brand means an attraction | string | Required |
| 40 |  | brand_channel | channel brand id, a brand means an attraction | string | Optional |
| 41 |  | brand_supplier | supplier brand id, a brand means an attraction | string | Optional |
| 42 |  | office_id_supplier | channel reginal office id that DS passes to Disney | string | Optional |
| 43 |  | office_id_channel | channel reginal office id that channel passes to DS | string | Optional |
| 44 |  | affiliation | Disney discount groups | string | Optional |
| 45 |  | product_code | supplier product code | string | Optional |
| 46 |  | quantity | product quantity | number | Optional |
| 47 |  | admission_date | expected ticket date | string | Optional |
| 48 |  | start_date | expected ticket date range, start date | string | Optional |
| 49 |  | end_date | expected ticket date range, end date | string | Optional |
| 50 |  | duration_days | ticket duration days, how many days the ticket can be used | number | Optional |
| 51 |  | usage_buffer_days | besides duration dyas, ticket has the usage buffer days, it means the ticket can be used within the duration.days+usage.buffer.days<br>e.g. a ticket's duration.days=3, usage.buffer.days=2; it meas you can use the ticket 3 days within 5(3+2) days | number | Optional |
| 52 |  | product_age_type | product age type | MUST BE: Adult, Child | Optional |
| 53 |  | availability_result | availability result | For Example: Avail\|NotAvail | Optional |
| 55 | Disney TTC Get Product  List | Disney TTC Get Product  List |  |  |  |
| 56 |  | process | derby process type | MUST BE: TicketGetProductList | Required |
| 57 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 58 |  | process_result | process result | Success, Fail | Required |
| 59 |  | echo_token | unique id for the request | string | Required |
| 60 |  | supplier | derby supplier code | string | Required |
| 61 |  | channel | derby channel code | string | Required for distributor request |
| 62 |  | channel_supplier | supplier distributor id | string | Optional |
| 63 |  | chain_disney | disney chain id | string | Optional |
| 64 |  | brand_disney | disney brand id, a brand means an attraction | string | Required |
| 65 |  | brand_channel | channel brand id, a brand means an attraction | string | Optional |
| 66 |  | brand_supplier | supplier brand id, a brand means an attraction | string | Optional |
| 67 |  | office_id_supplier | channel reginal office id that DS passes to Disney | string | Optional |
| 68 |  | office_id_channel | channel reginal office id that channel passes to DS | string | Optional |
| 69 |  | product_cnt | disney product count | number | Required |
| 71 | Disney TTC Get Product  | Disney TTC Get Product  List |  |  |  |
| 72 |  | process | derby process type | MUST BE: TicketGetProduct | Required |
| 73 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 74 |  | process_result | process result | Success, Fail | Required |
| 75 |  | echo_token | unique id for the request | string | Required |
| 76 |  | supplier | derby supplier code | string | Required |
| 77 |  | channel | derby channel code | string | Required for distributor request |
| 78 |  | channel_supplier | supplier distributor id | string | Optional |
| 79 |  | chain_disney | disney chain id | string | Optional |
| 80 |  | brand_disney | disney brand id, a brand means an attraction | string | Required |
| 81 |  | brand_channel | channel brand id, a brand means an attraction | string | Optional |
| 82 |  | brand_supplier | supplier brand id, a brand means an attraction | string | Optional |
| 83 |  | office_id_supplier | channel reginal office id that DS passes to Disney | string | Optional |
| 84 |  | office_id_channel | channel reginal office id that channel passes to DS | string | Optional |
| 85 |  | affiliation | Disney discount groups | string | Optional |
| 86 |  | product_code | supplier product code | string | Required |
| 87 |  | duration_days | ticket duration days, how many days the ticket can be used | string | Optional |
| 88 |  | usage_buffer_days | besides duration dyas, ticket has the usage buffer days, it means the ticket can be used within the duration.days+usage.buffer.days<br>e.g. a ticket's duration.days=3, usage.buffer.days=2; it meas you can use the ticket 3 days within 5(3+2) days | string | Optional |
| 91 | Disney TTC Token | Disney ticket Get Auth Token |  |  |  |
| 92 |  | process | derby process type | MUST BE: GetAuthToken | Required |
| 93 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 94 |  | process_result | process result | Success, Fail | Required |
| 95 |  | echo_token | unique id for the request | string | Optional |
| 96 |  | supplier | derby supplier code | string | Required |
| 97 |  | channel | derby channel code | string | Required for distributor request |
| 99 | Disney TTC SupplierRequest | Disney ARI pull |  |  |  |
| 100 |  | process | derby process type | MUST BE: TicketSupplierRequest | Required |
| 101 |  | process_supplier | process supplier | string Distributors,Distributor,Products,Product,ProductRate,LiveCheck,Hotels,Hotel,HotelRoom,RoomPackages,RoomPackage,RoomPackageAvailRequest,RoomPackageAvailConsume,RoomPackageRate | Optional |
| 102 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 103 |  | process_result | process result | Success, Fail | Required |
| 104 |  | echo_token | unique id for the request | string | Optional |
| 105 |  | supplier | derby supplier code | string | Required |
| 106 |  | channel | derby channel code | string | Required for distributor request |
| 107 |  | channel_supplier | supplier distributor id | string | Optional |
| 108 |  | channel_cnt | distributor count | number | Optional |
| 109 |  | contract_start | contract start date, the contract is betwwen the channel and the disney brand | string | Optional |
| 110 |  | contract_end | contract end date, the contract is betwwen the channel and the disney brand | string | Optional |
| 111 |  | chain_disney | disney chain id | string | Optional |
| 112 |  | brand_disney | disney brand id, a brand means an attraction | string | Required |
| 113 |  | brand_channel | channel brand id, a brand means an attraction | string | Optional |
| 114 |  | brand_supplier | supplier brand id, a brand means an attraction | string | Optional |
| 115 |  | office_id_supplier | channel reginal office id that DS passes to Disney | string | Optional |
| 116 |  | office_id_channel | channel reginal office id that channel passes to DS | string | Optional |
| 117 |  | affiliation | Disney discount groups | string | Optional |
| 118 |  | product_code | supplier product code | string | Optional |
| 121 | TTC CDS | Ticket CDS Change |  |  |  |
| 122 |  | process | derby process type | MUST BE: TicketSingleCDSFetch | Required |
| 123 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 124 |  | process_result | process result | Success, Fail | Required |
| 125 |  | echo_token | unique id for the request | string | Optional |
| 126 |  | supplier | derby supplier code | string | Required |
| 127 |  | channel | derby channel code | string | Required for distributor request |
| 128 |  | chain_disney | disney chain id | string | Optional |
| 129 |  | brand_disney | disney brand id, a brand means an attraction | string | Required |
| 130 |  | brand_channel | channel brand id, a brand means an attraction | string | Optional |
| 131 |  | brand_supplier | supplier brand id, a brand means an attraction | string | Optional |
| 132 |  | office_id_supplier | channel reginal office id that DS passes to Disney | string | Optional |
| 133 |  | office_id_channel | channel reginal office id that channel passes to DS | string | Optional |
| 134 |  | start_date | batch start date. Format is 2015-12-24 | string | Optional |
| 135 |  | end_date | batch end date. Format is 2015-12-26 | string | Optional |
| 136 |  | product_codes | supplier product code | string array | Optional |
