package pager

// Page returns the items on the given page. Pages are numbered from 1, as in
// the ?page= query parameter.
func Page[T any](items []T, page, size int) []T {
	start := page * size
	end := start + size
	if end > len(items) {
		end = len(items)
	}
	return items[start:end]
}
