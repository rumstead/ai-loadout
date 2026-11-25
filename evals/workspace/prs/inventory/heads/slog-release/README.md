# inventory

Tracks stock per SKU and lets the order service reserve and release it.

    go run ./cmd/server

The server listens on `:$PORT` (default 8080) and logs JSON to stdout. Set
`LOG_LEVEL=debug` for debug logs. See docs/api.md for the endpoints.
