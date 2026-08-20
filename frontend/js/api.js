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
  if (typeof err.detail === "string") {
    return err.detail;
  }

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

function initCustomSelects() {
  document.querySelectorAll(".custom-select").forEach(wrapper => {
    const trigger = wrapper.querySelector(".custom-select-trigger");
    const options = wrapper.querySelectorAll(".custom-select-option");
    const hiddenInput = wrapper.querySelector("input[type=hidden]");

    trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      document.querySelectorAll(".custom-select.open").forEach(el => {
        if (el !== wrapper) el.classList.remove("open");
      });
      wrapper.classList.toggle("open");
    });

    options.forEach(opt => {
      opt.addEventListener("click", () => {
        options.forEach(o => o.classList.remove("selected"));
        opt.classList.add("selected");
        trigger.childNodes[0].textContent = opt.textContent;
        hiddenInput.value = opt.dataset.value;
        wrapper.classList.remove("open");
        hiddenInput.dispatchEvent(new Event("change"));
      });
    });
  });

  document.addEventListener("click", () => {
    document.querySelectorAll(".custom-select.open").forEach(el => el.classList.remove("open"));
  });
} 