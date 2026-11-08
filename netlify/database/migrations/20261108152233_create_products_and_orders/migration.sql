CREATE TABLE "orders" (
	"id" text PRIMARY KEY,
	"product_id" text NOT NULL,
	"product_name" text NOT NULL,
	"customer_name" text NOT NULL,
	"customer_phone" text NOT NULL,
	"delivery_address" text NOT NULL,
	"quantity" integer NOT NULL,
	"unit_price" integer NOT NULL,
	"total_price" integer NOT NULL,
	"status" text DEFAULT 'Pending' NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "products" (
	"id" text PRIMARY KEY,
	"brand" text NOT NULL,
	"model" text NOT NULL,
	"processor" text DEFAULT '' NOT NULL,
	"generation" text DEFAULT '' NOT NULL,
	"ram" text DEFAULT '' NOT NULL,
	"ssd" text DEFAULT '' NOT NULL,
	"screen" text DEFAULT '' NOT NULL,
	"price" integer DEFAULT 0 NOT NULL,
	"condition" text DEFAULT '' NOT NULL,
	"availability" text DEFAULT 'Available' NOT NULL,
	"images" jsonb DEFAULT '[]' NOT NULL,
	"description" text DEFAULT '' NOT NULL,
	"sort_order" integer DEFAULT 0 NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
