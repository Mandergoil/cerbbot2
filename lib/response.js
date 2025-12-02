export function json(res, statusCode, payload) {
  res.statusCode = statusCode;
  res.setHeader("Content-Type", "application/json");
  res.end(JSON.stringify(payload));
}

export function methodNotAllowed(res, allowed) {
  res.setHeader("Allow", allowed.join(", "));
  json(res, 405, { error: "Method not allowed" });
}

export function unauthorized(res) {
  json(res, 401, { error: "Unauthorized" });
}

export function badRequest(res, message) {
  json(res, 400, { error: message });
}

export function notFound(res) {
  json(res, 404, { error: "Not found" });
}
