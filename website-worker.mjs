const CANONICAL_ORIGIN = "https://abliterated.cloud";

const CONTENT_TYPES = new Map([
  ["/index.md", "text/markdown; charset=utf-8"],
  ["/auth.md", "text/markdown; charset=utf-8"],
  ["/.well-known/api-catalog", "application/linkset+json; charset=utf-8"],
  ["/.well-known/openid-configuration", "application/json; charset=utf-8"],
  ["/.well-known/oauth-authorization-server", "application/json; charset=utf-8"],
  ["/.well-known/oauth-protected-resource", "application/json; charset=utf-8"],
  ["/.well-known/http-message-signatures-directory", "application/json; charset=utf-8"],
  ["/.well-known/http-message-signature-directory", "application/json; charset=utf-8"],
  ["/.well-known/agent.json", "application/json; charset=utf-8"],
  ["/.well-known/agent-card.json", "application/json; charset=utf-8"],
  ["/.well-known/webmcp.json", "application/json; charset=utf-8"],
  ["/openapi.json", "application/json; charset=utf-8"],
  ["/manifest.webmanifest", "application/manifest+json; charset=utf-8"],
]);

const DISCOVERY_LINKS = [
  '</llms.txt>; rel="alternate"; type="text/markdown"',
  '</llms-full.txt>; rel="alternate"; type="text/plain"',
  '</auth.md>; rel="service-desc"; type="text/markdown"',
  '</sitemap.xml>; rel="sitemap"; type="application/xml"',
  '</openapi.json>; rel="service-desc"; type="application/json"',
  '</.well-known/api-catalog>; rel="api-catalog"; type="application/linkset+json"',
  '</.well-known/mcp/server-card.json>; rel="describedby"; type="application/json"',
  '</.well-known/agent-card.json>; rel="describedby"; type="application/json"',
  '</.well-known/agent-skills/index.json>; rel="service-desc"; type="application/json"',
  '</.well-known/webmcp.json>; rel="service-desc"; type="application/json"',
].join(", ");

function siteOrigin(request, env) {
  if (env.SITE_ENV === "production") return env.SITE_ORIGIN || CANONICAL_ORIGIN;
  return new URL(request.url).origin;
}

function commonHeaders(contentType, pathname) {
  const headers = new Headers({
    "content-type": contentType,
    "content-signal": "ai-train=no, search=yes, ai-input=yes",
    link: DISCOVERY_LINKS,
    vary: "Accept",
    "x-content-type-options": "nosniff",
    "referrer-policy": "strict-origin-when-cross-origin",
  });

  if (pathname.startsWith("/.well-known/") || pathname.startsWith("/oauth/") || ["/auth.md", "/llms.txt", "/llms-full.txt", "/openapi.json"].includes(pathname)) {
    headers.set("access-control-allow-origin", "*");
    headers.set("access-control-allow-methods", "GET, HEAD, OPTIONS, POST");
    headers.set("access-control-allow-headers", "Content-Type, Authorization");
  }

  return headers;
}

function jsonResponse(value, status, pathname) {
  return new Response(JSON.stringify(value, null, 2), {
    status,
    headers: commonHeaders("application/json; charset=utf-8", pathname),
  });
}

function replaceOrigin(text, origin) {
  return text
    .replaceAll(CANONICAL_ORIGIN, origin)
    .replaceAll("https://eminogrande.github.io/mn-uncensored", origin);
}

async function assetResponse(request, env, pathname, origin) {
  const assetUrl = new URL(request.url);
  assetUrl.pathname = pathname;
  const asset = await env.ASSETS.fetch(new Request(assetUrl, request));
  if (!asset.ok) return asset;

  const contentType = CONTENT_TYPES.get(pathname) || asset.headers.get("content-type") || "application/octet-stream";
  const headers = new Headers(asset.headers);
  for (const [name, value] of commonHeaders(contentType, pathname)) headers.set(name, value);

  const isControlledTextAsset = contentType.startsWith("text/") || contentType.includes("json") || contentType.includes("xml");
  if (!isControlledTextAsset) return new Response(asset.body, { status: asset.status, headers });

  // These are small, repository-owned static files; rewriting keeps preview and
  // production discovery documents on the origin that served the request.
  const text = replaceOrigin(await asset.text(), origin);
  headers.delete("content-length");
  headers.delete("etag");
  return new Response(text, { status: asset.status, headers });
}

