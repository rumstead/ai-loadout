package inventory

import (
	"errors"
	"testing"
)

func TestReserve(t *testing.T) {
	tests := []struct {
		name    string
		qty     int
		wantErr error
	}{
		{name: "part of the stock", qty: 3},
		{name: "more than available", qty: 11, wantErr: ErrInsufficient},
		{name: "zero", qty: 0, wantErr: ErrInvalidQty},
		{name: "negative", qty: -1, wantErr: ErrInvalidQty},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			s := NewStore(map[string]int{"widget": 10})
			if err := s.Reserve("widget", tt.qty); !errors.Is(err, tt.wantErr) {
				t.Fatalf("Reserve(%d) = %v, want %v", tt.qty, err, tt.wantErr)
			}
		})
	}
}

func TestRelease(t *testing.T) {
	s := NewStore(map[string]int{"widget": 10})
	if err := s.Reserve("widget", 4); err != nil {
		t.Fatal(err)
	}
	if err := s.Release("widget", 4); err != nil {
		t.Fatal(err)
	}
	if got, _ := s.Available("widget"); got != 10 {
		t.Fatalf("Available = %d after reserve and release, want 10", got)
	}
}

func TestUnknownSKU(t *testing.T) {
	s := NewStore(nil)
	if err := s.Reserve("nope", 1); !errors.Is(err, ErrUnknownSKU) {
		t.Fatalf("Reserve = %v, want ErrUnknownSKU", err)
	}
	if _, err := s.Available("nope"); !errors.Is(err, ErrUnknownSKU) {
		t.Fatalf("Available = %v, want ErrUnknownSKU", err)
	}
}
