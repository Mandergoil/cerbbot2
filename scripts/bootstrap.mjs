import "dotenv/config";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { addAdmin, saveProduct } from "../lib/kv.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function seedProducts() {
  const file = path.join(__dirname, "../data/seed-products.json");
  if (!fs.existsSync(file)) {
    console.warn("No seed file found, skipping products");
    return;
  }
  const raw = fs.readFileSync(file, "utf-8");
  const items = JSON.parse(raw);
  for (const product of items) {
    await saveProduct(product);
    console.log(`✓ Seeded ${product.id}`);
  }
}

async function seedAdmins() {
  const { SUPER_ADMIN_USERNAME = "@Lapsus00" } = process.env;
  if (!SUPER_ADMIN_USERNAME) {
    console.warn("SUPER_ADMIN_USERNAME missing");
    return;
  }
  await addAdmin(SUPER_ADMIN_USERNAME);
  console.log(`✓ Ensured admin ${SUPER_ADMIN_USERNAME}`);
}

(async function main() {
  await seedAdmins();
  await seedProducts();
  console.log("Bootstrap complete");
})();
