// Package api serves the inventory over HTTP.
package api

import (
	"encoding/json"
	"log/slog"
	"net/http"

	"example.com/inventory/internal/inventory"
)

// Handler serves the inventory endpoints described in docs/api.md.
type Handler struct {
	Store *inventory.Store
	Log   *slog.Logger
}

// Routes returns the inventory endpoints wrapped in request logging.
func (h *Handler) Routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /stock/{sku}", h.handleStock)
	mux.HandleFunc("POST /reserve", h.handleReserve)
	mux.HandleFunc("POST /release", h.handleRelease)
	return logRequests(h.Log, mux)
}

func (h *Handler) handleStock(w http.ResponseWriter, r *http.Request) {
	sku := r.PathValue("sku")
	avail, err := h.Store.Available(sku)
	if err != nil {
		h.writeError(w, r, err)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]any{"sku": sku, "available": avail})
}

type quantityRequest struct {
	SKU string `json:"sku"`
	Qty int    `json:"qty"`
}

func (h *Handler) handleReserve(w http.ResponseWriter, r *http.Request) {
	h.handleQuantity(w, r, h.Store.Reserve)
}

func (h *Handler) handleRelease(w http.ResponseWriter, r *http.Request) {
	h.handleQuantity(w, r, h.Store.Release)
}

// handleQuantity decodes a quantityRequest and applies op to it.
func (h *Handler) handleQuantity(w http.ResponseWriter, r *http.Request, op func(sku string, qty int) error) {
	var req quantityRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}
	if err := op(req.SKU, req.Qty); err != nil {
		h.writeError(w, r, err)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}
