import { listAdmins, addAdmin } from "../../lib/kv.js";
import { parseJsonBody } from "../../lib/body.js";
import { json, methodNotAllowed, unauthorized, badRequest } from "../../lib/response.js";
import { verifyBearer, ensureAdmin, ensureSuperAdmin } from "../../lib/auth.js";

export default async function handler(req, res) {
  const claims = verifyBearer(req);
  if (!claims) {
    unauthorized(res);
    return;
  }

  if (req.method === "GET") {
    if (!(await ensureAdmin(claims.username))) {
      unauthorized(res);
      return;
    }
    const admins = await listAdmins();
    json(res, 200, { admins });
    return;
  }

  if (req.method === "POST") {
    if (!(await ensureSuperAdmin(claims.username))) {
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
    const { username } = body;
    if (!username) {
      badRequest(res, "username is required");
      return;
    }
    const admins = await addAdmin(username);
    json(res, 201, { admins });
    return;
  }

  methodNotAllowed(res, ["GET", "POST"]);
}
