# API

## GET /stock/{sku}

Returns `{"sku": "...", "available": N}`.

## POST /reserve

Body: `{"sku": "...", "qty": N}`. Reserves `qty` units. Fails with 409 when
`qty` exceeds the available stock, and 400 when `qty` is not positive.
