import type { Config, Context } from "@netlify/functions";
import { getStore } from "@netlify/blobs";

const CONTENT_TYPES: Record<string, string> = { jpg: "image/jpeg", png: "image/png", webp: "image/webp" };

export default async (_req: Request, context: Context) => {
  const key = String(context.params.key ?? "");
  const data = await getStore("product-images").get(key, { type: "arrayBuffer" });
  if (!data) return new Response("Image not found", { status: 404 });
  const ext = key.split(".").pop()?.toLowerCase() ?? "";
  return new Response(data, {
    headers: {
      "Content-Type": CONTENT_TYPES[ext] ?? "application/octet-stream",
      // Keys are random and never overwritten, so the image can be cached forever.
      "Cache-Control": "public, max-age=31536000, immutable",
    },
  });
};

export const config: Config = {
  path: "/uploads/:key",
  method: "GET",
};
