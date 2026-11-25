package api

import (
	"errors"
	"net/http"

	"example.com/inventory/internal/inventory"
)

// writeError maps store errors to HTTP statuses and logs anything unexpected.
func (h *Handler) writeError(w http.ResponseWriter, r *http.Request, err error) {
	switch {
	case errors.Is(err, inventory.ErrUnknownSKU):
		http.Error(w, err.Error(), http.StatusNotFound)
	case errors.Is(err, inventory.ErrInvalidQty):
		http.Error(w, err.Error(), http.StatusBadRequest)
	case errors.Is(err, inventory.ErrInsufficient):
		http.Error(w, err.Error(), http.StatusConflict)
	default:
		h.Log.ErrorContext(r.Context(), "request failed", "path", r.URL.Path, "err", err)
		http.Error(w, "internal error", http.StatusInternalServerError)
	}
}
