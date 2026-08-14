let rawUrl = (import.meta.env.VITE_BACKEND_URL || "http://localhost:8000/api/v1").trim();

// Strip trailing slashes
rawUrl = rawUrl.replace(/\/+$/, "");

// Automatically append /api/v1 if not present
if (!rawUrl.endsWith("/api/v1")) {
  rawUrl = `${rawUrl}/api/v1`;
}

const API_BASE_URL = rawUrl;

export default API_BASE_URL;
export { API_BASE_URL };
