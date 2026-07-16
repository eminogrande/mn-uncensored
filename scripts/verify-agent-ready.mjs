const args = process.argv.slice(2);
const localOnly = args.includes("--local-only");
const allowPagesDevDnsGap = args.includes("--allow-pages-dev-dns-gap");
const target = args.find((arg) => !arg.startsWith("--")) || "http://localhost:8788";

const requiredScanChecks = [
  ["discoverability", "robotsTxt"],
  ["discoverability", "sitemap"],
  ["discoverability", "linkHeaders"],
  ["discoverability", "dnsAid"],
  ["contentAccessibility", "markdownNegotiation"],
  ["botAccessControl", "robotsTxtAiRules"],
  ["botAccessControl", "contentSignals"],
  ["botAccessControl", "webBotAuth"],
  ["discovery", "apiCatalog"],
  ["discovery", "oauthDiscovery"],
  ["discovery", "oauthProtectedResource"],
  ["discovery", "authMd"],
  ["discovery", "mcpServerCard"],
  ["discovery", "a2aAgentCard"],
  ["discovery", "agentSkills"],
  ["discovery", "webMcp"],
];

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function contentType(response) {
  return (response.headers.get("content-type") || "").toLowerCase();
}

async function getJson(path, init) {
  const response = await fetch(new URL(path, target), init);
  const text = await response.text();
  let json;
  try { json = JSON.parse(text); } catch { json = null; }
  return { response, text, json };
}

async function verifyLocal() {
  console.log(`Verifying agent surfaces at ${target}`);

  const home = await fetch(target);
  assert(home.ok, "Homepage did not return 200");
  const links = home.headers.get("link") || "";
  for (const required of ["/llms.txt", "/auth.md", "/.well-known/api-catalog", "/.well-known/agent-card.json"]) {
    assert(links.includes(required), `Homepage Link header is missing ${required}`);
  }
  assert(home.headers.get("content-signal")?.includes("search=yes"), "Homepage Content-Signal header is missing");

  const markdown = await fetch(target, { headers: { accept: "text/markdown" } });
  assert(markdown.ok && contentType(markdown).includes("text/markdown"), "Markdown negotiation failed");

  for (const [path, expectedType] of [
    ["/index.md", "text/markdown"],
    ["/auth.md", "text/markdown"],
    ["/.well-known/api-catalog", "application/linkset+json"],
    ["/.well-known/openid-configuration", "application/json"],
    ["/.well-known/oauth-authorization-server", "application/json"],
    ["/.well-known/oauth-protected-resource", "application/json"],
    ["/.well-known/mcp/server-card.json", "application/json"],
    ["/.well-known/agent-card.json", "application/json"],
    ["/.well-known/agent-skills/index.json", "application/json"],
    ["/.well-known/webmcp.json", "application/json"],
    ["/.well-known/http-message-signatures-directory", "application/json"],
    ["/openapi.json", "application/json"],
  ]) {
    const response = await fetch(new URL(path, target));
    assert(response.ok, `${path} did not return 200`);
    assert(contentType(response).includes(expectedType), `${path} returned ${contentType(response)}, expected ${expectedType}`);
  }

  const robots = await fetch(new URL("/robots.txt", target));
  const robotsText = await robots.text();
  assert(robotsText.includes("Content-Signal:"), "robots.txt is missing Content-Signal");
  assert(robotsText.includes("Sitemap:"), "robots.txt is missing Sitemap");
  assert(robotsText.includes("GPTBot"), "robots.txt is missing AI crawler rules");

  const openApi = await getJson("/openapi.json");
  assert(openApi.json?.["x-model-catalog"]?.length === 4, "OpenAPI catalog must contain four models");
  for (const model of [
    "huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated",
    "YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated",
    "huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated",
    "cebeuq/Ornith-1.0-397B-abliterated-W4A16",
  ]) {
    assert(openApi.text.includes(model), `OpenAPI is missing ${model}`);
  }

  const agentCard = await getJson("/.well-known/agent-card.json");
  assert(agentCard.json?.supportedInterfaces?.length > 0, "Agent card has no supported interface");
  const mcpCard = await getJson("/.well-known/mcp/server-card.json");
  assert(mcpCard.json?.transport?.url, "MCP server card has no transport URL");
  const oauth = await getJson("/.well-known/oauth-authorization-server");
  assert(oauth.json?.agent_auth?.skill?.endsWith("/auth.md"), "OAuth discovery has no agent auth skill");
  const skillIndex = await getJson("/.well-known/agent-skills/index.json");
  assert(skillIndex.json?.skills?.length > 0, "Agent skill index is empty");

  const initialize = await getJson("/mcp", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2025-11-05" } }),
  });
  assert(initialize.json?.result?.serverInfo?.name, "MCP initialize failed");

  const tools = await getJson("/mcp", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ jsonrpc: "2.0", id: 2, method: "tools/list" }),
  });
  assert(tools.json?.result?.tools?.some((tool) => tool.name === "list_models"), "MCP list_models tool is missing");

  console.log("Local agent-readiness checks passed.");
}

async function verifyPublicScan() {
  const scan = await fetch("https://isitagentready.com/api/scan", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ url: target }),
  });
  const payload = await scan.json();
  assert(scan.ok, `isitagentready scan failed with HTTP ${scan.status}`);
  assert(!payload.siteError, `isitagentready site error: ${payload.siteError?.httpStatus || "unknown"}`);

  const pagesDev = new URL(target).hostname.endsWith(".pages.dev") || new URL(target).hostname.endsWith(".workers.dev");
  for (const [group, key] of requiredScanChecks) {
    const status = payload.checks?.[group]?.[key]?.status;
    if (allowPagesDevDnsGap && pagesDev && group === "discoverability" && key === "dnsAid" && status === "fail") continue;
    assert(status === "pass", `${group}.${key} is ${status || "missing"}`);
  }

  console.log(`isitagentready score: ${payload.score ?? payload.overallScore ?? "not reported"}`);
  console.log("Public agent-readiness scan passed.");
}

try {
  await verifyLocal();
  if (!localOnly) await verifyPublicScan();
} catch (error) {
  console.error(`Verification failed: ${error.message}`);
  process.exit(1);
}