function mcpResponse(payload, origin) {
  if (payload?.method === "initialize") {
    return {
      jsonrpc: "2.0",
      id: payload.id ?? null,
      result: {
        protocolVersion: payload.params?.protocolVersion || "2025-11-05",
        capabilities: { tools: {}, resources: {} },
        serverInfo: { name: "ABLITERATED.cloud Public Site MCP", version: "1.0.0" },
      },
    };
  }

  if (payload?.method === "tools/list") {
    return {
      jsonrpc: "2.0",
      id: payload.id ?? null,
      result: {
        tools: [
          {
            name: "get_site_summary",
            description: "Explain ABLITERATED.cloud, its current beta status and access model.",
            inputSchema: { type: "object", properties: {} },
          },
          {
            name: "list_models",
            description: "List the four exact Hugging Face repositories, availability and managed prices.",
            inputSchema: { type: "object", properties: {} },
          },
        ],
      },
    };
  }

  if (payload?.method === "tools/call" && payload.params?.name === "get_site_summary") {
    return {
      jsonrpc: "2.0",
      id: payload.id ?? null,
      result: {
        content: [{ type: "text", text: `ABLITERATED.cloud provides token-protected, OpenAI-compatible access to exact abliterated Hugging Face models. Documentation: ${origin}/llms-full.txt` }],
      },
    };
  }

  if (payload?.method === "tools/call" && payload.params?.name === "list_models") {
    return {
      jsonrpc: "2.0",
      id: payload.id ?? null,
      result: {
        content: [{ type: "text", text: `Read the exact model catalog at ${origin}/openapi.json or ${origin}/llms-full.txt.` }],
      },
    };
  }

  return { jsonrpc: "2.0", id: payload?.id ?? null, error: { code: -32601, message: "Method not found" } };
}

async function handleMcp(request, origin) {
  if (request.method !== "POST") return jsonResponse({ error: "Use POST" }, 405, "/mcp");
  let payload;
  try {
    payload = await request.json();
  } catch {
    return jsonResponse({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "Parse error" } }, 400, "/mcp");
  }
  return jsonResponse(mcpResponse(payload, origin), 200, "/mcp");
}

function handleAgentAuth(request) {
  if (request.method !== "POST") return jsonResponse({ error: "Use POST" }, 405, "/agent/auth");
  return jsonResponse({
    registration_id: "abliterated_public_site",
    registration_type: "anonymous",
    credential_type: "access_token",
    credential: "abliterated_public_site_readonly",
    credential_expires: null,
    scopes: ["public:read"],
    note: "This credential reads public website metadata only. It does not authorize model inference.",
  }, 200, "/agent/auth");
}

function oauthJsonResponse(value, status, pathname) {
  const headers = commonHeaders("application/json; charset=utf-8", pathname);
  headers.set("cache-control", "no-store");
  headers.set("pragma", "no-cache");
  return new Response(JSON.stringify(value, null, 2), { status, headers });
}

async function handleOAuthToken(request) {
  if (request.method !== "POST") return oauthJsonResponse({ error: "invalid_request", error_description: "Use POST" }, 405, "/oauth/token");

  let values;
  try {
    if ((request.headers.get("content-type") || "").includes("application/json")) {
      values = await request.json();
    } else {
      values = Object.fromEntries(new URLSearchParams(await request.text()));
    }
  } catch {
    return oauthJsonResponse({ error: "invalid_request", error_description: "The request body could not be parsed" }, 400, "/oauth/token");
  }

  if (values?.grant_type !== "client_credentials") {
    return oauthJsonResponse({ error: "unsupported_grant_type" }, 400, "/oauth/token");
  }
  if (values.scope && values.scope !== "public:read") {
    return oauthJsonResponse({ error: "invalid_scope", scope: "public:read" }, 400, "/oauth/token");
  }

  return oauthJsonResponse({
    access_token: "abliterated_public_site_readonly",
    token_type: "Bearer",
    scope: "public:read",
  }, 200, "/oauth/token");
}

function handleOAuthRegistration(request) {
  if (request.method !== "POST") return oauthJsonResponse({ error: "invalid_client_metadata", error_description: "Use POST" }, 405, "/oauth/register");
  return oauthJsonResponse({
    client_id: "abliterated_public_site",
    client_id_issued_at: 1784325600,
    grant_types: ["client_credentials"],
    token_endpoint_auth_method: "none",
    scope: "public:read",
  }, 201, "/oauth/register");
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const pathname = url.pathname || "/";
    const routePath = pathname.replace(/\/+$/, "") || "/";
    const origin = siteOrigin(request, env);

    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: commonHeaders("text/plain; charset=utf-8", routePath) });

    if (routePath === "/" && (request.headers.get("accept") || "").includes("text/markdown")) {
      return assetResponse(request, env, "/index.md", origin);
    }

    if (routePath === "/mcp") return handleMcp(request, origin);
    if (routePath === "/agent/auth") return handleAgentAuth(request);
    if (routePath === "/a2a") return jsonResponse({ name: "ABLITERATED.cloud Public Site Agent", status: "ready", card: `${origin}/.well-known/agent-card.json` }, 200, routePath);
    if (routePath === "/oauth/token") return handleOAuthToken(request);
    if (routePath === "/oauth/register") return handleOAuthRegistration(request);

    // Keep the incoming trailing slash for directory indexes. Workers Static
    // Assets treats `/blog/` as canonical and would redirect `/blog` back to it.
    return assetResponse(request, env, pathname, origin);
  },
};
