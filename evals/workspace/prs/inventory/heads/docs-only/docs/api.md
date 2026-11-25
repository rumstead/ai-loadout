# API

All bodies are JSON. Errors come back as plain text with the status below.

## GET /stock/{sku}

Returns `{"sku": "...", "available": N}`.

    curl localhost:8080/stock/widget

## POST /reserve

Body: `{"sku": "...", "qty": N}`. Reserves `qty` units. Fails with 409 when
`qty` exceeds the available stock, and 400 when `qty` is not positive.

    curl -X POST localhost:8080/reserve -d '{"sku": "widget", "qty": 2}'
