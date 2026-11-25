# API

## GET /stock/{sku}

Returns `{"sku": "...", "available": N}`, or 404 for an unknown SKU.

## POST /reserve

Body: `{"sku": "...", "qty": N}`. Reserves `qty` units. Fails with 409 when
`qty` exceeds the available stock, and 400 when `qty` is not positive.

## POST /release

Body: `{"sku": "...", "qty": N}`. Returns `qty` reserved units to the
available stock, for example when an order is cancelled. Fails with 400 when
`qty` is not positive.
