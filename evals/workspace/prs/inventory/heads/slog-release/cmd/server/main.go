package main

import (
	"cmp"
	"log/slog"
	"net/http"
	"os"

	"example.com/inventory/internal/api"
	"example.com/inventory/internal/inventory"
)

func main() {
	level := slog.LevelInfo
	if os.Getenv("LOG_LEVEL") == "debug" {
		level = slog.LevelDebug
	}
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: level}))

	store := inventory.NewStore(map[string]int{"widget": 100, "gadget": 25})
	h := &api.Handler{Store: store, Log: logger}

	addr := ":" + cmp.Or(os.Getenv("PORT"), "8080")
	logger.Info("listening", "addr", addr)
	if err := http.ListenAndServe(addr, h.Routes()); err != nil {
		logger.Error("server stopped", "err", err)
		os.Exit(1)
	}
}
