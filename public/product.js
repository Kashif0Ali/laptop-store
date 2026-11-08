import { api, esc, laptopSvg, rupees, setTitle, whatsappLink } from "/app.js";

const root = document.getElementById("product-root");
const id = decodeURIComponent(location.pathname.replace(/^\/product\/?/, "").replace(/\/$/, "")) || new URLSearchParams(location.search).get("id") || "";

function notFound() {
  setTitle("Laptop not found");
  root.innerHTML = `<section class="not-found"><span class="eyebrow">Not found</span><h1>That laptop has moved on.</h1><p class="muted">It may have been sold or removed from the collection.</p><a class="button" href="/#shop">Browse the collection ↗</a></section>`;
}

function render(p) {
  setTitle(`${p.brand} ${p.model}`);
  const main = p.images[0] ? `<img data-gallery-main src="${esc(p.images[0])}" alt="${esc(p.brand)} ${esc(p.model)} laptop">` : laptopSvg("laptop-art");
  const thumbs = p.images.length > 1
    ? `<div class="thumbs">${p.images.map((src, i) => `<button type="button" class="thumb" data-gallery-image="${esc(src)}" aria-label="View product image ${i + 1}"><img src="${esc(src)}" alt="" loading="lazy"></button>`).join("")}</div>`
    : "";
  const spec = (label, value) => `<div class="spec"><small>${label}</small><b>${esc(value || "—")}</b></div>`;
  const orderForm = p.available
    ? `<div class="form-card order-form" id="order-form">
        <h3>Place an order request</h3>
        <p class="muted" style="margin-top:-7px">Cash on delivery. We’ll confirm stock, condition, delivery, and final price on WhatsApp.</p>
        <p class="form-error" role="alert" id="order-error" hidden></p>
        <form class="stack" id="order">
          <label>Your name<input class="field" name="customerName" maxlength="100" autocomplete="name" required></label>
          <label>Your WhatsApp number<input class="field" name="customerPhone" type="tel" maxlength="24" autocomplete="tel" placeholder="03xx xxxxxxx" required></label>
          <label>Delivery address<textarea class="field" name="deliveryAddress" rows="3" maxlength="500" minlength="8" autocomplete="street-address" required></textarea></label>
          <label>Quantity<select class="select" name="quantity">${[1, 2, 3, 4, 5].map((q) => `<option>${q}</option>`).join("")}</select></label>
          <button class="button" type="submit">Continue to WhatsApp order ↗</button>
        </form>
      </div>`
    : `<div class="form-card"><h3>Currently unavailable</h3><p class="muted">This laptop isn’t available right now. Message us on WhatsApp to ask about restocking.</p></div>`;

  root.innerHTML = `<section class="container product-layout">
    <div><div class="gallery-main">${main}</div>${thumbs}</div>
    <div class="product-detail">
      <a class="text-link" href="/#shop">← Back to collection</a>
      <div style="margin-top:24px"><span class="eyebrow">${esc(p.brand)} · ${esc(p.availability)}</span></div>
      <h1>${esc(p.model)}</h1>
      <div class="product-brand">${esc([p.condition, p.generation].filter(Boolean).join(" · "))}</div>
      <div class="detail-price">Indicative · ${rupees(p.price)}</div>
      <p class="detail-description">${esc(p.description || "Thoughtfully selected, carefully described, and ready for your next big idea.")}</p>
      <div class="spec-grid">${spec("Processor", p.processor)}${spec("Memory", p.ram)}${spec("Storage", p.ssd)}${spec("Display", p.screen)}</div>
      <div class="detail-actions">
        ${p.available ? `<a class="button" href="#order-form">Order this laptop ↘</a>` : ""}
        <a class="button button-secondary" href="${whatsappLink}?text=${encodeURIComponent(`Hi, I have a question about the ${p.brand} ${p.model}.`)}" target="_blank" rel="noopener noreferrer">Questions? WhatsApp us ↗</a>
      </div>
      ${orderForm}
    </div>
  </section>`;

  root.querySelectorAll("[data-gallery-image]").forEach((b) =>
    b.addEventListener("click", () => (root.querySelector("[data-gallery-main]").src = b.dataset.galleryImage)),
  );

  const form = document.getElementById("order");
  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorBox = document.getElementById("order-error");
    const button = form.querySelector("button");
    errorBox.hidden = true;
    button.disabled = true;
    button.textContent = "Saving your request…";
    try {
      const order = await api("/api/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ productId: p.id, ...Object.fromEntries(new FormData(form)) }),
      });
      location.href = `/order/${encodeURIComponent(order.id)}`;
    } catch (err) {
      errorBox.textContent = err.message;
      errorBox.hidden = false;
      button.disabled = false;
      button.textContent = "Continue to WhatsApp order ↗";
    }
  });
}

try {
  if (!id) throw Object.assign(new Error("Missing id"), { status: 404 });
  render(await api(`/api/products/${encodeURIComponent(id)}`));
} catch (err) {
  if (err.status === 404) notFound();
  else root.innerHTML = `<section class="not-found"><h1>Something went wrong.</h1><p class="muted">${esc(err.message)}</p><a class="button" href="">Try again</a></section>`;
}
