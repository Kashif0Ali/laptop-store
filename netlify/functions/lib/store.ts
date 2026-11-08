import { createHmac, timingSafeEqual, createHash } from "node:crypto";

export const STORE_NAME = "AK Apple Store";

const AVAILABLE_VALUES = new Set(["available", "in stock", "yes"]);
export const ORDER_STATUSES = ["Pending", "Confirmed", "Completed", "Cancelled"] as const;

export function isAvailable(availability: string | null | undefined) {
  return AVAILABLE_VALUES.has(String(availability ?? "").trim().toLowerCase());
}

/** Normalises a Pakistani-style number (03xx…) to international wa.me format (923xx…). */
export function normalizePhone(value: string) {
  let digits = String(value ?? "").replace(/\D/g, "");
  if (digits.startsWith("00")) digits = digits.slice(2);
  if (digits.startsWith("0")) digits = "92" + digits.slice(1);
  return digits;
}

export function storeWhatsapp() {
  return normalizePhone(Netlify.env.get("WHATSAPP_NUMBER") || "03183703386");
}

export function formatRupees(amount: number) {
  return "Rs. " + amount.toLocaleString("en-US");
}

export function json(data: unknown, status = 200, headers: Record<string, string> = {}) {
  return Response.json(data, { status, headers: { "Cache-Control": "no-store", ...headers } });
}

export function error(message: string, status = 400) {
  return json({ error: message }, status);
}

// ---------- Seller session (signed cookie) ----------

const COOKIE = "ak_admin";
const SESSION_SECONDS = 60 * 60 * 12;

function credentials() {
  return {
    user: Netlify.env.get("ADMIN_USER") || "admin",
    password: Netlify.env.get("ADMIN_PASSWORD") || "",
  };
}

function signingKey() {
  const { user, password } = credentials();
  return createHash("sha256").update(`ak-admin-session:${user}:${password}`).digest();
}

function sign(value: string) {
  return createHmac("sha256", signingKey()).update(value).digest("base64url");
}

function safeEqual(a: string, b: string) {
  const ab = Buffer.from(a);
  const bb = Buffer.from(b);
  return ab.length === bb.length && timingSafeEqual(ab, bb);
}

export function adminConfigured() {
  return credentials().password.length > 0;
}

export function checkCredentials(user: string, password: string) {
  const expected = credentials();
  if (!expected.password) return false;
  // Evaluate both comparisons to avoid leaking which one failed.
  const userOk = safeEqual(String(user), expected.user);
  const passOk = safeEqual(String(password), expected.password);
  return userOk && passOk;
}

export function sessionCookie() {
  const exp = String(Math.floor(Date.now() / 1000) + SESSION_SECONDS);
  const value = `${exp}.${sign(exp)}`;
  return `${COOKIE}=${value}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${SESSION_SECONDS}`;
}

export function clearSessionCookie() {
  return `${COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0`;
}

export function isAdmin(req: Request) {
  if (!adminConfigured()) return false;
  const cookies = req.headers.get("cookie") || "";
  const match = cookies.split(/;\s*/).find((c) => c.startsWith(`${COOKIE}=`));
  if (!match) return false;
  const [exp, signature] = match.slice(COOKIE.length + 1).split(".");
  if (!exp || !signature) return false;
  if (Number(exp) < Date.now() / 1000) return false;
  return safeEqual(signature, sign(exp));
}

export function requireAdmin(req: Request) {
  return isAdmin(req) ? null : error("Please sign in to the seller portal.", 401);
}
