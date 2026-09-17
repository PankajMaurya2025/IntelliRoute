import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach the JWT (if present) to every outgoing request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("intelliroute_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Normalize errors into a consistent { status, message } shape so every
// component can handle them the same way, and force a logout on 401.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status ?? null;
    let message = "Something went wrong. Please try again.";

    if (!error.response) {
      message = "Could not reach the server. Check your connection and that the backend is running.";
    } else if (status === 401) {
      message = "Your session has expired. Please log in again.";
      localStorage.removeItem("intelliroute_token");
      localStorage.removeItem("intelliroute_user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    } else if (status === 403) {
      message = "You don't have permission to do that.";
    } else if (status === 404) {
      message = error.response.data?.detail || "Not found.";
    } else if (status === 422) {
      const detail = error.response.data?.detail;
      if (Array.isArray(detail)) {
        message = detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
      } else if (typeof detail === "string") {
        message = detail;
      } else {
        message = "Invalid request. Please check the form and try again.";
      }
    } else if (status >= 500) {
      message = error.response.data?.detail || "The server ran into a problem. Please try again shortly.";
    } else if (error.response.data?.detail) {
      message = typeof error.response.data.detail === "string" ? error.response.data.detail : message;
    }

    return Promise.reject({ status, message, raw: error });
  }
);

export function wsBaseUrl() {
  return BASE_URL.replace(/^http/, "ws");
}

export default api;
