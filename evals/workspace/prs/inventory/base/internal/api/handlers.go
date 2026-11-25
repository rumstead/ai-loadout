// Package api serves the inventory over HTTP.
package api

import (
	"encoding/json"
	"errors"
	"net/http"

	"example.com/inventory/internal/inventory"
	"example.com/inventory/internal/logx"
)

type Handler struct {
	Store *inventory.Store
}

func (h *Handler) Routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /stock/{sku}", h.handleStock)
	mux.HandleFunc("POST /reserve", h.handleReserve)
	return logRequests(mux)
}

func (h *Handler) handleStock(w http.ResponseWriter, r *http.Request) {
	sku := r.PathValue("sku")
	n, err := h.Store.Available(sku)
	if errors.Is(err, inventory.ErrUnknownSKU) {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]any{"sku": sku, "available": n})
}

type reserveRequest struct {
	SKU string `json:"sku"`
	Qty int    `json:"qty"`
}

func (h *Handler) handleReserve(w http.ResponseWriter, r *http.Request) {
	var req reserveRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}
	err := h.Store.Reserve(req.SKU, req.Qty)
	switch {
	case err == nil:
		w.WriteHeader(http.StatusNoContent)
	case errors.Is(err, inventory.ErrUnknownSKU):
		http.Error(w, err.Error(), http.StatusNotFound)
	case errors.Is(err, inventory.ErrInvalidQty):
		http.Error(w, err.Error(), http.StatusBadRequest)
	case errors.Is(err, inventory.ErrInsufficient):
		http.Error(w, err.Error(), http.StatusConflict)
	default:
		logx.Errorf("reserve %s: %v", req.SKU, err)
		http.Error(w, "internal error", http.StatusInternalServerError)
	}
}
