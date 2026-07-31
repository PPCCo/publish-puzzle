#!/usr/bin/env node
// Tier-3 headless-browser fetch helper for the quarantined research fetcher.
//
// Contract with publishing_house/net/fetch.py::render():
//   argv[2] = URL to render (host allowlisting is enforced on the Python side).
//   On success: print a single JSON object {status, final_url, body} to stdout,
//   exit 0.
//   If Playwright is not installed: print an identifiable message to stderr and
//   exit non-zero so render() degrades to the manual tier instead of failing hard.
//
// GET-only navigation, no credentials, no cookies persisted. This helper never
// logs in or submits forms — it only renders a page the fetcher was allowed to GET.

const url = process.argv[2];
if (!url) {
  process.stderr.write("usage: browser_fetch.mjs <url>\n");
  process.exit(2);
}

let chromium;
try {
  ({ chromium } = await import("playwright"));
} catch (err) {
  // Distinct, greppable signal: render() treats this as browser-unavailable.
  process.stderr.write("playwright not installed: Cannot find package 'playwright'\n");
  process.exit(3);
}

let browser;
try {
  browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent:
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " +
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
  });
  const page = await context.newPage();
  const response = await page.goto(url, { waitUntil: "domcontentloaded", timeout: 40000 });
  const body = await page.content();
  const out = {
    status: response ? response.status() : 0,
    final_url: page.url(),
    body: body.slice(0, 4 * 1024 * 1024),
  };
  process.stdout.write(JSON.stringify(out));
  await browser.close();
  process.exit(0);
} catch (err) {
  if (browser) {
    try { await browser.close(); } catch (_) { /* ignore */ }
  }
  process.stderr.write("render failed: " + (err && err.message ? err.message : String(err)) + "\n");
  process.exit(1);
}
