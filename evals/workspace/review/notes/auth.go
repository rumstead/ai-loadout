package notes

import (
	"context"
	"net/http"
)

type User struct {
	ID string
}

type ctxKey struct{}

// requireUser rejects requests without a valid session and puts the session's
// user in the request context.
func (s *Server) requireUser(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		c, err := r.Cookie("session")
		if err != nil {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		user, ok := s.Sessions.Lookup(r.Context(), c.Value)
		if !ok {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		next.ServeHTTP(w, r.WithContext(context.WithValue(r.Context(), ctxKey{}, user)))
	})
}

func userFrom(ctx context.Context) User {
	return ctx.Value(ctxKey{}).(User)
}
