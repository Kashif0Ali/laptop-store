import type { Config, Context } from "@netlify/functions";
import { randomUUID } from "node:crypto";
import { asc, eq, sql } from "drizzle-orm";
import { getStore } from "@netlify/blobs";
import { db } from "../../db/index.js";
import { products } from "../../db/schema.js";
import { error, isAvailable, json, requireAdmin } from "./lib/store.js";

const IMAGE_TYPES: Record<string, string> = {
  "image/jpeg": "jpg",
  "image/png": "png",
  "image/webp": "webp",
};
const MAX_IMAGE_BYTES = 4 * 1024 * 1024;
const TEXT_FIELDS = ["brand", "model", "processor", "generation", "ram", "ssd", "screen", "condition", "availability", "description"] as const;

function text(form: FormData, key: string, max = 200) {
  return String(form.get(key) ?? "").trim().slice(0, max);
}

async function deleteUploads(images: string[]) {
  const store = getStore("product-images");
  await Promise.all(
    images
      .filter((src) => src.startsWith("/uploads/"))
      .map((src) => store.delete(src.slice("/uploads/".length)).catch(() => {})),
  );
}

export default async (req: Request, context: Context) => {
  const denied = requireAdmin(req);
  if (denied) return denied;

  if (req.method === "GET") {
    const rows = await db.select().from(products).orderBy(asc(products.sortOrder), asc(products.createdAt));
    return json(rows.map((p) => ({ ...p, available: isAvailable(p.availability) })));
  }

  if (req.method === "DELETE") {
    const id = String(context.params.id ?? "");
    const [removed] = await db.delete(products).where(eq(products.id, id)).returning();
    if (!removed) return error("Laptop not found", 404);
    await deleteUploads(removed.images);
    return json({ deleted: id });
  }

  if (req.method !== "POST") return error("Method not allowed", 405);

  let form: FormData;
  try {
    form = await req.formData();
  } catch {
    return error("Could not read the form. If you attached large photos, try fewer at a time.");
  }

  const id = text(form, "id", 80).replace(/\s+/g, "-");
  if (!id) return error("A product ID is required.");
  const values: Record<string, string> = {};
  for (const key of TEXT_FIELDS) values[key] = text(form, key, key === "description" ? 3000 : 200);
  if (!values.brand || !values.model) return error("Brand and model are required.");
  const price = Number.parseInt(text(form, "price").replace(/[^\d]/g, ""), 10);
  if (!(price > 0)) return error("Enter a price greater than zero (numbers only).");
  values.availability ||= "Available";

  const files = form.getAll("images").filter((f): f is File => f instanceof File && f.size > 0);
  for (const file of files) {
    if (!IMAGE_TYPES[file.type]) return error(`"${file.name}" is not a JPG, PNG, or WebP image.`);
    if (file.size > MAX_IMAGE_BYTES) return error(`"${file.name}" is larger than 4 MB.`);
  }

  const [existing] = await db.select().from(products).where(eq(products.id, id));
  const keepImages = form.get("keepImages") === "on";

  const store = getStore("product-images");
  const uploaded: string[] = [];
  for (const file of files) {
    const key = `${randomUUID()}.${IMAGE_TYPES[file.type]}`;
    await store.set(key, await file.arrayBuffer());
    uploaded.push(`/uploads/${key}`);
  }

  const previous = existing?.images ?? [];
  const images = uploaded.length ? (keepImages ? [...previous, ...uploaded] : uploaded) : previous;

  const row = { ...values, price, images } as typeof products.$inferInsert;

  if (existing) {
    const [updated] = await db
      .update(products)
      .set({ ...row, updatedAt: new Date() })
      .where(eq(products.id, id))
      .returning();
    if (uploaded.length && !keepImages) await deleteUploads(previous);
    return json(updated);
  }

  const [{ next }] = await db
    .select({ next: sql<number>`coalesce(max(${products.sortOrder}), -1) + 1` })
    .from(products);
  const [created] = await db
    .insert(products)
    .values({ ...row, id, sortOrder: Number(next) })
    .returning();
  return json(created, 201);
};

export const config: Config = {
  path: ["/api/admin/products", "/api/admin/products/:id"],
  method: ["GET", "POST", "DELETE"],
};
