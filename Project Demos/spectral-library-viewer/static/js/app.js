/**
 * Spectral Library Viewer - Main Application
 *
 * Interactive spectral visualization with Plotly.js
 * Supports CSV, SLI (ENVI), and ASCII spectral formats
 */

(function () {
  "use strict";

  // ============================================================
  // State
  // ============================================================
  const state = {
    wavelengths: [],
    spectra: [],
    metadata: null,
    selectedIndices: new Set(),
    activeIndex: null,
    categories: {},
    enabledCategories: new Set(),
    searchTerm: "",
  };

  // Distinct colors for spectral traces (colorblind-friendly palette)
  const COLORS = [
    "#6366f1", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6",
    "#06b6d4", "#f97316", "#84cc16", "#ec4899", "#14b8a6",
    "#a855f7", "#eab308", "#22c55e", "#e11d48", "#0ea5e9",
    "#d946ef", "#65a30d", "#f43f5e", "#0891b2", "#c026d3",
    "#ca8a04", "#16a34a", "#dc2626", "#7c3aed", "#059669",
  ];

  // Spectral region definitions
  const SPECTRAL_REGIONS = [
    { name: "UV",   start: 200,  end: 400,  color: "rgba(148,103,189,0.08)" },
    { name: "VNIR", start: 400,  end: 1000, color: "rgba(44,160,44,0.06)" },
    { name: "SWIR", start: 1000, end: 2500, color: "rgba(255,127,14,0.06)" },
    { name: "MIR",  start: 2500, end: 5000, color: "rgba(214,39,40,0.06)" },
  ];

  // ============================================================
  // DOM References
  // ============================================================
  const dom = {
    dropZone: document.getElementById("drop-zone"),
    fileInput: document.getElementById("file-input"),
    btnBrowse: document.getElementById("btn-browse"),
    btnLoadSample: document.getElementById("btn-load-sample"),
    searchInput: document.getElementById("search-input"),
    categoryFilters: document.getElementById("category-filters"),
    spectraList: document.getElementById("spectra-list"),
    spectraCount: document.getElementById("spectra-count"),
    btnSelectAll: document.getElementById("btn-select-all"),
    btnSelectNone: document.getElementById("btn-select-none"),
    plotContainer: document.getElementById("plot-container"),
    toggleRegions: document.getElementById("toggle-regions"),
    toggleGrid: document.getElementById("toggle-grid"),
    toggleNormalize: document.getElementById("toggle-normalize"),
    toggleContinuum: document.getElementById("toggle-continuum"),
    yAxisSelect: document.getElementById("y-axis-select"),
    btnExport: document.getElementById("btn-export-png"),
    infoPanel: document.getElementById("info-panel"),
    infoContent: document.getElementById("info-content"),
    metadataPanel: document.getElementById("metadata-panel"),
    metadataContent: document.getElementById("metadata-content"),
  };

  // ============================================================
  // Toast Notifications
  // ============================================================
  function showToast(message, type = "info") {
    let container = document.querySelector(".toast-container");
    if (!container) {
      container = document.createElement("div");
      container.className = "toast-container";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // ============================================================
  // File Upload & Parsing
  // ============================================================
  function setupUpload() {
    dom.btnBrowse.addEventListener("click", (e) => {
      e.stopPropagation();
      dom.fileInput.click();
    });

    dom.dropZone.addEventListener("click", () => dom.fileInput.click());

    dom.fileInput.addEventListener("change", (e) => {
      if (e.target.files.length) uploadFiles(e.target.files);
    });

    dom.dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dom.dropZone.classList.add("drag-over");
    });

    dom.dropZone.addEventListener("dragleave", () => {
      dom.dropZone.classList.remove("drag-over");
    });

    dom.dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dom.dropZone.classList.remove("drag-over");
      if (e.dataTransfer.files.length) uploadFiles(e.dataTransfer.files);
    });
  }

  async function uploadFiles(files) {
    const formData = new FormData();
    for (const file of files) {
      formData.append("file", file);
    }

    showToast("Uploading and parsing files...", "info");

    try {
      const resp = await fetch("/api/upload", { method: "POST", body: formData });
      const data = await resp.json();

      if (!resp.ok) {
        showToast(data.error || "Upload failed", "error");
        return;
      }

      loadData(data);
      showToast(`Loaded ${data.spectra.length} spectra successfully`, "success");
    } catch (err) {
      showToast("Network error: " + err.message, "error");
    }
  }

  async function loadSampleLibrary() {
    showToast("Loading sample library...", "info");

    try {
      const resp = await fetch("/api/sample-library");
      const data = await resp.json();

      if (!resp.ok) {
        showToast(data.error || "Failed to load sample library", "error");
        return;
      }

      loadData(data);
      showToast(`Loaded ${data.spectra.length} sample spectra`, "success");
    } catch (err) {
      showToast("Network error: " + err.message, "error");
    }
  }

  // ============================================================
  // Data Loading
  // ============================================================
  function loadData(data) {
    state.wavelengths = data.wavelengths;
    state.spectra = data.spectra;
    state.metadata = data.metadata;
    state.selectedIndices.clear();
    state.activeIndex = null;
    state.categories = {};

    // Index categories
    data.spectra.forEach((s, i) => {
      const cat = s.category || "Uploaded";
      if (!state.categories[cat]) state.categories[cat] = [];
      state.categories[cat].push(i);
    });

    state.enabledCategories = new Set(Object.keys(state.categories));

    // Select first 5 spectra by default
    const limit = Math.min(5, data.spectra.length);
    for (let i = 0; i < limit; i++) state.selectedIndices.add(i);

    renderCategoryFilters();
    renderSpectraList();
    renderPlot();
    showMetadata();
  }

  // ============================================================
  // Category Filters
  // ============================================================
  function renderCategoryFilters() {
    dom.categoryFilters.innerHTML = "";

    const sortedCats = Object.keys(state.categories).sort();
    for (const cat of sortedCats) {
      const count = state.categories[cat].length;
      const label = document.createElement("label");
      label.className = "category-filter";

      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = state.enabledCategories.has(cat);
      cb.addEventListener("change", () => {
        if (cb.checked) state.enabledCategories.add(cat);
        else state.enabledCategories.delete(cat);
        renderSpectraList();
        renderPlot();
      });

      const text = document.createElement("span");
      text.textContent = cat;

      const badge = document.createElement("span");
      badge.className = "category-badge";
      badge.textContent = count;

      label.appendChild(cb);
      label.appendChild(text);
      label.appendChild(badge);
      dom.categoryFilters.appendChild(label);
    }
  }

  // ============================================================
  // Spectra List
  // ============================================================
  function getFilteredIndices() {
    const term = state.searchTerm.toLowerCase();
    const indices = [];

    state.spectra.forEach((s, i) => {
      const cat = s.category || "Uploaded";
      if (!state.enabledCategories.has(cat)) return;
      if (term && !s.name.toLowerCase().includes(term)) return;
      indices.push(i);
    });

    return indices;
  }

  function renderSpectraList() {
    const filtered = getFilteredIndices();
    dom.spectraCount.textContent = filtered.length;

    if (filtered.length === 0) {
      dom.spectraList.innerHTML =
        '<div class="empty-state"><p>No spectra match filters</p><span>Try adjusting search or category filters</span></div>';
      return;
    }

    dom.spectraList.innerHTML = "";

    filtered.forEach((idx) => {
      const s = state.spectra[idx];
      const color = COLORS[idx % COLORS.length];
      const isSelected = state.selectedIndices.has(idx);
      const isActive = state.activeIndex === idx;

      const item = document.createElement("div");
      item.className = "spectrum-item" + (isSelected ? " selected" : "") + (isActive ? " active" : "");

      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.className = "spectrum-checkbox";
      cb.checked = isSelected;
      cb.addEventListener("change", (e) => {
        e.stopPropagation();
        if (cb.checked) state.selectedIndices.add(idx);
        else state.selectedIndices.delete(idx);
        renderSpectraList();
        renderPlot();
      });

      const dot = document.createElement("div");
      dot.className = "spectrum-color-dot";
      dot.style.backgroundColor = color;

      const name = document.createElement("span");
      name.className = "spectrum-name";
      name.textContent = s.name;
      name.title = s.name;

      item.addEventListener("click", () => {
        state.activeIndex = state.activeIndex === idx ? null : idx;
        renderSpectraList();
        showSpectrumInfo();
      });

      item.appendChild(cb);
      item.appendChild(dot);
      item.appendChild(name);
      dom.spectraList.appendChild(item);
    });
  }

  // ============================================================
  // Spectrum Info
  // ============================================================
  function showSpectrumInfo() {
    if (state.activeIndex === null) {
      dom.infoPanel.style.display = "none";
      return;
    }

    const s = state.spectra[state.activeIndex];
    const values = s.values.filter((v) => v !== null && !isNaN(v));

    const min = Math.min(...values).toFixed(4);
    const max = Math.max(...values).toFixed(4);
    const mean = (values.reduce((a, b) => a + b, 0) / values.length).toFixed(4);

    let html = `
      <div class="info-row"><span class="info-label">Name</span><span class="info-value">${s.name}</span></div>
      <div class="info-row"><span class="info-label">Category</span><span class="info-value">${s.category || "N/A"}</span></div>
      <div class="info-row"><span class="info-label">Bands</span><span class="info-value">${s.values.length}</span></div>
      <div class="info-row"><span class="info-label">Min</span><span class="info-value">${min}</span></div>
      <div class="info-row"><span class="info-label">Max</span><span class="info-value">${max}</span></div>
      <div class="info-row"><span class="info-label">Mean</span><span class="info-value">${mean}</span></div>
    `;

    if (s.description) {
      html += `<div class="info-description">${s.description}</div>`;
    }

    dom.infoContent.innerHTML = html;
    dom.infoPanel.style.display = "block";
  }

  // ============================================================
  // Metadata Panel
  // ============================================================
  function showMetadata() {
    if (!state.metadata) {
      dom.metadataPanel.style.display = "none";
      return;
    }

    const m = state.metadata;
    let html = "";

    const fields = [
      ["Source", m.filename],
      ["Format", m.format],
      ["Spectra", m.num_spectra],
      ["Bands", m.num_bands],
      ["Wavelength Unit", m.wavelength_unit],
    ];

    fields.forEach(([label, value]) => {
      if (value !== undefined) {
        html += `<div class="info-row"><span class="info-label">${label}</span><span class="info-value">${value}</span></div>`;
      }
    });

    if (m.description) {
      html += `<div class="info-description">${m.description}</div>`;
    }

    dom.metadataContent.innerHTML = html;
    dom.metadataPanel.style.display = "block";
  }

  // ============================================================
  // Plot Rendering
  // ============================================================
  function computeContinuumRemoval(wavelengths, values) {
    const n = values.length;
    if (n < 3) return values.slice();

    // Build upper convex hull for continuum
    const hull = [0];
    for (let i = 1; i < n; i++) {
      while (hull.length >= 2) {
        const a = hull[hull.length - 2];
        const b = hull[hull.length - 1];
        const slopeAB = (values[b] - values[a]) / (wavelengths[b] - wavelengths[a]);
        const slopeAI = (values[i] - values[a]) / (wavelengths[i] - wavelengths[a]);
        if (slopeAI >= slopeAB) hull.pop();
        else break;
      }
      hull.push(i);
    }

    // Interpolate continuum line
    const continuum = new Float64Array(n);
    let hi = 0;
    for (let i = 0; i < n; i++) {
      while (hi < hull.length - 1 && i > hull[hi + 1]) hi++;
      const a = hull[hi];
      const b = hull[Math.min(hi + 1, hull.length - 1)];
      if (a === b) {
        continuum[i] = values[a];
      } else {
        const frac = (wavelengths[i] - wavelengths[a]) / (wavelengths[b] - wavelengths[a]);
        continuum[i] = values[a] + frac * (values[b] - values[a]);
      }
    }

    // Continuum removed = value / continuum
    const result = new Array(n);
    for (let i = 0; i < n; i++) {
      result[i] = continuum[i] > 0 ? values[i] / continuum[i] : values[i];
    }
    return result;
  }

  function renderPlot() {
    if (state.wavelengths.length === 0) return;

    const showRegions = dom.toggleRegions.checked;
    const showGrid = dom.toggleGrid.checked;
    const normalize = dom.toggleNormalize.checked;
    const continuumRemoval = dom.toggleContinuum.checked;
    const yAxisMode = dom.yAxisSelect.value;

    const traces = [];
    const wl = state.wavelengths;

    state.selectedIndices.forEach((idx) => {
      const s = state.spectra[idx];
      if (!s) return;

      let values = s.values.slice();

      // Transform based on y-axis mode
      if (yAxisMode === "absorbance") {
        values = values.map((v) => (v > 0 && v <= 1 ? -Math.log10(v) : 0));
      } else if (yAxisMode === "emissivity") {
        values = values.map((v) => 1 - v);
      }

      // Continuum removal
      if (continuumRemoval && yAxisMode === "reflectance") {
        values = computeContinuumRemoval(wl, values);
      }

      // Normalize
      if (normalize) {
        const max = Math.max(...values.filter((v) => !isNaN(v)));
        const min = Math.min(...values.filter((v) => !isNaN(v)));
        const range = max - min || 1;
        values = values.map((v) => (v - min) / range);
      }

      const color = COLORS[idx % COLORS.length];
      const isActive = state.activeIndex === idx;

      traces.push({
        x: wl,
        y: values,
        type: "scattergl",
        mode: "lines",
        name: s.name,
        line: {
          color: color,
          width: isActive ? 3 : 1.5,
        },
        opacity: isActive ? 1 : 0.85,
        hovertemplate: `<b>${s.name}</b><br>Wavelength: %{x:.0f} nm<br>Value: %{y:.4f}<extra></extra>`,
      });
    });

    // Spectral region shapes
    const shapes = [];
    const annotations = [];

    if (showRegions) {
      SPECTRAL_REGIONS.forEach((region) => {
        if (region.end < wl[0] || region.start > wl[wl.length - 1]) return;

        shapes.push({
          type: "rect",
          xref: "x",
          yref: "paper",
          x0: Math.max(region.start, wl[0]),
          x1: Math.min(region.end, wl[wl.length - 1]),
          y0: 0,
          y1: 1,
          fillcolor: region.color,
          line: { width: 0 },
          layer: "below",
        });

        const midX = (Math.max(region.start, wl[0]) + Math.min(region.end, wl[wl.length - 1])) / 2;
        annotations.push({
          x: midX,
          y: 1.02,
          xref: "x",
          yref: "paper",
          text: region.name,
          showarrow: false,
          font: { size: 10, color: "#6b7294" },
        });
      });
    }

    // Y-axis labels
    const yLabels = {
      reflectance: continuumRemoval ? "Continuum Removed Reflectance" : "Reflectance",
      absorbance: "Absorbance (-log₁₀R)",
      emissivity: "Emissivity (1-R)",
    };

    const layout = {
      paper_bgcolor: "#1a1d2e",
      plot_bgcolor: "#1a1d2e",
      margin: { t: 30, r: 40, b: 60, l: 70 },
      xaxis: {
        title: { text: "Wavelength (nm)", font: { size: 12, color: "#9ca3bf" } },
        color: "#9ca3bf",
        gridcolor: showGrid ? "#2d3154" : "transparent",
        gridwidth: 1,
        zerolinecolor: "#333760",
        tickfont: { size: 11 },
        range: [wl[0] - 20, wl[wl.length - 1] + 20],
      },
      yaxis: {
        title: {
          text: normalize ? "Normalized " + yLabels[yAxisMode] : yLabels[yAxisMode],
          font: { size: 12, color: "#9ca3bf" },
        },
        color: "#9ca3bf",
        gridcolor: showGrid ? "#2d3154" : "transparent",
        gridwidth: 1,
        zerolinecolor: "#333760",
        tickfont: { size: 11 },
      },
      legend: {
        font: { size: 11, color: "#9ca3bf" },
        bgcolor: "rgba(26,29,46,0.8)",
        bordercolor: "#333760",
        borderwidth: 1,
        orientation: "h",
        x: 0,
        y: -0.18,
        xanchor: "left",
      },
      shapes: shapes,
      annotations: annotations,
      hovermode: "x unified",
      hoverlabel: {
        bgcolor: "#252840",
        bordercolor: "#333760",
        font: { size: 12, color: "#e8eaf0" },
      },
      dragmode: "zoom",
    };

    const config = {
      responsive: true,
      displayModeBar: true,
      modeBarButtonsToRemove: ["lasso2d", "select2d"],
      displaylogo: false,
      toImageButtonOptions: {
        format: "png",
        filename: "spectral_plot",
        height: 800,
        width: 1400,
        scale: 2,
      },
    };

    // Clear placeholder
    const placeholder = dom.plotContainer.querySelector(".plot-placeholder");
    if (placeholder) placeholder.remove();

    Plotly.react(dom.plotContainer, traces, layout, config);
  }

  // ============================================================
  // Event Handlers
  // ============================================================
  function setupEventHandlers() {
    dom.btnLoadSample.addEventListener("click", loadSampleLibrary);

    dom.searchInput.addEventListener("input", (e) => {
      state.searchTerm = e.target.value;
      renderSpectraList();
    });

    dom.btnSelectAll.addEventListener("click", () => {
      getFilteredIndices().forEach((i) => state.selectedIndices.add(i));
      renderSpectraList();
      renderPlot();
    });

    dom.btnSelectNone.addEventListener("click", () => {
      state.selectedIndices.clear();
      renderSpectraList();
      renderPlot();
    });

    // Plot options
    dom.toggleRegions.addEventListener("change", renderPlot);
    dom.toggleGrid.addEventListener("change", renderPlot);
    dom.toggleNormalize.addEventListener("change", renderPlot);
    dom.toggleContinuum.addEventListener("change", renderPlot);
    dom.yAxisSelect.addEventListener("change", renderPlot);

    // Export
    dom.btnExport.addEventListener("click", () => {
      Plotly.downloadImage(dom.plotContainer, {
        format: "png",
        width: 1400,
        height: 800,
        scale: 2,
        filename: "spectral_library_plot",
      });
      showToast("Plot exported as PNG", "success");
    });
  }

  // ============================================================
  // Initialize
  // ============================================================
  function init() {
    setupUpload();
    setupEventHandlers();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
