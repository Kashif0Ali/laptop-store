import { api, bindFavorites, esc, laptopSvg, rupees } from "/app.js";

const grid = document.getElementById("product-grid");
const search = document.getElementById("product-search");
const sort = document.getElementById("sort-products");
const filters = document.getElementById("brand-filters");
const dialog = document.getElementById("quick-view");
let products = [];
let activeBrand = "all";

const searchText = (p) => [p.brand, p.model, p.processor, p.generation, p.ram, p.ssd, p.screen, p.condition].join(" ").toLowerCase();

function card(p) {
  const media = p.images[0]
    ? `<img src="${esc(p.images[0])}" alt="${esc(p.brand)} ${esc(p.model)} laptop" loading="lazy">`
    : laptopSvg();
  const specs2 = [p.ram && `${p.ram} RAM`, p.ssd, p.condition].filter(Boolean).join(" · ");
  return `<article class="product-card">
    <div class="product-media">${media}<span class="stock-tag">${esc(p.availability)}</span>
      <button type="button" class="favorite" data-favorite="${esc(p.id)}" aria-label="Save ${esc(p.brand)} ${esc(p.model)} to favorites" aria-pressed="false">♡</button></div>
    <div class="product-info">
      <div class="product-brand">${esc(p.brand)}</div><h3>${esc(p.model)}</h3>
      <div class="spec-line">${esc([p.processor, p.generation].filter(Boolean).join(" · "))}</div>
      <div class="spec-line">${esc(specs2)}</div>
      <div class="product-bottom">
        <span class="price">Indicative · ${rupees(p.price)}</span>
        <div class="card-actions">
          <button type="button" class="button button-secondary button-small" data-quick-view="${esc(p.id)}">Quick view</button>
          <a class="text-link" href="/product/${encodeURIComponent(p.id)}">Details ↗</a>
        </div>
      </div>
    </div>
  </article>`;
}

function render() {
  if (!products.length) {
    grid.innerHTML = `<div class="empty-state"><strong>Your next favorite is almost here.</strong>We’re refreshing the collection. Check back soon or message us for help finding a specific laptop.</div>`;
    return;
  }
  const query = search.value.trim().toLowerCase();
  let list = products.filter((p) => searchText(p).includes(query) && (activeBrand === "all" || p.brand.toLowerCase() === activeBrand));
  const order = sort.value;
  if (order === "price-low") list = [...list].sort((a, b) => a.price - b.price);
  if (order === "price-high") list = [...list].sort((a, b) => b.price - a.price);
  if (order === "name") list = [...list].sort((a, b) => `${a.brand} ${a.model}`.localeCompare(`${b.brand} ${b.model}`));
  grid.innerHTML = list.length
    ? list.map(card).join("")
    : `<div class="empty-state"><strong>No matches this time.</strong>Try another search or choose a different brand.</div>`;
  bindFavorites(grid);
}

function renderFilters() {
  const brands = [...new Set(products.map((p) => p.brand).filter(Boolean))].sort();
  if (brands.length < 2) return;
  filters.hidden = false;
  filters.innerHTML = [`<button type="button" class="filter-chip active" data-brand="all">All laptops</button>`, ...brands.map((b) => `<button type="button" class="filter-chip" data-brand="${esc(b.toLowerCase())}">${esc(b)}</button>`)].join("");
  filters.addEventListener("click", (e) => {
    const chip = e.target.closest("[data-brand]");
    if (!chip) return;
    activeBrand = chip.dataset.brand;
    filters.querySelectorAll("[data-brand]").forEach((c) => c.classList.toggle("active", c === chip));
    render();
  });
}

grid.addEventListener("click", (e) => {
  const button = e.target.closest("[data-quick-view]");
  if (!button) return;
  const p = products.find((x) => x.id === button.dataset.quickView);
  dialog.querySelector("[data-modal-brand]").textContent = p.brand;
  dialog.querySelector("[data-modal-title]").textContent = p.model;
  dialog.querySelector("[data-modal-price]").textContent = `Indicative · ${rupees(p.price)}`;
  dialog.querySelector("[data-modal-description]").textContent = p.description || "Carefully selected tech, ready for its next chapter.";
  dialog.querySelector("[data-modal-specs]").replaceChildren(
    ...[p.processor, p.ram && `${p.ram} RAM`, p.ssd, p.screen].filter(Boolean).map((s) => Object.assign(document.createElement("span"), { textContent: s })),
  );
  dialog.querySelector("[data-modal-link]").href = `/product/${encodeURIComponent(p.id)}`;
  dialog.showModal();
});
dialog.querySelector("[data-modal-close]").addEventListener("click", () => dialog.close());
document.getElementById("search-form").addEventListener("submit", (e) => e.preventDefault());
search.addEventListener("input", render);
sort.addEventListener("change", render);

const initialQuery = new URLSearchParams(location.search).get("q");
if (initialQuery) search.value = initialQuery;

try {
  products = await api("/api/products");
  renderFilters();
  render();
} catch (err) {
  grid.innerHTML = `<div class="empty-state"><strong>We couldn’t load the collection.</strong>${esc(err.message)} — please refresh to try again.</div>`;
}
