const menuButton = document.querySelector(".menu-button");
const mobileMenu = document.querySelector(".mobile-menu");

function setMenu(open) {
  if (!menuButton || !mobileMenu) return;
  menuButton.setAttribute("aria-expanded", String(open));
  menuButton.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");
  mobileMenu.hidden = !open;
  document.body.classList.toggle("menu-open", open);
}

menuButton?.addEventListener("click", () => {
  setMenu(menuButton.getAttribute("aria-expanded") !== "true");
});

mobileMenu?.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => setMenu(false));
});

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape") setMenu(false);
});

window.addEventListener("resize", () => {
  if (window.innerWidth > 940) setMenu(false);
});

// Register the public, read-only catalog with browsers that expose WebMCP.
// The feature is progressive enhancement; ordinary browsers ignore it.
(() => {
  const models = [
    {
      name: "Qwen3.6 35B A3B — Abliterated",
      repository: "huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated",
      apiModelId: "mn/god",
      status: "deployed-currently-stopped",
      priceUsdPerHour: 5.45,
    },
    {
      name: "Ornith 1.0 35B — Abliterated",
      repository: "YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated",
      apiModelId: "mn/code",
      status: "deployed-currently-stopped",
      priceUsdPerHour: 5.45,
    },
    {
      name: "Qwythos 9B Claude Mythos 5 — Abliterated",
      repository: "huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated",
      apiModelId: "mn/fast",
      status: "deployed-currently-stopped",
      priceUsdPerHour: 2.34,
    },
    {
      name: "Ornith 1.0 397B W4A16 — Abliterated",
      repository: "cebeuq/Ornith-1.0-397B-abliterated-W4A16",
      apiModelId: "mn/ornith-397b",
      status: "planned-not-deployed",
      priceUsdPerHour: 10.9,
    },
  ];
  const registeredContexts = new WeakSet();

  function toolResult(value) {
    return {
      content: [{ type: "text", text: JSON.stringify(value, null, 2) }],
      structuredContent: value,
    };
  }

  const tools = [
    {
      name: "get_site_summary",
      description: "Explain ABLITERATED.cloud and its current private-beta status.",
      inputSchema: { type: "object", properties: {} },
      execute: async () => toolResult({
        name: "ABLITERATED.cloud",
        summary: "Token-protected, OpenAI-compatible managed access to exact abliterated Hugging Face models.",
        access: "Private beta through Signal",
        billingLive: false,
      }),
    },
    {
      name: "list_models",
      description: "List the four exact Hugging Face repositories, status and managed price.",
      inputSchema: { type: "object", properties: {} },
      execute: async () => toolResult({ models }),
    },
    {
      name: "read_public_documentation",
      description: "Read the complete public ABLITERATED.cloud documentation as text.",
      inputSchema: { type: "object", properties: {} },
      execute: async () => {
        const response = await fetch("llms-full.txt", { headers: { accept: "text/plain" } });
        const text = await response.text();
        return { content: [{ type: "text", text }], structuredContent: { text } };
      },
    },
  ];

  window.__webmcp_tools = tools;

  function registerTools() {
    const context = navigator.modelContext || document.modelContext || window.modelContext;
    if (!context || registeredContexts.has(context)) return Boolean(context);
    const registerTool = context.registerTool || context.register;
    if (typeof registerTool !== "function") return false;

    for (const tool of tools) {
      try {
        registerTool.call(context, tool);
      } catch (error) {
        const message = String(error?.message || error || "");
        if (!/already|duplicate|registered/i.test(message)) {
          console.warn("ABLITERATED.cloud WebMCP registration failed", tool.name, error);
        }
      }
    }
    registeredContexts.add(context);
    window.__abliteratedWebMcpRegistered = true;
    return true;
  }

  let attempts = 0;
  function registerWhenReady() {
    if (registerTools() || attempts >= 30) return;
    attempts += 1;
    window.setTimeout(registerWhenReady, 100);
  }

  registerWhenReady();
  document.addEventListener("DOMContentLoaded", registerWhenReady, { once: true });
  window.addEventListener("load", registerWhenReady, { once: true });
})();
