import { getProduct, saveProduct, deleteProduct } from "../../lib/kv.js";
import { parseJsonBody } from "../../lib/body.js";
import { json, methodNotAllowed, badRequest, unauthorized, notFound } from "../../lib/response.js";
import { verifyBearer } from "../../lib/auth.js";

function extractId(req) {
  if (req.query?.id) {
    return req.query.id;
  }
  const segments = req.url.split("?")[0].split("/");
  return segments[segments.length - 1];
}

export default async function handler(req, res) {
  const id = extractId(req);

  if (req.method === "GET") {
    const item = await getProduct(id);
    if (!item) {
      notFound(res);
      return;
    }
    json(res, 200, { item });
    return;
  }

  if (req.method === "PUT") {
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
    const existing = await getProduct(id);
    if (!existing) {
      notFound(res);
      return;
    }
    const updated = await saveProduct({
      id,
      name: body.name ?? existing.name,
      category: body.category ?? existing.category,
      media: body.media ?? existing.media,
      description: body.description ?? existing.description,
      featured: body.featured ?? existing.featured
    });
    json(res, 200, { item: updated });
    return;
  }

  if (req.method === "DELETE") {
    const auth = verifyBearer(req);
    if (!auth) {
      unauthorized(res);
      return;
    }
    const existing = await getProduct(id);
    if (!existing) {
      notFound(res);
      return;
    }
    await deleteProduct(id);
    json(res, 204, {});
    return;
  }

  methodNotAllowed(res, ["GET", "PUT", "DELETE"]);
}
