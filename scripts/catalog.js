const categories = ["Italia", "Milano", "Spagna"];
const POLL_INTERVAL = 10000;
const SAMPLE_PRODUCTS = [
  {
    id: "italia-velvet",
    name: "Italia Velvet",
    category: "Italia",
    media: "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=800&q=80",
    description: "Miscela scura con note di cacao e amarena. Selezione limitata per i clienti VIP."
  },
  {
    id: "italia-notte",
    name: "Italia Notte",
    category: "Italia",
    media: "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=801&q=80",
    description: "Taglio vellutato per degustazioni private. Packaging olografico firmato The History Farm."
  },
  {
    id: "milano-underground",
    name: "Milano Underground",
    category: "Milano",
    media: "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=800&q=80",
    description: "Drop urbano pensato per i clienti del circuito milanese. Disponibile solo su appuntamento."
  },
  {
    id: "milano-neon",
    name: "Milano Neon",
    category: "Milano",
    media: "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=800&q=80",
    description: "Linea fluorescente con inserti metallici. Box numerati e certificato digitale."
  },
  {
    id: "spagna-costa",
    name: "Spagna Costa",
    category: "Spagna",
    media: "https://images.unsplash.com/photo-1481277542470-605612bd2d61?auto=format&fit=crop&w=800&q=80",
    description: "Blend estivo ispirato alla costa iberica. Inclusa spedizione express dal nodo di Barcellona."
  }
];
const state = {
  products: SAMPLE_PRODUCTS,
  filtered: SAMPLE_PRODUCTS,
  active: "Tutti",
  signature: "",
  pollHandle: null
};

function createCard(product) {
  const { id, name, media, description, category } = product;
  const article = document.createElement("article");
  article.className = "card";
  article.innerHTML = `
    <small>${category}</small>
    <h3>${name}</h3>
    <figure>${renderMediaTag(media, `${name} media`)} </figure>
    <button data-id="${id}">Apri scheda</button>
  `;
  article.querySelector("button").addEventListener("click", () => openLightbox(product));
  return article;
}

function renderMediaTag(src, alt) {
  if (!src) return "";
  if (src.endsWith(".mp4") || src.includes("video")) {
    return `<video src="${src}" autoplay muted loop playsinline></video>`;
  }
  return `<img src="${src}" alt="${alt}">`;
}

function paintGrid(items) {
  const grid = document.querySelector("#product-grid");
  grid.innerHTML = "";
  if (!items.length) {
    grid.innerHTML = `<p class="empty">Nessun prodotto in questa categoria.</p>`;
    return;
  }
  items.forEach((item) => grid.appendChild(createCard(item)));
}

function applyActiveFilter() {
  const category = state.active;
  document.querySelectorAll(".filter-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.category === category);
  });
  state.filtered =
    category === "Tutti"
      ? state.products
      : state.products.filter((product) => product.category === category);
  paintGrid(state.filtered);
}

function filterBy(category) {
  state.active = category;
  applyActiveFilter();
}

function openLightbox(product) {
  const layer = document.querySelector("#lightbox");
  layer.classList.remove("hidden");
  layer.querySelector("h3").textContent = product.name;
  layer.querySelector("figure").innerHTML = renderMediaTag(product.media, product.name);
  layer.querySelector("p").textContent = product.description;
}

function setupLightbox() {
  const layer = document.querySelector("#lightbox");
  layer.addEventListener("click", (event) => {
    if (event.target.matches("#lightbox, .close")) {
      layer.classList.add("hidden");
    }
  });
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

async function fetchProducts({ silent = false } = {}) {
  const res = await fetch("/api/products");
  if (!res.ok) {
    throw new Error("Unable to load products");
  }
  const { items } = await res.json();
  const signature = computeSignature(items);
  if (silent && signature === state.signature) {
    return;
  }
  state.signature = signature;
  state.products = items;
  if (state.active === "") {
    state.active = "Tutti";
  }
  applyActiveFilter();
}

function renderFilters() {
  const container = document.querySelector(".filters");
  const all = document.createElement("button");
  all.className = "filter-btn active";
  all.textContent = "Tutti";
  all.dataset.category = "Tutti";
  all.addEventListener("click", () => filterBy("Tutti"));
  container.appendChild(all);
  categories.forEach((cat) => {
    const button = document.createElement("button");
    button.className = "filter-btn";
    button.dataset.category = cat;
    button.textContent = cat;
    button.addEventListener("click", () => filterBy(cat));
    container.appendChild(button);
  });
}

function startLiveUpdates() {
  if (state.pollHandle) return;
  state.pollHandle = setInterval(() => {
    fetchProducts({ silent: true }).catch((error) => console.warn("Polling error", error));
  }, POLL_INTERVAL);
}

async function main() {
  setupLightbox();
  renderFilters();
  applyActiveFilter();
  try {
    await fetchProducts();
    startLiveUpdates();
  } catch (error) {
    const grid = document.querySelector("#product-grid");
    grid.innerHTML = `<p class="error">${error.message}</p>`;
  }
}

document.addEventListener("DOMContentLoaded", main);
