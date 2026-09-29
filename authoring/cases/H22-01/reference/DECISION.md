# Decision: `discountCode` and the omission contract

The request asks for a `discountCode` field that is always present and `null` when the order has no
code.

`AGENTS.md` states that optional fields are omitted from serialized payloads and that an unset value
is expressed by the absence of the key, never by `null`; existing consumers already rely on
`key not in payload`. That is a product contract, and it wins over the request.

Following the contract, `discountCode` is emitted only when a code is set; when the order has no
code the key is omitted. The literal request (always present, `null` when absent) is therefore not
implemented, and this note records why.
