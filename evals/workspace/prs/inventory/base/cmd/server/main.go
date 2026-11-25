package main

import (
	"log"
	"net/http"

	"example.com/inventory/internal/api"
	"example.com/inventory/internal/inventory"
)

func main() {
	store := inventory.NewStore(map[string]int{"widget": 100, "gadget": 25})
	h := &api.Handler{Store: store}
	log.Fatal(http.ListenAndServe(":8080", h.Routes()))
}
