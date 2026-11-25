package inventory

import (
	"errors"
	"testing"
)

func TestReserve(t *testing.T) {
	s := NewStore(map[string]int{"widget": 10})
	if err := s.Reserve("widget", 4); err != nil {
		t.Fatalf("Reserve(4) = %v", err)
	}
	if err := s.Reserve("widget", 6); err != nil {
		t.Fatalf("Reserve(6) of the last 6 = %v", err)
	}
	if err := s.Reserve("widget", 1); !errors.Is(err, ErrInsufficient) {
		t.Fatalf("Reserve(1) with none left = %v, want ErrInsufficient", err)
	}
}
