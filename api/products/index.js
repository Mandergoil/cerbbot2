import { listProducts, saveProduct } from "../../lib/kv.js";
import { parseJsonBody } from "../../lib/body.js";
import { json, methodNotAllowed, badRequest, unauthorized } from "../../lib/response.js";
import { verifyBearer } from "../../lib/auth.js";
import { customAlphabet } from "nanoid";

const nanoid = customAlphabet("abcdefghijklmnopqrstuvwxyz0123456789", 8);

export default async function handler(req, res) {
  if (req.method === "GET") {
    const host = req.headers.host || process.env.VERCEL_URL || "localhost";
    const protocol = host.startsWith("localhost") ? "http" : "https";
    const url = new URL(req.url, `${protocol}://${host}`);
    const category = url.searchParams.get("category");
    const items = await listProducts(category);
    json(res, 200, { items });
    return;
  }

  if (req.method === "POST") {
    const auth = verifyBearer(req);
    if (!auth) {
      unauthorized(res);
      return;
    }
    let body;
    try {
      body = await parseJsonBody(req);
    } catch (error) {
      badRequest(res, error.message);
      return;
    }
    const { id = nanoid(), name, category, media, description, featured = false } = body;
    if (!name || !category || !media || !description) {
      badRequest(res, "Missing required fields");
      return;
    }
    const saved = await saveProduct({ id, name, category, media, description, featured });
    json(res, 201, { item: saved });
    return;
  }

  methodNotAllowed(res, ["GET", "POST"]);
}
