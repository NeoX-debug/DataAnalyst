// ── Shared utilities ──────────────────────────────────────────────────────────

// Re-render Lucide icons after dynamic HTML insertions
function refreshIcons() {
  if (window.lucide) lucide.createIcons();
}

const GRAD_COLORS = [
  "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b",
  "#ef4444", "#ec4899", "#3b82f6", "#14b8a6",
  "#f97316", "#a855f7", "#22c55e", "#e11d48"
];

async function fetchJSON(url) {
  try {
    const res = await fetch(url);
    return await res.json();
  } catch (err) {
    console.error("fetchJSON error:", url, err);
    return {};
  }
}

async function postJSON(url, data) {
  try {
    const res = await fetch(url, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(data)
    });
    return await res.json();
  } catch (err) {
    console.error("postJSON error:", url, err);
    return { error: "Erreur réseau" };
  }
}

function showToast(msg, type = "info", duration = 3500) {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.3s";
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ── Chart.js shared dark theme options ────────────────────────────────────────
Chart.defaults.color = "#64748b";
Chart.defaults.font.family = "Inter";
Chart.defaults.plugins.legend.labels.usePointStyle = true;

function darkBarOptions(yLabel = "") {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: "#94a3b8", font: { family: "Inter", size: 11 } }
      },
      tooltip: {
        backgroundColor: "#1a1a2e",
        borderColor: "rgba(255,255,255,0.1)",
        borderWidth: 1,
        titleColor: "#e2e8f0",
        bodyColor: "#94a3b8",
        padding: 10,
        callbacks: {
          label: ctx => ` ${ctx.dataset.label ?? ""}: ${ctx.parsed.y ?? ctx.parsed.x} ${yLabel.includes("€") ? "€" : ""}`
        }
      }
    },
    scales: {
      x: {
        ticks: { color: "#64748b", font: { family: "Inter", size: 11 }, maxRotation: 30 },
        grid:  { color: "rgba(255,255,255,0.04)" },
        border: { color: "rgba(255,255,255,0.08)" }
      },
      y: {
        ticks: { color: "#64748b", font: { family: "Inter", size: 11 } },
        grid:  { color: "rgba(255,255,255,0.04)" },
        border: { color: "rgba(255,255,255,0.08)" },
        title: yLabel ? { display: true, text: yLabel, color: "#64748b", font: { size: 11 } } : { display: false }
      }
    }
  };
}

function darkDoughnutOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "right",
        labels: { color: "#94a3b8", font: { family: "Inter", size: 11 }, padding: 16 }
      },
      tooltip: {
        backgroundColor: "#1a1a2e",
        borderColor: "rgba(255,255,255,0.1)",
        borderWidth: 1,
        titleColor: "#e2e8f0",
        bodyColor: "#94a3b8",
        padding: 10
      }
    }
  };
}
