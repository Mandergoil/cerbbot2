import jwt from "jsonwebtoken";
import { listAdmins } from "./kv.js";

const { ADMIN_JWT_SECRET = "dev-secret", TOKEN_TTL_MINUTES = "30", SUPER_ADMIN_USERNAME = "@Lapsus00" } = process.env;
const ttl = parseInt(TOKEN_TTL_MINUTES, 10) || 30;

export function generateAdminToken(payload) {
  return jwt.sign(payload, ADMIN_JWT_SECRET, { expiresIn: `${ttl}m` });
}

export function verifyBearer(req) {
  const header = req.headers?.authorization || "";
  const [, token] = header.split(" ");
  if (!token) {
    return null;
  }
  try {
    return jwt.verify(token, ADMIN_JWT_SECRET);
  } catch (error) {
    return null;
  }
}

export async function ensureAdmin(username) {
  const admins = await listAdmins();
  return admins.includes(username);
}

export async function ensureSuperAdmin(username) {
  return username === SUPER_ADMIN_USERNAME;
}
