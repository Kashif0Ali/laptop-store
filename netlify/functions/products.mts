import type { Config, Context } from "@netlify/functions";
import { asc, eq } from "drizzle-orm";
import { db } from "../../db/index.js";
import { products } from "../../db/schema.js";
import { error, isAvailable, json } from "./lib/store.js";

export default async (_req: Request, context: Context) => {
  const { id } = context.params;

  if (id) {
    const [product] = await db.select().from(products).where(eq(products.id, id));
    if (!product) return error("Laptop not found", 404);
    return json({ ...product, available: isAvailable(product.availability) });
  }

  const rows = await db.select().from(products).orderBy(asc(products.sortOrder), asc(products.createdAt));
  return json(
    rows
      .filter((p) => isAvailable(p.availability))
      .map((p) => ({ ...p, available: true })),
  );
};

export const config: Config = {
  path: ["/api/products", "/api/products/:id"],
  method: "GET",
};
