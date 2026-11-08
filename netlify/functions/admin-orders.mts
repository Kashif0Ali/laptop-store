import type { Config, Context } from "@netlify/functions";
import { desc, eq } from "drizzle-orm";
import { db } from "../../db/index.js";
import { orders } from "../../db/schema.js";
import { error, json, normalizePhone, ORDER_STATUSES, requireAdmin } from "./lib/store.js";

export default async (req: Request, context: Context) => {
  const denied = requireAdmin(req);
  if (denied) return denied;

  if (req.method === "GET") {
    const rows = await db.select().from(orders).orderBy(desc(orders.createdAt));
    return json({
      statuses: ORDER_STATUSES,
      orders: rows.map((o) => ({ ...o, customerWhatsapp: normalizePhone(o.customerPhone) })),
    });
  }

  const id = context.params.id;
  if (req.method === "PATCH" && id) {
    const { status } = await req.json().catch(() => ({}));
    if (!ORDER_STATUSES.includes(status)) return error("Invalid order status");
    const updated = await db.update(orders).set({ status }).where(eq(orders.id, id)).returning();
    if (!updated.length) return error("Order not found", 404);
    return json(updated[0]);
  }

  return error("Method not allowed", 405);
};

export const config: Config = {
  path: ["/api/admin/orders", "/api/admin/orders/:id"],
  method: ["GET", "PATCH"],
};
