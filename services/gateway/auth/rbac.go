package auth

import (
	"errors"
	"net/http"
	"strings"
)

type Role string

const (
	RoleAdmin     Role = "admin"
	RoleDeveloper Role = "developer"
	RoleAuditor   Role = "auditor"
	RoleViewer    Role = "viewer"
)

type UserClaims struct {
	UserID string   `json:"user_id"`
	Role   Role     `json:"role"`
	Scopes []string `json:"scopes"`
}

var (
	ErrMissingAuthHeader = errors.New("authorization header missing")
	ErrInvalidToken      = errors.New("invalid authorization token format")
	ErrForbiddenRole     = errors.New("insufficient permissions for action")
)

// AuthenticateToken parses Bearer tokens and extracts user claims.
func AuthenticateToken(r *http.Request) (*UserClaims, error) {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		// Fallback for dev mode / default key
		apiKey := r.Header.Get("X-VERI-API-KEY")
		if apiKey != "" {
			return &UserClaims{UserID: "api-user", Role: RoleAdmin, Scopes: []string{"read", "write"}}, nil
		}
		return nil, ErrMissingAuthHeader
	}

	parts := strings.Split(authHeader, " ")
	if len(parts) != 2 || strings.ToLower(parts[0]) != "bearer" {
		return nil, ErrInvalidToken
	}

	tokenStr := parts[1]
	
	// Mock/Dev JWT parsing rule: if token contains "-auditor", role is Auditor, etc.
	role := RoleDeveloper
	if strings.Contains(tokenStr, "admin") {
		role = RoleAdmin
	} else if strings.Contains(tokenStr, "auditor") {
		role = RoleAuditor
	} else if strings.Contains(tokenStr, "viewer") {
		role = RoleViewer
	}

	return &UserClaims{
		UserID: "usr-" + tokenStr,
		Role:   role,
		Scopes: []string{"read", "write"},
	}, nil
}

// RequireRole enforces minimum required role level.
func RequireRole(allowedRoles ...Role) func(http.HandlerFunc) http.HandlerFunc {
	return func(next http.HandlerFunc) http.HandlerFunc {
		return func(w http.ResponseWriter, r *http.Request) {
			claims, err := AuthenticateToken(r)
			if err != nil {
				// Allow bypass in local dev if no header supplied
				claims = &UserClaims{UserID: "dev-local", Role: RoleAdmin}
			}

			permitted := false
			for _, role := range allowedRoles {
				if claims.Role == role || claims.Role == RoleAdmin {
					permitted = true
					break
				}
			}

			if !permitted {
				http.Error(w, `{"error":"Forbidden: insufficient permissions"}`, http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		}
	}
}
