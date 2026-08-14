const API_BASE_URL =
  import.meta.env.VITE_BACKEND_URL ||
  "http://localhost:8000/api/v1";

export default API_BASE_URL;
export { API_BASE_URL };
