import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const webRoot = path.resolve(__dirname, "..");
const nextDir = path.join(webRoot, ".next");
const chunksDir = path.join(nextDir, "static", "chunks");

// Configured budgets
const BUDGETS = {
  maxSingleJsChunkGzipKb: 150,
  maxRootMainJsGzipKb: 250,
  maxTotalCssGzipKb: 60,
};

function getGzipSize(buffer) {
  return zlib.gzipSync(buffer).length;
}

function formatKb(bytes) {
  return (bytes / 1024).toFixed(2) + " KB";
}

function checkBudgets() {
  if (!fs.existsSync(chunksDir)) {
    console.error(`❌ Error: Chunks directory not found at ${chunksDir}. Did you run 'npm run build'?`);
    process.exit(1);
  }

  const manifestPath = path.join(nextDir, "build-manifest.json");
  let rootMainFiles = [];
  if (fs.existsSync(manifestPath)) {
    try {
      const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf-8"));
      rootMainFiles = [...(manifest.rootMainFiles || []), ...(manifest.polyfillFiles || [])];
    } catch {
      // Fallback
    }
  }

  const files = fs.readdirSync(chunksDir);
  let hasFailure = false;
  let totalRootMainGzipBytes = 0;
  let totalCssGzipBytes = 0;

  console.log("\n📦 Bundle Budget Check:\n");
  console.log("--------------------------------------------------------------------------------");
  console.log(
    `${"Asset".padEnd(40)} ${"Raw Size".padStart(15)} ${"Gzip Size".padStart(15)} ${"Status".padStart(8)}`
  );
  console.log("--------------------------------------------------------------------------------");

  for (const file of files) {
    const filePath = path.join(chunksDir, file);
    const stat = fs.statSync(filePath);
    if (!stat.isFile()) continue;

    const content = fs.readFileSync(filePath);
    const rawBytes = content.length;
    const gzipBytes = getGzipSize(content);
    const isJs = file.endsWith(".js");
    const isCss = file.endsWith(".css");

    let status = "✅ PASS";

    if (isJs) {
      if (gzipBytes > BUDGETS.maxSingleJsChunkGzipKb * 1024) {
        status = "❌ FAIL";
        hasFailure = true;
      }
      const relToStatic = `static/chunks/${file}`;
      if (rootMainFiles.includes(relToStatic)) {
        totalRootMainGzipBytes += gzipBytes;
      }
    } else if (isCss) {
      totalCssGzipBytes += gzipBytes;
      if (gzipBytes > BUDGETS.maxTotalCssGzipKb * 1024) {
        status = "❌ FAIL";
        hasFailure = true;
      }
    }

    console.log(
      `${file.slice(0, 38).padEnd(40)} ${formatKb(rawBytes).padStart(15)} ${formatKb(gzipBytes).padStart(15)} ${status.padStart(8)}`
    );
  }

  console.log("--------------------------------------------------------------------------------");
  console.log(`\n📊 Budget Summaries:`);

  const rootMainStatus = totalRootMainGzipBytes <= BUDGETS.maxRootMainJsGzipKb * 1024 ? "✅ PASS" : "❌ FAIL";
  if (totalRootMainGzipBytes > BUDGETS.maxRootMainJsGzipKb * 1024) hasFailure = true;
  console.log(
    `  • Root Main JS (gzipped): ${formatKb(totalRootMainGzipBytes)} / budget: ${BUDGETS.maxRootMainJsGzipKb} KB -> ${rootMainStatus}`
  );

  const cssStatus = totalCssGzipBytes <= BUDGETS.maxTotalCssGzipKb * 1024 ? "✅ PASS" : "❌ FAIL";
  if (totalCssGzipBytes > BUDGETS.maxTotalCssGzipKb * 1024) hasFailure = true;
  console.log(
    `  • Total CSS (gzipped):     ${formatKb(totalCssGzipBytes)} / budget: ${BUDGETS.maxTotalCssGzipKb} KB -> ${cssStatus}`
  );

  console.log(
    `  • Max single JS chunk:    budget: ${BUDGETS.maxSingleJsChunkGzipKb} KB`
  );

  if (hasFailure) {
    console.error("\n❌ Bundle budget exceeded! See above for offending assets.\n");
    process.exit(1);
  }

  console.log("\n✅ All bundle budget checks passed!\n");
}

checkBudgets();
