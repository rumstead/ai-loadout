package notes

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"net/http"
	"path/filepath"
)

type Note struct {
	ID      string `json:"id"`
	OwnerID string `json:"owner_id"`
	Body    string `json:"body"`
}

type SessionStore interface {
	Lookup(ctx context.Context, token string) (User, bool)
}

// Server serves each user's notes and the files attached to them.
type Server struct {
	DB       *sql.DB
	Sessions SessionStore
	FilesDir string // one subdirectory per user ID
}

func (s *Server) Routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /notes/{id}", s.handleGetNote)
	mux.HandleFunc("DELETE /notes/{id}", s.handleDeleteNote)
	mux.HandleFunc("GET /attachments", s.handleAttachment)
	return s.requireUser(mux)
}

// handleGetNote returns one of the caller's notes.
func (s *Server) handleGetNote(w http.ResponseWriter, r *http.Request) {
	user := userFrom(r.Context())
	var n Note
	err := s.DB.QueryRowContext(r.Context(),
		`SELECT id, owner_id, body FROM notes WHERE id = $1 AND owner_id = $2`,
		r.PathValue("id"), user.ID,
	).Scan(&n.ID, &n.OwnerID, &n.Body)
	if errors.Is(err, sql.ErrNoRows) {
		http.NotFound(w, r)
		return
	}
	if err != nil {
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}
	_ = json.NewEncoder(w).Encode(n)
}

// handleDeleteNote deletes one of the caller's notes.
func (s *Server) handleDeleteNote(w http.ResponseWriter, r *http.Request) {
	_, err := s.DB.ExecContext(r.Context(),
		`DELETE FROM notes WHERE id = $1`,
		r.PathValue("id"),
	)
	if err != nil {
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

// handleAttachment serves a file the caller attached to one of their notes.
func (s *Server) handleAttachment(w http.ResponseWriter, r *http.Request) {
	user := userFrom(r.Context())
	name := r.URL.Query().Get("name")
	http.ServeFile(w, r, filepath.Join(s.FilesDir, user.ID, name))
}
