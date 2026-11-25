// Package inventory keeps the available stock for each SKU.
package inventory

import (
	"errors"
	"sync"
)

var (
	ErrUnknownSKU   = errors.New("unknown sku")
	ErrInvalidQty   = errors.New("quantity must be positive")
	ErrInsufficient = errors.New("insufficient stock")
)

type Store struct {
	mu    sync.Mutex
	stock map[string]int
}

func NewStore(initial map[string]int) *Store {
	s := &Store{stock: make(map[string]int, len(initial))}
	for k, v := range initial {
		s.stock[k] = v
	}
	return s
}

// Available returns the units of sku that can still be reserved.
func (s *Store) Available(sku string) (int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	n, ok := s.stock[sku]
	if !ok {
		return 0, ErrUnknownSKU
	}
	return n, nil
}

// Reserve takes qty units of sku out of the available stock. It fails with
// ErrInsufficient when qty exceeds what is available.
func (s *Store) Reserve(sku string, qty int) error {
	if qty <= 0 {
		return ErrInvalidQty
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	n, ok := s.stock[sku]
	if !ok {
		return ErrUnknownSKU
	}
	if qty > n {
		return ErrInsufficient
	}
	s.stock[sku] = n - qty
	return nil
}
