import api from "./axios";

// POST /api/auth/signup  { name, email, password } -> Token { access_token, token_type, user }
export function signup({ name, email, password }) {
  return api.post("/api/auth/signup", { name, email, password }).then((r) => r.data);
}

// POST /api/auth/login  { email, password } -> Token { access_token, token_type, user }
export function login({ email, password }) {
  return api.post("/api/auth/login", { email, password }).then((r) => r.data);
}

// GET /api/auth/me -> UserOut { id, name, email, role }
export function fetchCurrentUser() {
  return api.get("/api/auth/me").then((r) => r.data);
}
