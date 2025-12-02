const FILTERS = ["Tutti", "Italia", "Milano", "Spagna"];
const STORAGE_KEY = "cerbbot_admin_token";
const POLL_INTERVAL = 10000;

const state = {
  bearer: null,
  products: [],
  filtered: [],
  filter: "Tutti",
  admins: [],
  superAdmin: document.body.dataset.superAdmin,
  signatures: {
    products: "",
    admins: ""
  },
  pollHandle: null
};

const refs = {
  loginView: document.getElementById("login-view"),
  dashboard: document.getElementById("dashboard"),
  loginForm: document.getElementById("login-form"),
  loginStatus: document.getElementById("login-status"),
  logoutBtn: document.getElementById("logout-btn"),
  filters: document.getElementById("admin-filters"),
  productsTable: document.getElementById("products-table"),
  productForm: document.getElementById("product-form"),
  resetForm: document.getElementById("reset-form"),
  adminsList: document.getElementById("admins-list"),
  adminForm: document.getElementById("admin-form")
};

function field(name) {
  return refs.productForm.elements.namedItem(name);
}

function setStatus(message, type = "info") {
  refs.loginStatus.textContent = message;
  refs.loginStatus.style.color = type === "error" ? "#ff6b6b" : "var(--muted)";
}

function saveToken(token) {
  state.bearer = token;
  localStorage.setItem(STORAGE_KEY, token);
}

function clearToken() {
  state.bearer = null;
  localStorage.removeItem(STORAGE_KEY);
  stopRealtimeSync();
}

function showDashboard() {
  refs.loginView.hidden = true;
  refs.dashboard.hidden = false;
}

function showLogin() {
  refs.loginView.hidden = false;
  refs.dashboard.hidden = true;
}

async function apiFetch(path, options = {}) {
  if (!state.bearer) {
    throw new Error("Missing bearer token");
  }
  const res = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
      Authorization: `Bearer ${state.bearer}`
    }
  });
  if (res.status === 401) {
    clearToken();
    showLogin();
    throw new Error("Sessione scaduta");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || "Richiesta fallita");
  }
  if (res.status === 204) {
    return null;
  }
  return res.json();
}

async function loginWithPassword(password) {
  const res = await fetch("/api/auth", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ intent: "password", password })
  });
  if (!res.ok) {
    throw new Error("Password errata");
  }
  const data = await res.json();
  saveToken(data.bearer);
  setStatus("Accesso riuscito");
}

async function loadData() {
  const [{ items }, adminsData] = await Promise.all([
    apiFetch("/api/products"),
    apiFetch("/api/admins")
  ]);
  syncProducts(items, { force: true });
  syncAdmins(adminsData.admins, { force: true });
  startRealtimeSync();
}

function computeSignature(items) {
  return JSON.stringify(items?.map((item) => ({
    id: item.id,
    name: item.name,
    category: item.category,
    media: item.media,
    description: item.description,
    featured: Boolean(item.featured)
  })) ?? []);
}

function syncProducts(items, { force = false } = {}) {
  const signature = computeSignature(items);
  if (!force && signature === state.signatures.products) {
    return;
  }
  state.signatures.products = signature;
  state.products = items;
  state.filtered = items;
  applyFilter();
}

function syncAdmins(admins, { force = false } = {}) {
  const signature = JSON.stringify(admins);
  if (!force && signature === state.signatures.admins) {
    return;
  }
  state.signatures.admins = signature;
  state.admins = admins;
  renderAdmins();
}

async function refreshData() {
  try {
    const [{ items }, adminsData] = await Promise.all([
      apiFetch("/api/products"),
      apiFetch("/api/admins")
    ]);
    syncProducts(items);
    syncAdmins(adminsData.admins);
  } catch (error) {
    console.warn("Sync fallita", error);
  }
}

function startRealtimeSync() {
  if (state.pollHandle) return;
  state.pollHandle = setInterval(refreshData, POLL_INTERVAL);
}

function stopRealtimeSync() {
  if (!state.pollHandle) return;
  clearInterval(state.pollHandle);
  state.pollHandle = null;
}

function renderFilters() {
  refs.filters.innerHTML = "";
  FILTERS.forEach((filter) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `filter-btn${state.filter === filter ? " active" : ""}`;
    button.textContent = filter;
    button.addEventListener("click", () => {
      state.filter = filter;
      applyFilter();
    });
    refs.filters.appendChild(button);
  });
}

