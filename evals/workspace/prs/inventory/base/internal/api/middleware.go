package api

import (
	"net/http"

	"example.com/inventory/internal/logx"
)

func logRequests(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		logx.Infof("%s %s", r.Method, r.URL.Path)
		next.ServeHTTP(w, r)
	})
}
