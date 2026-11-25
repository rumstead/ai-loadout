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

// Store holds the available units per SKU. It is safe for concurrent use.
type Store struct {
	mu    sync.Mutex
	stock map[string]int
}

// NewStore returns a Store seeded with a copy of initial.
func NewStore(initial map[string]int) *Store {
	s := &Store{stock: make(map[string]int, len(initial))}
	for sku, n := range initial {
		s.stock[sku] = n
	}
	return s
}

// Available returns the units of sku that can still be reserved.
func (s *Store) Available(sku string) (int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	avail, ok := s.stock[sku]
	if !ok {
		return 0, ErrUnknownSKU
	}
	return avail, nil
}

// Reserve takes qty units of sku out of the available stock. It fails with
// ErrInsufficient when qty exceeds what is available.
func (s *Store) Reserve(sku string, qty int) error {
	return s.adjust(sku, qty, func(avail int) (int, error) {
		if avail <= qty {
			return 0, ErrInsufficient
		}
		return avail - qty, nil
	})
}

// Release returns qty previously reserved units of sku to the available stock.
func (s *Store) Release(sku string, qty int) error {
	return s.adjust(sku, qty, func(avail int) (int, error) {
		return avail + qty, nil
	})
}

// adjust checks qty, then replaces the stock of sku with fn's result while
// holding the lock.
func (s *Store) adjust(sku string, qty int, fn func(avail int) (int, error)) error {
	if qty <= 0 {
		return ErrInvalidQty
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	avail, ok := s.stock[sku]
	if !ok {
		return ErrUnknownSKU
	}
	next, err := fn(avail)
	if err != nil {
		return err
	}
	s.stock[sku] = next
	return nil
}
