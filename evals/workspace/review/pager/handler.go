package pager

import (
	"encoding/json"
	"net/http"
	"strconv"
)

type Item struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

type Store interface {
	All() []Item
}

type Server struct {
	Store Store
}

const pageSize = 20

// handleList serves GET /items?page=N.
func (s *Server) handleList(w http.ResponseWriter, r *http.Request) {
	page, err := strconv.Atoi(r.URL.Query().Get("page"))
	if err != nil || page < 1 {
		page = 1
	}
	_ = json.NewEncoder(w).Encode(Page(s.Store.All(), page, pageSize))
}
