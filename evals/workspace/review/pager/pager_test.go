package pager

import (
	"reflect"
	"testing"
)

func TestPage(t *testing.T) {
	items := []int{1, 2, 3, 4, 5}
	got := Page(items, 0, 2)
	if want := []int{1, 2}; !reflect.DeepEqual(got, want) {
		t.Fatalf("Page = %v, want %v", got, want)
	}
}
