import type { Config } from "@netlify/functions";
import { adminConfigured, checkCredentials, clearSessionCookie, error, isAdmin, json, sessionCookie } from "./lib/store.js";

export default async (req: Request) => {
  const action = new URL(req.url).pathname.split("/").pop();

  if (action === "session" && req.method === "GET") {
    return json({ signedIn: isAdmin(req), configured: adminConfigured() });
  }

  if (action === "logout" && req.method === "POST") {
    return json({ signedIn: false }, 200, { "Set-Cookie": clearSessionCookie() });
  }

  if (action === "login" && req.method === "POST") {
    if (!adminConfigured()) return error("The seller password has not been set up for this site yet.", 503);
    let body: Record<string, unknown> = {};
    try {
      body = await req.json();
    } catch {
      return error("Invalid request body");
    }
    if (!checkCredentials(String(body.username ?? ""), String(body.password ?? ""))) {
      return error("That username and password don't match. Please try again.", 401);
    }
    return json({ signedIn: true }, 200, { "Set-Cookie": sessionCookie() });
  }

  return error("Not found", 404);
};

export const config: Config = {
  path: ["/api/admin/session", "/api/admin/login", "/api/admin/logout"],
};
