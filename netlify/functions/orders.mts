import type { Config, Context } from "@netlify/functions";
import { randomBytes } from "node:crypto";
import { eq } from "drizzle-orm";
import { db } from "../../db/index.js";
import { orders, products } from "../../db/schema.js";
import { error, formatRupees, isAvailable, json, STORE_NAME, storeWhatsapp } from "./lib/store.js";

type Order = typeof orders.$inferSelect;

function whatsappUrl(order: Order) {
  const message = [
    `${STORE_NAME} order request ${order.id}`,
    `Laptop: ${order.productName}`,
    `Quantity: ${order.quantity}`,
    `Indicative total: ${formatRupees(order.totalPrice)}`,
    `Customer: ${order.customerName}`,
    `Customer WhatsApp: ${order.customerPhone}`,
    `Delivery address: ${order.deliveryAddress}`,
    "Payment: Cash on delivery",
    "Please confirm stock, configuration, final price, and delivery.",
  ].join("\n");
  return `https://wa.me/${storeWhatsapp()}?text=${encodeURIComponent(message)}`;
}

function publicOrder(order: Order) {
  return {
    id: order.id,
    productId: order.productId,
    productName: order.productName,
    quantity: order.quantity,
    unitPrice: order.unitPrice,
    totalPrice: order.totalPrice,
    status: order.status,
    createdAt: order.createdAt,
    whatsappUrl: whatsappUrl(order),
  };
}

export default async (req: Request, context: Context) => {
  if (req.method === "GET") {
    const [order] = await db.select().from(orders).where(eq(orders.id, String(context.params.id || "")));
    if (!order) return error("Order not found", 404);
    return json(publicOrder(order));
  }

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return error("Invalid request body");
  }

  const productId = String(body.productId ?? "");
  const [product] = await db.select().from(products).where(eq(products.id, productId));
  if (!product) return error("Laptop not found", 404);
  if (!isAvailable(product.availability)) return error("This laptop is no longer available to order.", 409);

  const name = String(body.customerName ?? "").trim().slice(0, 100);
  const phone = String(body.customerPhone ?? "").trim().slice(0, 24);
  const address = String(body.deliveryAddress ?? "").trim().slice(0, 500);
  const quantity = Number.parseInt(String(body.quantity ?? "1"), 10);

  if (!name) return error("Enter your name to continue.");
  if (phone.replace(/\D/g, "").length < 9) return error("Enter a valid phone number so we can confirm your order.");
  if (address.length < 8) return error("Enter a complete delivery address.");
  if (!(quantity >= 1 && quantity <= 5)) return error("Choose a quantity between 1 and 5.");
  if (product.price <= 0) return error("This item has no valid listed price. Please contact the seller.");

  const [order] = await db
    .insert(orders)
    .values({
      id: randomBytes(6).toString("hex").toUpperCase(),
      productId: product.id,
      productName: `${product.brand} ${product.model}`,
      customerName: name,
      customerPhone: phone,
      deliveryAddress: address,
      quantity,
      unitPrice: product.price,
      totalPrice: product.price * quantity,
    })
    .returning();

  return json(publicOrder(order), 201);
};

export const config: Config = {
  path: ["/api/orders", "/api/orders/:id"],
  method: ["GET", "POST"],
};
