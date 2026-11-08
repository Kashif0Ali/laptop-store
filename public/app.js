// Shared storefront helpers: layout, formatting, API access, and small UI behaviours.
export const STORE = {
  name: "AK Apple Store",
  whatsapp: "923183703386",
  whatsappDisplay: "03183703386",
};
export const whatsappLink = `https://wa.me/${STORE.whatsapp}`;

export function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

export const rupees = (n) => "Rs. " + Number(n || 0).toLocaleString("en-US");

export async function api(path, options = {}) {
  const res = await fetch(path, { cache: "no-store", ...options });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(data.error || `Request failed (${res.status})`), { status: res.status });
  return data;
}

let svgId = 0;
export function laptopSvg(className = "laptop-mini") {
  const id = `l${svgId++}`;
  return `<svg class="${className}" viewBox="0 0 400 260" role="img" aria-label="Laptop illustration"><defs><linearGradient id="s${id}" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#baff70"/><stop offset=".48" stop-color="#8d74ed"/><stop offset="1" stop-color="#30304c"/></linearGradient><linearGradient id="b${id}" x2="0" y2="1"><stop stop-color="#d5d4e4"/><stop offset="1" stop-color="#626276"/></linearGradient></defs><rect x="61" y="25" width="278" height="184" rx="14" fill="#77778b"/><rect x="68" y="32" width="264" height="169" rx="9" fill="#181827"/><rect x="77" y="41" width="246" height="151" rx="5" fill="#202037"/><circle cx="200" cy="48" r="2" fill="#b9b8cb"/><rect x="96" y="62" width="55" height="6" rx="3" fill="#d8ff72"/><rect x="96" y="78" width="122" height="15" rx="4" fill="url(#s${id})"/><rect x="96" y="99" width="79" height="7" rx="3" fill="#86839f"/><rect x="96" y="123" width="65" height="48" rx="6" fill="#a186fb" opacity=".8"/><rect x="169" y="123" width="65" height="48" rx="6" fill="#d8ff72" opacity=".8"/><rect x="242" y="123" width="65" height="48" rx="6" fill="#65dce8" opacity=".8"/><path d="M37 213h326l30 19c4 3 2 9-5 9H12c-7 0-9-6-5-9l30-19Z" fill="url(#b${id})"/><path d="M163 214h74l8 7h-90l8-7Z" fill="#77778b"/></svg>`;
}

const brandMark = `<a class="brand" href="/"><span class="brand-mark" style="font-size:11px;letter-spacing:-.08em">AK</span>Apple Store<span style="color:var(--lime)">.</span></a>`;

function renderShell() {
  document.body.insertAdjacentHTML(
    "afterbegin",
    `<div class="announcement">COMPLIMENTARY DELIVERY · TESTED TECH · ZERO GUESSWORK</div>
    <header class="site-header">
      <nav class="nav" aria-label="Main navigation">
        ${brandMark}
        <div class="nav-links" id="nav-links"><a href="/#shop">Shop MacBooks</a><a href="/#why-ak">Why AK Apple</a><a href="/admin">Seller portal</a></div>
        <div class="nav-actions"><a class="button button-small" href="/#shop">Find your laptop <span aria-hidden="true">↗</span></a><button class="menu-toggle" id="menu-toggle" aria-expanded="false" aria-controls="nav-links">Menu</button></div>
      </nav>
    </header>`,
  );
  document.body.insertAdjacentHTML(
    "beforeend",
    `<footer class="site-footer"><div class="footer-inner">${brandMark}<span>Your next Mac starts here.</span><span>© ${new Date().getFullYear()} ${STORE.name}</span></div></footer>
    <div class="toast" id="toast" role="status" aria-live="polite"></div>`,
  );
  const toggle = document.getElementById("menu-toggle");
  const links = document.getElementById("nav-links");
  toggle.addEventListener("click", () => toggle.setAttribute("aria-expanded", String(links.classList.toggle("open"))));
}
renderShell();

let toastTimer;
export function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2200);
}

export function bindFavorites(root = document) {
  const saved = new Set(JSON.parse(localStorage.getItem("ak-favorites") || "[]"));
  root.querySelectorAll("[data-favorite]").forEach((button) => {
    const id = button.dataset.favorite;
    const update = () => {
      button.classList.toggle("active", saved.has(id));
      button.setAttribute("aria-pressed", String(saved.has(id)));
      button.textContent = saved.has(id) ? "♥" : "♡";
    };
    update();
    button.addEventListener("click", () => {
      saved.has(id) ? saved.delete(id) : saved.add(id);
      localStorage.setItem("ak-favorites", JSON.stringify([...saved]));
      update();
      showToast(saved.has(id) ? "Saved to your favorites" : "Removed from favorites");
    });
  });
}

export function setTitle(title) {
  document.title = `${title} · ${STORE.name}`;
}
