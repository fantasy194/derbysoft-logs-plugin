# Payment

Verbatim cell values from `Perf Log Process & Fields Standardization (1).xlsx`. The row number and column letters point to the original workbook; blank cells are left blank. Formulas are retained as formulas. The workbook contains draft, conflicting and deprecated entries; do not assume every row is deployed.

| Row | A | B | C | D | E |
| ---: | --- | --- | --- | --- | --- |
| 3 | Payment |  |  |  |  |
| 4 |  | process_duration | total process time, unit is ms | number 1-99999999999 | Required |
| 5 |  | process | derby process type | MUST BE:Pay/Refund/PayQuery/RefundQuery/PayNotify/RefundNotify/SyncNotify/AsyncNotify | Required |
| 6 |  | process_result | process result | Success, Fail | Required |
| 7 |  | provider_code |  | string,upper case | Required |
| 8 |  | currency_code |  |  | Required |
| 9 |  | payment_status |  | MUST BE:PayWaiting,PaySuccess,PayFailed,RefundWaiting,RefundSuccess,RefundFailed | Required |
| 10 |  | total_amount |  | number | Required when process is Pay |
| 11 |  | refund_amount |  | number | Required when process is Refund |
| 12 |  | user_id |  |  | Required |
| 13 |  | merchant_pay_no |  | payment provider pay no | Required |
| 14 |  | merchant_refund_no |  | payment provider refund no | Required when process is Refund |
| 15 |  | pay_no |  |  | Required |
| 16 |  | refund_no |  |  |  |
| 18 |  | err_code | special error code for payment | Unauthorized, PaymentNotFound, OperationFailed, PayFailed, RefundFailed, SignVerifyFailed, ProviderUnsupported, CurrencyCodeUnsupported, MerchantAlreadyExist，ProviderFailed |  |
