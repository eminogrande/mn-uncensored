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

// A lightweight, dependency-free point-cloud brain for the hero. It pauses
// outside the viewport, caps pixel density, and becomes static when reduced
// motion is requested.
(() => {
  const canvas = document.querySelector("#brain-canvas");
  const stage = canvas?.closest(".brain-stage");
  const context = canvas?.getContext("2d");
  if (!canvas || !stage || !context) return;

  let seed = 397;
  const random = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296;
  };

  const lobes = [
    [-0.62, 0.1, 0, 0.57, 0.55, 0.48],
    [-0.18, 0.31, 0, 0.66, 0.55, 0.51],
    [0.39, 0.25, 0, 0.68, 0.53, 0.49],
    [0.7, -0.06, 0, 0.46, 0.43, 0.4],
    [0.17, -0.27, 0, 0.66, 0.47, 0.46],
    [-0.58, -0.31, 0, 0.39, 0.34, 0.36],
    [-0.02, -0.55, 0, 0.28, 0.3, 0.27],
    [0.03, -0.76, 0, 0.16, 0.25, 0.16],
  ];

  function lobeDistance(x, y, z, scale = 1) {
    let nearest = Infinity;
    for (const [cx, cy, cz, rx, ry, rz] of lobes) {
      const value = ((x - cx) / (rx * scale)) ** 2
        + ((y - cy) / (ry * scale)) ** 2
        + ((z - cz) / (rz * scale)) ** 2;
      nearest = Math.min(nearest, value);
    }
    return nearest;
  }

  const points = [];
  let attempts = 0;
  while (points.length < 300 && attempts < 30000) {
    attempts += 1;
    const x = random() * 2.55 - 1.2;
    const y = random() * 1.8 - 0.88;
    const z = random() * 1.1 - 0.55;
    const distance = lobeDistance(x, y, z);
    if (distance <= 1 && (distance >= 0.47 || random() < 0.17)) {
      points.push({ x, y, z, size: 0.65 + random() * 1.35, accent: random() > 0.91 });
    }
  }

  const edges = [];
  const degree = new Uint8Array(points.length);
  for (let i = 0; i < points.length; i += 1) {
    const candidates = [];
    for (let j = i + 1; j < points.length; j += 1) {
      const dx = points[i].x - points[j].x;
      const dy = points[i].y - points[j].y;
      const dz = points[i].z - points[j].z;
      const distance = Math.hypot(dx, dy, dz);
      if (distance < 0.3) candidates.push([distance, j]);
    }
    candidates.sort((a, b) => a[0] - b[0]);
    for (const [, j] of candidates) {
      if (degree[i] >= 3) break;
      if (degree[j] >= 3) continue;
      edges.push([i, j]);
      degree[i] += 1;
      degree[j] += 1;
    }
  }

  let width = 0;
  let height = 0;
  let frame = 0;
  let visible = true;
  let lastPaint = 0;
  const motionQuery = window.matchMedia
    ? window.matchMedia("(prefers-reduced-motion: reduce)")
    : { matches: false };

  function resize() {
    const bounds = stage.getBoundingClientRect();
    width = Math.max(1, Math.round(bounds.width));
    height = Math.max(1, Math.round(bounds.height));
    const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * pixelRatio);
    canvas.height = Math.round(height * pixelRatio);
    context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    paint(performance.now(), true);
  }

  function project(point, time) {
    const rotation = motionQuery.matches ? -0.18 : Math.sin(time * 0.00012) * 0.2 - 0.12;
    const tilt = -0.06;
    const cos = Math.cos(rotation);
    const sin = Math.sin(rotation);
    const x = point.x * cos - point.z * sin;
    const depth = point.x * sin + point.z * cos;
    const y = point.y * Math.cos(tilt) - depth * Math.sin(tilt);
    const z = point.y * Math.sin(tilt) + depth * Math.cos(tilt);
    const scale = Math.min(width / 3.15, height / 1.72);
    const perspective = 1 + z * 0.12;
    return {
      x: width * 0.5 + x * scale * perspective,
      y: height * 0.48 + y * scale * perspective,
      z,
      size: point.size * (0.75 + (z + 0.55) * 0.5),
      accent: point.accent,
    };
  }

  function paint(time, force = false) {
    if (!force && time - lastPaint < 32) {
      frame = requestAnimationFrame(paint);
      return;
    }
    lastPaint = time;
    context.clearRect(0, 0, width, height);
    const projected = points.map((point) => project(point, time));

    context.lineWidth = 0.65;
    for (const [fromIndex, toIndex] of edges) {
      const from = projected[fromIndex];
      const to = projected[toIndex];
      const opacity = Math.max(0.07, Math.min(0.25, 0.12 + (from.z + to.z) * 0.08));
      context.strokeStyle = `rgba(67, 72, 82, ${opacity})`;
      context.beginPath();
      context.moveTo(from.x, from.y);
      context.lineTo(to.x, to.y);
      context.stroke();
    }

    projected.sort((a, b) => a.z - b.z);
    for (const point of projected) {
      const opacity = Math.max(0.3, Math.min(0.88, 0.48 + point.z * 0.5));
      context.fillStyle = point.accent
        ? `rgba(36, 88, 211, ${opacity})`
        : `rgba(20, 22, 27, ${opacity})`;
      context.beginPath();
      context.arc(point.x, point.y, point.size, 0, Math.PI * 2);
      context.fill();
    }

    if (!motionQuery.matches && visible && !document.hidden) {
      frame = requestAnimationFrame(paint);
    }
  }

  function updateAnimation() {
    cancelAnimationFrame(frame);
    frame = 0;
    if (visible && !document.hidden && !motionQuery.matches) {
      frame = requestAnimationFrame(paint);
    } else {
      paint(performance.now(), true);
    }
  }

  if ("ResizeObserver" in window) {
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(stage);
  } else {
    window.addEventListener("resize", resize, { passive: true });
  }

  if ("IntersectionObserver" in window) {
    const intersectionObserver = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      updateAnimation();
    }, { rootMargin: "80px" });
    intersectionObserver.observe(stage);
  } else {
    updateAnimation();
  }

  document.addEventListener("visibilitychange", updateAnimation);
  motionQuery.addEventListener?.("change", updateAnimation);
  resize();
})();

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