function applyFilter() {
  if (state.filter === "Tutti") {
    state.filtered = state.products;
  } else {
    state.filtered = state.products.filter((item) => item.category === state.filter);
  }
  renderFilters();
  renderProducts();
}

function renderProducts() {
  const template = document.getElementById("product-row");
  refs.productsTable.innerHTML = "";
  state.filtered.forEach((product) => {
    const clone = template.content.cloneNode(true);
    clone.querySelector(".name").textContent = product.name;
    clone.querySelector(".category").textContent = product.category;
    clone.querySelector(".media").textContent = product.media;
    clone.querySelectorAll("button").forEach((btn) => {
      btn.dataset.id = product.id;
      btn.addEventListener("click", () => handleRowAction(btn.dataset.action, product.id));
    });
    refs.productsTable.appendChild(clone);
  });
}

function fillForm(product) {
  field("id").value = product.id;
  field("name").value = product.name;
  field("category").value = product.category;
  field("media").value = product.media;
  field("description").value = product.description;
  field("featured").value = product.featured ? "true" : "false";
}

function resetForm() {
  refs.productForm.reset();
  field("id").value = "";
}

async function handleRowAction(action, id) {
  const product = state.products.find((item) => item.id === id);
  if (!product) return;
  if (action === "edit") {
    fillForm(product);
    window.scrollTo({ top: refs.productForm.offsetTop - 80, behavior: "smooth" });
  }
  if (action === "delete") {
    if (!confirm(`Eliminare ${product.name}?`)) return;
    await apiFetch(`/api/products/${id}`, { method: "DELETE" });
    state.products = state.products.filter((item) => item.id !== id);
    state.signatures.products = computeSignature(state.products);
    applyFilter();
  }
}

async function handleProductSubmit(event) {
  event.preventDefault();
  const formData = new FormData(refs.productForm);
  const payload = Object.fromEntries(formData.entries());
  payload.featured = payload.featured === "true";
  const hasId = Boolean(payload.id);
  const url = hasId ? `/api/products/${payload.id}` : "/api/products";
  const method = hasId ? "PUT" : "POST";
  const response = await apiFetch(url, { method, body: JSON.stringify(payload) });
  const saved = response?.item;
  if (hasId) {
    state.products = state.products.map((prod) => (prod.id === saved.id ? saved : prod));
  } else {
    state.products.push(saved);
  }
  state.signatures.products = computeSignature(state.products);
  resetForm();
  applyFilter();
}

function renderAdmins() {
  refs.adminsList.innerHTML = "";
  const template = document.getElementById("admin-item");
  state.admins.forEach((username) => {
    const clone = template.content.cloneNode(true);
    clone.querySelector(".username").textContent = username;
    const button = clone.querySelector("button");
    button.dataset.username = username;
    if (username === state.superAdmin) {
      button.disabled = true;
      button.textContent = "Super admin";
    } else {
      button.addEventListener("click", () => removeAdmin(username));
    }
    refs.adminsList.appendChild(clone);
  });
}

async function addAdmin(event) {
  event.preventDefault();
  const formData = new FormData(refs.adminForm);
  const username = formData.get("username").trim();
  if (!username.startsWith("@")) {
    alert("Usa il formato @username");
    return;
  }
  const data = await apiFetch("/api/admins", {
    method: "POST",
    body: JSON.stringify({ username })
  });
  syncAdmins(data.admins, { force: true });
  refs.adminForm.reset();
}

async function removeAdmin(username) {
  await apiFetch(`/api/admins/${encodeURIComponent(username)}`, { method: "DELETE" });
  syncAdmins(state.admins.filter((admin) => admin !== username), { force: true });
}

function bindEvents() {
  refs.loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const password = new FormData(refs.loginForm).get("password");
    try {
      await loginWithPassword(password);
      await loadData();
      showDashboard();
    } catch (error) {
      setStatus(error.message, "error");
    }
  });
  refs.logoutBtn.addEventListener("click", () => {
    clearToken();
    showLogin();
  });
  refs.productForm.addEventListener("submit", (event) => {
    handleProductSubmit(event).catch((error) => alert(error.message));
  });
  refs.resetForm.addEventListener("click", resetForm);
  refs.adminForm.addEventListener("submit", (event) => {
    addAdmin(event).catch((error) => alert(error.message));
  });
}

async function tryAutoLogin() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (!saved) return;
  saveToken(saved);
  try {
    await loadData();
    showDashboard();
  } catch (error) {
    clearToken();
    console.error(error);
  }
}

function init() {
  bindEvents();
  renderFilters();
  tryAutoLogin();
}

document.addEventListener("DOMContentLoaded", init);
