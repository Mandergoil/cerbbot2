import { removeAdmin } from "../../lib/kv.js";
import { json, methodNotAllowed, unauthorized } from "../../lib/response.js";
import { verifyBearer, ensureSuperAdmin } from "../../lib/auth.js";

function extractUsername(req) {
  if (req.query?.username) {
    return req.query.username;
  }
  const segments = req.url.split("?")[0].split("/");
  return segments[segments.length - 1];
}

export default async function handler(req, res) {
  if (req.method !== "DELETE") {
    methodNotAllowed(res, ["DELETE"]);
    return;
  }
  const claims = verifyBearer(req);
  if (!claims || !(await ensureSuperAdmin(claims.username))) {
    unauthorized(res);
    return;
  }
  const username = extractUsername(req);
  await removeAdmin(username);
  json(res, 204, {});
}
