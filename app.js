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

  // A lateral brain outline: cerebrum across the top, cerebellum at the
  // lower-left, and a small stem descending near the center-right.
  const outlineControls = [
    [-1.08, 0.05], [-1.05, -0.27], [-0.88, -0.55], [-0.58, -0.73],
    [-0.23, -0.82], [0.16, -0.81], [0.52, -0.69], [0.81, -0.48],
    [0.99, -0.2], [1.02, 0.05], [0.9, 0.28], [0.69, 0.43],
    [0.47, 0.48], [0.34, 0.59], [0.29, 0.83], [0.12, 0.97],
    [-0.02, 0.71], [-0.18, 0.58], [-0.44, 0.61], [-0.7, 0.52],
    [-0.92, 0.34], [-1.05, 0.18],
  ];

  function catmullRom(p0, p1, p2, p3, t) {
    const t2 = t * t;
    const t3 = t2 * t;
    return [0, 1].map((axis) => 0.5 * (
      (2 * p1[axis])
      + (-p0[axis] + p2[axis]) * t
      + (2 * p0[axis] - 5 * p1[axis] + 4 * p2[axis] - p3[axis]) * t2
      + (-p0[axis] + 3 * p1[axis] - 3 * p2[axis] + p3[axis]) * t3
    ));
  }

  const outline = [];
  for (let index = 0; index < outlineControls.length; index += 1) {
    const count = outlineControls.length;
    const p0 = outlineControls[(index - 1 + count) % count];
    const p1 = outlineControls[index];
    const p2 = outlineControls[(index + 1) % count];
    const p3 = outlineControls[(index + 2) % count];
    for (let step = 0; step < 4; step += 1) {
      outline.push(catmullRom(p0, p1, p2, p3, step / 4));
    }
  }

  function insideOutline(x, y) {
    let inside = false;
    for (let i = 0, j = outline.length - 1; i < outline.length; j = i, i += 1) {
      const [xi, yi] = outline[i];
      const [xj, yj] = outline[j];
      const intersects = ((yi > y) !== (yj > y))
        && (x < ((xj - xi) * (y - yi)) / (yj - yi) + xi);
      if (intersects) inside = !inside;
    }
    return inside;
  }

  function zoneFor(x, y) {
    if (x > 0.48) return 0;
    if (y < -0.34) return 1;
    if (x < -0.48 && y > 0.08) return 2;
    if (y > 0.34) return 3;
    return 4;
  }

  const points = [];
  const edges = [];

  function addPoint(x, y, z, options = {}) {
    points.push({
      x,
      y,
      z,
      size: options.size ?? 0.65 + random() * 1.3,
      accent: options.accent ?? random() > 0.94,
      contour: Boolean(options.contour),
      zone: zoneFor(x, y),
    });
    return points.length - 1;
  }

  const contourIndexes = outline.map(([x, y]) => addPoint(
    x,
    y,
    (random() - 0.5) * 0.08,
    { contour: true, size: 1.05 + random() * 0.55 },
  ));
  contourIndexes.forEach((pointIndex, index) => {
    edges.push([pointIndex, contourIndexes[(index + 1) % contourIndexes.length], true]);
  });

  let attempts = 0;
  while (points.length < 420 && attempts < 30000) {
    attempts += 1;
    const x = random() * 2.2 - 1.1;
    const y = random() * 1.84 - 0.84;
    if (insideOutline(x, y)) {
      addPoint(x, y, random() * 0.62 - 0.31);
    }
  }

  const degree = new Uint8Array(points.length);
  for (const [from, to] of edges) {
    degree[from] += 1;
    degree[to] += 1;
  }
  for (let i = 0; i < points.length; i += 1) {
    const candidates = [];
    for (let j = i + 1; j < points.length; j += 1) {
      const dx = points[i].x - points[j].x;
      const dy = points[i].y - points[j].y;
      const dz = points[i].z - points[j].z;
      const distance = Math.hypot(dx, dy, dz);
      if (distance < 0.23) candidates.push([distance, j]);
    }
    candidates.sort((a, b) => a[0] - b[0]);
    for (const [, j] of candidates) {
      if (degree[i] >= 4) break;
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
  const pointer = { active: false, x: 0, y: 0 };
  const neon = [
    [255, 43, 214],
    [0, 229, 255],
    [157, 255, 0],
    [255, 122, 0],
    [123, 97, 255],
  ];
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
    const rotation = motionQuery.matches ? 0 : Math.sin(time * 0.00016) * 0.055;
    const xScale = Math.min(width / 2.48, 470);
    const yScale = height / 2.12;
    const depth = point.z + point.x * rotation;
    const x = width * 0.5 + (point.x + point.z * rotation) * xScale;
    const y = height * 0.44 + (point.y + point.z * 0.035) * yScale;
    const radius = Math.max(92, Math.min(165, width * 0.145));
    const hoverDistance = Math.hypot(x - pointer.x, y - pointer.y);
    const glow = pointer.active ? Math.max(0, 1 - hoverDistance / radius) ** 1.7 : 0;
    return {
      x,
      y,
      z: depth,
      size: point.size * (0.9 + (depth + 0.35) * 0.35),
      accent: point.accent,
      contour: point.contour,
      glow,
      zone: point.zone,
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

    context.shadowBlur = 0;
    context.lineWidth = 0.7;
    for (const [fromIndex, toIndex, contourEdge] of edges) {
      const from = projected[fromIndex];
      const to = projected[toIndex];
      const opacity = contourEdge
        ? 0.32
        : Math.max(0.08, Math.min(0.3, 0.15 + (from.z + to.z) * 0.08));
      context.lineWidth = contourEdge ? 1 : 0.7;
      context.strokeStyle = `rgba(67, 72, 82, ${opacity})`;
      context.beginPath();
      context.moveTo(from.x, from.y);
      context.lineTo(to.x, to.y);
      context.stroke();
    }

    // Redraw only the activated local network with a neon halo.
    for (const [fromIndex, toIndex] of edges) {
      const from = projected[fromIndex];
      const to = projected[toIndex];
      const glow = Math.max(from.glow, to.glow);
      if (glow < 0.02) continue;
      const source = from.glow >= to.glow ? from : to;
      const [red, green, blue] = neon[source.zone];
      context.lineWidth = 0.8 + glow * 2.2;
      context.shadowBlur = 5 + glow * 16;
      context.shadowColor = `rgb(${red}, ${green}, ${blue})`;
      context.strokeStyle = `rgba(${red}, ${green}, ${blue}, ${0.2 + glow * 0.78})`;
      context.beginPath();
      context.moveTo(from.x, from.y);
      context.lineTo(to.x, to.y);
      context.stroke();
    }

    context.shadowBlur = 0;
    const depthSorted = [...projected].sort((a, b) => a.z - b.z);
    for (const point of depthSorted) {
      const opacity = Math.max(0.35, Math.min(0.9, 0.55 + point.z * 0.5));
      context.fillStyle = point.accent
        ? `rgba(36, 88, 211, ${opacity})`
        : `rgba(20, 22, 27, ${opacity})`;
      context.beginPath();
      context.arc(point.x, point.y, point.size + (point.contour ? 0.25 : 0), 0, Math.PI * 2);
      context.fill();
    }

    for (const point of depthSorted) {
      if (point.glow < 0.02) continue;
      const [red, green, blue] = neon[point.zone];
      context.shadowBlur = 8 + point.glow * 20;
      context.shadowColor = `rgb(${red}, ${green}, ${blue})`;
      context.fillStyle = `rgba(${red}, ${green}, ${blue}, ${0.45 + point.glow * 0.55})`;
      context.beginPath();
      context.arc(point.x, point.y, point.size + 1 + point.glow * 2.4, 0, Math.PI * 2);
      context.fill();
    }
    context.shadowBlur = 0;

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

  function updatePointer(event) {
    const bounds = stage.getBoundingClientRect();
    pointer.x = event.clientX - bounds.left;
    pointer.y = event.clientY - bounds.top;
    pointer.active = true;
    if (motionQuery.matches) paint(performance.now(), true);
  }

  function clearPointer() {
    pointer.active = false;
    if (motionQuery.matches) paint(performance.now(), true);
  }

  stage.addEventListener("pointermove", updatePointer, { passive: true });
  stage.addEventListener("pointerleave", clearPointer, { passive: true });

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
