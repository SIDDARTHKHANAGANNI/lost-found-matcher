const API_BASE = "http://localhost:8000";
 
function getToken() {
  return localStorage.getItem("token");
}
 
function setToken(token) {
  localStorage.setItem("token", token);
}
 
function clearToken() {
  localStorage.removeItem("token");
}
 
function requireAuth() {
  if (!getToken()) {
    window.location.href = "login.html";
    throw new Error("Not authenticated");
  }
}
 
function extractErrorMessage(err) {
  // Simple FastAPI HTTPException: { detail: "some string" }
  if (typeof err.detail === "string") {
    return err.detail;
  }
 
  // Pydantic ValidationError converted via e.errors(): detail is a list of
  // objects like { type, loc, msg, input, ctx }
  if (Array.isArray(err.detail)) {
    return err.detail
      .map(e => {
        if (typeof e === "string") return e;
        if (e.msg) {
          const field = Array.isArray(e.loc) ? e.loc[e.loc.length - 1] : "";
          return field ? `${field}: ${e.msg}` : e.msg;
        }
        return JSON.stringify(e);
      })
      .join(" | ");
  }
 
  // fallback — anything else, stringify safely instead of [object Object]
  if (err.detail) {
    try {
      return JSON.stringify(err.detail);
    } catch {
      return "Request failed";
    }
  }
 
  return "Request failed";
}
 
async function apiRequest(path, options = {}) {
  const headers = options.headers || {};
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
 
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
 
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(extractErrorMessage(err));
  }
 
  return res.json();
}
 