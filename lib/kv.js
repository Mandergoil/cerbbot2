import { kv } from "@vercel/kv";

const PRODUCT_KEY = "products";
const ADMIN_KEY = "admins";
const TOKEN_KEY = "admin-tokens";

export async function listProducts(category) {
  const ids = (await kv.smembers(PRODUCT_KEY)) || [];
  const entries = await Promise.all(
    ids.map(async (id) => ({ id, ...(await kv.hgetall(`${PRODUCT_KEY}:${id}`)) }))
  );
  const mapped = entries
    .filter((entry) => entry && Object.keys(entry).length)
    .map((entry) => ({
      id: entry.id,
      name: entry.name,
      category: entry.category,
      media: entry.media,
      description: entry.description,
      featured: entry.featured === "true"
    }));
  if (!category) {
    return mapped;
  }
  return mapped.filter((item) => item.category === category);
}

export async function getProduct(id) {
  if (!id) return null;
  const data = await kv.hgetall(`${PRODUCT_KEY}:${id}`);
  if (!data || !Object.keys(data).length) return null;
  return {
    id,
    name: data.name,
    category: data.category,
    media: data.media,
    description: data.description,
    featured: data.featured === "true"
  };
}

export async function saveProduct(product) {
  const { id, ...rest } = product;
  if (!id) {
    throw new Error("Product id is required");
  }
  await kv.sadd(PRODUCT_KEY, id);
  await kv.hset(`${PRODUCT_KEY}:${id}`, {
    ...rest,
    featured: rest.featured ? "true" : "false"
  });
  return getProduct(id);
}

export async function deleteProduct(id) {
  await kv.srem(PRODUCT_KEY, id);
  await kv.del(`${PRODUCT_KEY}:${id}`);
}

export async function listAdmins() {
  return (await kv.smembers(ADMIN_KEY)) || [];
}

export async function addAdmin(username) {
  await kv.sadd(ADMIN_KEY, username);
  return listAdmins();
}

export async function removeAdmin(username) {
  await kv.srem(ADMIN_KEY, username);
  return listAdmins();
}

export async function putToken(token, username, ttlSeconds) {
  await kv.set(`${TOKEN_KEY}:${token}`, username, { ex: ttlSeconds });
}

export async function consumeToken(token) {
  const key = `${TOKEN_KEY}:${token}`;
  const username = await kv.get(key);
  if (username) {
    await kv.del(key);
  }
  return username;
}
