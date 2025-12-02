import { parseJsonBody } from "../lib/body.js";
import { json, methodNotAllowed, unauthorized, badRequest } from "../lib/response.js";
import { verifyBearer, ensureAdmin, ensureSuperAdmin, generateAdminToken } from "../lib/auth.js";
import { putToken, consumeToken } from "../lib/kv.js";
import { customAlphabet } from "nanoid";

const nanoid = customAlphabet("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", 12);
const ttlMinutes = parseInt(process.env.TOKEN_TTL_MINUTES || "30", 10);
const staticPassword = process.env.ADMIN_STATIC_PASSWORD || "history2552@#";
const defaultAdmin = process.env.SUPER_ADMIN_USERNAME || "@Lapsus00";

export default async function handler(req, res) {
  if (req.method === "GET") {
    const claims = verifyBearer(req);
    if (!claims) {
      unauthorized(res);
      return;
    }
    json(res, 200, { user: claims });
    return;
  }

  if (req.method !== "POST") {
    methodNotAllowed(res, ["GET", "POST"]);
    return;
  }

  let body;
  try {
    body = await parseJsonBody(req);
  } catch (error) {
    badRequest(res, error.message);
    return;
  }
  const { intent = "exchange", username, token, password } = body;

  if (intent === "password") {
    if (!password || password !== staticPassword) {
      unauthorized(res);
      return;
    }
    const jwtToken = generateAdminToken({ username: defaultAdmin });
    json(res, 200, { bearer: jwtToken, expiresInMinutes: ttlMinutes });
    return;
  }

  if (intent === "create") {
  const claims = verifyBearer(req);
  if (!claims || !(await ensureSuperAdmin(claims.username))) {
      unauthorized(res);
      return;
    }
    if (!username) {
      badRequest(res, "username is required");
      return;
    }
    const magic = nanoid();
    await putToken(magic, username, ttlMinutes * 60);
    json(res, 201, { token: magic, expiresInMinutes: ttlMinutes });
    return;
  }

  if (intent === "exchange") {
    if (!token) {
      badRequest(res, "token is required");
      return;
    }
    const owner = await consumeToken(token);
    if (!owner || !(await ensureAdmin(owner))) {
      unauthorized(res);
      return;
    }
    const jwtToken = generateAdminToken({ username: owner });
    json(res, 200, { bearer: jwtToken, expiresInMinutes: ttlMinutes });
    return;
  }

  if (intent === "impersonate") {
    const claims = verifyBearer(req);
    if (!claims || !(await ensureSuperAdmin(claims.username))) {
      unauthorized(res);
      return;
    }
    if (!username) {
      badRequest(res, "username is required");
      return;
    }
    if (!(await ensureAdmin(username))) {
      unauthorized(res);
      return;
    }
    const jwtToken = generateAdminToken({ username });
    json(res, 200, { bearer: jwtToken, expiresInMinutes: ttlMinutes });
    return;
  }

  badRequest(res, "unsupported intent");
}
