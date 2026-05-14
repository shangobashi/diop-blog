#!/usr/bin/env node
// check-no-unicode-escapes.js
// Prevents escaped Unicode sequences (like \u00e9) from appearing
// in human-facing content files as literal text.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const roots = ["static"];

// Matches literal \uXXXX (backslash + u + 4 hex chars)
// This is valid in JS strings but NOT in HTML text content.
// If it appears in .html files it will render as literal "\uXXXX".
const LITERAL_ESCAPE = /\\u[0-9a-fA-F]{4}/;
const DOUBLE_ESCAPE = /\\\\\\\\u[0-9a-fA-F]{4}/;

const failures = [];

function walk(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const full = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      walk(full);
      continue;
    }

    // Only check content/text files
    const ext = path.extname(entry.name).toLowerCase();
    if (![".html", ".js", ".json", ".md", ".mdx", ".tsx", ".jsx", ".ts", ".css"].includes(ext)) continue;

    try {
      const text = fs.readFileSync(full, "utf8");
      const lines = text.split("\n");

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];

        // Skip JS comments with intentional unicode examples
        if (line.trim().startsWith("// ") && LITERAL_ESCAPE.test(line)) continue;

        if (DOUBLE_ESCAPE.test(line) || LITERAL_ESCAPE.test(line)) {
          // For .js files, only flag double-escaped or non-string-literal usage
          // JS string literals with \uXXXX are valid and will be decoded by the engine
          if (ext === ".js" || ext === ".mjs" || ext === ".cjs") {
            // In JS, \uXXXX inside a string is valid - only flag double-escaped
            if (DOUBLE_ESCAPE.test(line)) {
              failures.push(`${full}:${i + 1}: double-escaped unicode escape`);
            }
          } else if (ext === ".html") {
            // In HTML, \uXXXX is ALWAYS literal text and will render as such
            failures.push(`${full}:${i + 1}: literal unicode escape sequence in HTML content`);
          } else if (ext === ".json") {
            // In JSON, \uXXXX is valid escape, but double-escapes are not
            if (DOUBLE_ESCAPE.test(line) || line.includes("\\\\u")) {
              failures.push(`${full}:${i + 1}: double-escaped unicode in JSON`);
            }
          } else {
            failures.push(`${full}:${i + 1}: literal unicode escape sequence`);
          }
        }
      }
    } catch (e) {
      // skip unreadable files
    }
  }
}

roots.forEach(dir => {
  const fullPath = path.join(root, dir);
  if (fs.existsSync(fullPath)) {
    console.log(`Checking ${dir}...`);
    walk(fullPath);
  }
});

if (failures.length) {
  console.error("\nVisible Unicode escape sequences found:");
  failures.forEach(f => console.error(`  ✗ ${f}`));
  console.error(`\n${failures.length} file(s) with escaped Unicode. Fix before deploying.`);
  process.exit(1);
}

console.log("No visible Unicode escape sequences found. i18n content is clean.");
