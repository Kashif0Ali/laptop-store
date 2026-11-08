import { pgTable, text, integer, timestamp, jsonb } from "drizzle-orm/pg-core";

export const products = pgTable("products", {
  id: text().primaryKey(),
  brand: text().notNull(),
  model: text().notNull(),
  processor: text().notNull().default(""),
  generation: text().notNull().default(""),
  ram: text().notNull().default(""),
  ssd: text().notNull().default(""),
  screen: text().notNull().default(""),
  price: integer().notNull().default(0),
  condition: text().notNull().default(""),
  availability: text().notNull().default("Available"),
  images: jsonb().$type<string[]>().notNull().default([]),
  description: text().notNull().default(""),
  sortOrder: integer("sort_order").notNull().default(0),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

export const orders = pgTable("orders", {
  id: text().primaryKey(),
  productId: text("product_id").notNull(),
  productName: text("product_name").notNull(),
  customerName: text("customer_name").notNull(),
  customerPhone: text("customer_phone").notNull(),
  deliveryAddress: text("delivery_address").notNull(),
  quantity: integer().notNull(),
  unitPrice: integer("unit_price").notNull(),
  totalPrice: integer("total_price").notNull(),
  status: text().notNull().default("Pending"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});
