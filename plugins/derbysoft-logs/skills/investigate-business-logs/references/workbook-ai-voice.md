# AI Voice

Verbatim cell values from `Perf Log Process & Fields Standardization (1).xlsx`. The row number and column letters point to the original workbook; blank cells are left blank. Formulas are retained as formulas. The workbook contains draft, conflicting and deprecated entries; do not assume every row is deployed.

| Row | A | B | C | D | E |
| ---: | --- | --- | --- | --- | --- |
| 1 | AI Voice Backend |  |  |  |  |
| 2 |  | process  | process  | MUST BE: <br>CreateCallRequest, CancelCallRequest,<br>GetCallRequestResult, ExecuteCallAttempt<br>GenerateCallAttempt,ReceiveCallAttemptOutcome | Required |
| 3 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 4 |  | process_result | process result | Success, Fail | Required |
| 5 |  | echo_token | unique id for the request | string | Required |
| 6 |  | call_request_id | The id of the CallRequest Resource | string | Required |
| 7 |  | call_request_status | The status of the CallRequest, only exist when process is <br>GetCallRequestResult | string | Optional |
| 8 |  | customer_id | The id of Customer(From CustomerDB) | string | Required |
| 9 |  | request_source | In which way the request from. | User, ClientAPI | Optional |
| 10 |  | api_client_id | The Client ID used to send requeset to the API, <br>Only exist when request source is ClientAPI | string | Optional |
| 11 |  | user_id | The id of user who send request. <br>Only exist when request source is User | string | Optional |
| 12 |  | call_attempt_id | The id of CallAttempt, only when process is <br>ExecuteCallAttempt/GenerateCallAttempt/ReceiveCallAttemptOutcome. | string | Optional |
| 13 |  | call_attempt_bundle_id | The id of CallAttemptBundle.<br>Multiple CallAttempts can be bound to a single CallAttemptBundle to make a single phone call<br> only when process is <br>ReportBundleRetrieveStatus, RetrieveCallAttemptBundles. | string | Optional |
