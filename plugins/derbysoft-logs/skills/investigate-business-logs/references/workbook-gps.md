# GPS

Verbatim cell values from `Perf Log Process & Fields Standardization (1).xlsx`. The row number and column letters point to the original workbook; blank cells are left blank. Formulas are retained as formulas. The workbook contains draft, conflicting and deprecated entries; do not assume every row is deployed.

| Row | A | B | C | D | E |
| ---: | --- | --- | --- | --- | --- |
| 1 | Request | Key | Comment | Value | Required/Optional |
| 3 | Content |  |  |  |  |
| 4 |  | process | ContentRetrieve, ContentReceive | ContentRetrieve, ContentReceive | Required |
| 5 |  | echo_token | unique id for the request | string | Optional |
| 6 |  | supplier | derby supplier code | string,upper case | Optional |
| 7 |  | channel | derby channel code | string,upper case | Optional |
| 9 | Action |  |  |  |  |
| 10 |  | process | SendEmail,MakeFile | SendEmail,MakeFile | Required |
| 11 |  | supplier | derby supplier code | string,upper case | Required |
| 12 |  | channel | derby channel code | string,upper case | Required |
| 14 | Member |  |  |  |  |
| 15 |  | process | EnrollMember,QueryMember,UpdateMember,QueryAllCoupon,QueryAvailCoupon | EnrollMember,QueryMember,UpdateMember,QueryAllCoupon,QueryAvailCoupon | Required |
| 16 |  | echo_token | unique id for the request | string | Optional |
| 17 |  | supplier | derby supplier code,upper case | string | Optional |
| 18 |  | channel | derby channel code,upper case | string | Optional |
| 19 |  | member_id | member.id | string | Optional |
| 21 | Reservation notify |  |  |  |  |
| 22 |  | process | PayNotify | PayNotify | Required |
| 23 |  | echo_token | unique id for the request | string | Optional |
| 24 |  | supplier | derby supplier code | string,upper case | Optional |
| 25 |  | channel | derby channel code | string,upper case | Optional |
| 26 |  | res_id_derby | derbysoft res no | string | Required |
| 27 |  | res_id_supplier | supplier res no | string | Required on supplier end |
| 28 |  | res_id_channel | channel res no | string | Required on channel end and supplier end |
