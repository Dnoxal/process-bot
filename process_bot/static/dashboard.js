async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

let companies = [];
const charts = {};

const palette = {
  ink: "#1c1815",
  muted: "#6d635a",
  accent: "#d16d45",
  accentDeep: "#8b4527",
  accentSoft: "#efb577",
  teal: "#2d7b77",
  gold: "#e7b458",
  berry: "#b85f79",
  slate: "#7884b4",
  olive: "#98a159",
  soft: ["#d16d45", "#e7b458", "#2d7b77", "#b85f79", "#8b4527", "#7884b4", "#98a159"],
};

function humanizeLabel(value) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function metricCard(label, value) {
  return `
    <article class="metric-card">
      <div class="metric-label">${label}</div>
      <div class="metric-value">${value}</div>
    </article>
  `;
}

function summaryCard(label, value) {
  return `
    <article class="summary-card">
      <p class="summary-label">${label}</p>
      <strong class="summary-value">${value}</strong>
    </article>
  `;
}

function destroyChart(name) {
  if (charts[name]) {
    charts[name].destroy();
    charts[name] = null;
  }
}

function createChart(name, elementId, config) {
  destroyChart(name);
  const context = document.getElementById(elementId);
  charts[name] = new Chart(context, config);
}

function lineGradient(context, topColor, bottomColor) {
  const chart = context.chart;
  const { ctx, chartArea } = chart;
  if (!chartArea) {
    return bottomColor;
  }
  const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
  gradient.addColorStop(0, topColor);
  gradient.addColorStop(1, bottomColor);
  return gradient;
}

function axisOptions() {
  return {
    ticks: {
      color: palette.muted,
      font: {
        family: "Avenir Next, Segoe UI, sans-serif",
      },
    },
    grid: {
      color: "rgba(28, 24, 21, 0.07)",
      drawBorder: false,
    },
  };
}

function commonPlugins() {
  return {
    legend: {
      labels: {
        color: palette.muted,
        usePointStyle: true,
        boxWidth: 10,
        font: {
          family: "Avenir Next, Segoe UI, sans-serif",
        },
      },
    },
    tooltip: {
      backgroundColor: "rgba(28, 24, 21, 0.94)",
      titleColor: "#fff8f1",
      bodyColor: "#fff8f1",
      padding: 12,
      displayColors: true,
    },
  };
}

function baseCartesianOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: commonPlugins(),
    scales: {
      x: axisOptions(),
      y: {
        ...axisOptions(),
        beginAtZero: true,
        ticks: {
          ...axisOptions().ticks,
          precision: 0,
        },
      },
    },
  };
}

function baseCircularOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    cutout: "56%",
    plugins: commonPlugins(),
  };
}

function setSearchStatus(message, tone = "default") {
  const status = document.getElementById("company-search-status");
  status.textContent = message;
  status.style.color = tone === "success" ? "var(--success)" : "var(--muted)";
}

function renderMetrics(stats) {
  document.getElementById("metric-cards").innerHTML = [
    metricCard("Total events", stats.total_events),
    metricCard("Members logging", stats.total_users),
    metricCard("Companies tracked", stats.total_companies),
  ].join("");
}

function renderCompanyOptions(items) {
  document.getElementById("company-options").innerHTML = items
    .map((company) => `<option value="${company.name}"></option>`)
    .join("");
}

function findCompanyByName(name) {
  return companies.find((company) => company.name.toLowerCase() === name.trim().toLowerCase()) || null;
}

function renderTopCompaniesChart(topCompanies) {
  createChart("topCompanies", "top-companies-chart", {
    type: "bar",
    data: {
      labels: topCompanies.map((row) => row.company),
      datasets: [
        {
          label: "Events",
          data: topCompanies.map((row) => row.events),
          borderRadius: 14,
          backgroundColor: topCompanies.map((_, index) => palette.soft[index % palette.soft.length]),
        },
      ],
    },
    options: {
      ...baseCartesianOptions(),
      plugins: {
        ...commonPlugins(),
        legend: { display: false },
      },
    },
  });
}

function renderGlobalStageChart(stageDistribution) {
  const entries = Object.entries(stageDistribution);
  createChart("globalStages", "stage-distribution-chart", {
    type: "doughnut",
    data: {
      labels: entries.map(([label]) => humanizeLabel(label)),
      datasets: [
        {
          data: entries.map(([, value]) => value),
          backgroundColor: entries.map((_, index) => palette.soft[index % palette.soft.length]),
          borderWidth: 0,
        },
      ],
    },
    options: baseCircularOptions(),
  });
}

function renderGlobalOutcomeChart(outcomeDistribution) {
  const entries = Object.entries(outcomeDistribution);
  createChart("globalOutcomes", "outcome-distribution-chart", {
    type: "pie",
    data: {
      labels: entries.map(([label]) => humanizeLabel(label)),
      datasets: [
        {
          data: entries.map(([, value]) => value),
          backgroundColor: entries.map((_, index) => palette.soft[index % palette.soft.length]),
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: commonPlugins(),
    },
  });
}

function renderGlobalTrendChart(points) {
  createChart("globalTrend", "global-trend-chart", {
    type: "line",
    data: {
      labels: points.map((point) => point.period_start),
      datasets: [
        {
          label: "Daily events",
          data: points.map((point) => point.events),
          borderColor: palette.accent,
          borderWidth: 3,
          backgroundColor(context) {
            return lineGradient(context, "rgba(209, 109, 69, 0.30)", "rgba(209, 109, 69, 0.02)");
          },
          fill: true,
          tension: 0.32,
          pointRadius: 3.5,
          pointHoverRadius: 5,
          pointBackgroundColor: palette.accentDeep,
        },
      ],
    },
    options: baseCartesianOptions(),
  });
}

function renderComparisonChart(stageDistribution, outcomeDistribution) {
  const stageTotal = Object.values(stageDistribution).reduce((sum, value) => sum + value, 0);
  const outcomeTotal = Object.values(outcomeDistribution).reduce((sum, value) => sum + value, 0);
  createChart("comparison", "comparison-chart", {
    type: "bar",
    data: {
      labels: ["Stage logs", "Outcome logs"],
      datasets: [
        {
          label: "Count",
          data: [stageTotal, outcomeTotal],
          borderRadius: 16,
          backgroundColor: [palette.accent, palette.teal],
        },
      ],
    },
    options: {
      ...baseCartesianOptions(),
      plugins: {
        ...commonPlugins(),
        legend: { display: false },
      },
    },
  });
}

function renderCompanySummary(stats) {
  const latestActivity = stats.latest_activity
    ? new Date(stats.latest_activity).toLocaleDateString()
    : "No activity yet";
  document.getElementById("company-summary").innerHTML = [
    summaryCard("Company", stats.company),
    summaryCard("Events", stats.total_events),
    summaryCard("Candidates", stats.total_candidates),
    summaryCard("Latest activity", latestActivity),
  ].join("");
}

function setCompanyHeadings(companyName) {
  document.getElementById("company-spotlight-title").textContent = `${companyName} board`;
  document.getElementById("company-trend-title").textContent = `${companyName} activity over time`;
  document.getElementById("company-stage-title").textContent = `${companyName} stage breakdown`;
  document.getElementById("company-funnel-title").textContent = `${companyName} recruiting funnel`;
  document.getElementById("company-outcome-title").textContent = `${companyName} outcome mix`;
}

function renderCompanyFunnel(stageDistribution, outcomeDistribution) {
  const funnel = document.getElementById("company-funnel");
  const offeredCount = outcomeDistribution.offered || 0;
  const rejectedCount = outcomeDistribution.rejected || 0;
  const steps = [
    { label: "OA", value: stageDistribution.oa || 0, color: palette.accent },
    { label: "Behavioral", value: stageDistribution.behavioral || 0, color: palette.gold },
    { label: "Onsite", value: stageDistribution.onsite || 0, color: palette.teal },
    { label: "Offers", value: offeredCount, color: palette.berry },
    { label: "Rejections", value: rejectedCount, color: palette.slate },
  ].filter((step) => step.value > 0);

  if (!steps.length) {
    funnel.innerHTML = `
      <div class="funnel-empty">
        <div>
          <strong>No funnel data yet</strong>
          <p>Once this company has stage and outcome logs, the funnel will appear here.</p>
        </div>
      </div>
    `;
    return;
  }

  const maxValue = Math.max(...steps.map((step) => step.value), 1);
  funnel.innerHTML = steps
    .map((step, index) => {
      const width = 100 - index * 9;
      const opacity = Math.max(step.value / maxValue, 0.28);
      return `
        <div
          class="funnel-step"
          style="width: ${Math.max(width, 52)}%; background: linear-gradient(135deg, ${step.color}, rgba(28, 24, 21, ${1 - opacity}));"
        >
          <strong>${step.label}</strong>
          <span>${step.value}</span>
        </div>
      `;
    })
    .join("");
}

function renderCompanyStageChart(stageDistribution) {
  const entries = Object.entries(stageDistribution);
  createChart("companyStage", "company-stage-chart", {
    type: "bar",
    data: {
      labels: entries.map(([label]) => humanizeLabel(label)),
      datasets: [
        {
          label: "Events",
          data: entries.map(([, value]) => value),
          borderRadius: 14,
          backgroundColor: entries.map((_, index) => palette.soft[index % palette.soft.length]),
        },
      ],
    },
    options: {
      ...baseCartesianOptions(),
      plugins: {
        ...commonPlugins(),
        legend: { display: false },
      },
    },
  });
}

function renderCompanyOutcomeChart(outcomeDistribution) {
  const entries = Object.entries(outcomeDistribution);
  createChart("companyOutcome", "company-outcome-chart", {
    type: "doughnut",
    data: {
      labels: entries.length ? entries.map(([label]) => humanizeLabel(label)) : ["No outcomes yet"],
      datasets: [
        {
          data: entries.length ? entries.map(([, value]) => value) : [1],
          backgroundColor: entries.length
            ? entries.map((_, index) => palette.soft[index % palette.soft.length])
            : ["rgba(28, 24, 21, 0.12)"],
          borderWidth: 0,
        },
      ],
    },
    options: baseCircularOptions(),
  });
}

function renderCompanyTrendChart(points) {
  createChart("companyTrend", "company-trend-chart", {
    type: "line",
    data: {
      labels: points.length ? points.map((point) => point.period_start) : ["No data"],
      datasets: [
        {
          label: "Daily events",
          data: points.length ? points.map((point) => point.events) : [0],
          borderColor: palette.teal,
          borderWidth: 3,
          backgroundColor(context) {
            return lineGradient(context, "rgba(45, 123, 119, 0.28)", "rgba(45, 123, 119, 0.03)");
          },
          fill: true,
          tension: 0.32,
          pointRadius: 3.5,
          pointHoverRadius: 5,
          pointBackgroundColor: palette.teal,
        },
      ],
    },
    options: baseCartesianOptions(),
  });
}

async function loadCompanyDetails(company) {
  const [stats, trends] = await Promise.all([
    fetchJson(`/api/stats/company/${company.slug}`),
    fetchJson(`/api/stats/trends?company_slug=${encodeURIComponent(company.slug)}`),
  ]);

  setCompanyHeadings(stats.company);
  renderCompanySummary(stats);
  renderCompanyStageChart(stats.stage_distribution);
  renderCompanyFunnel(stats.stage_distribution, stats.outcome_distribution);
  renderCompanyOutcomeChart(stats.outcome_distribution);
  renderCompanyTrendChart(trends);
  document.getElementById("company-empty-state").hidden = true;
  document.getElementById("company-board").hidden = false;
  setSearchStatus(`Showing exact stats for ${stats.company}.`, "success");
}

function bindCompanySearch() {
  const form = document.getElementById("company-search-form");
  const input = document.getElementById("company-search-input");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const company = findCompanyByName(input.value);
    if (!company) {
      document.getElementById("company-board").hidden = true;
      document.getElementById("company-empty-state").hidden = false;
      setSearchStatus("Company not found. Choose one of the tracked company names from the suggestions.");
      return;
    }

    setSearchStatus(`Loading exact stats for ${company.name}...`);
    try {
      await loadCompanyDetails(company);
    } catch (error) {
      document.getElementById("company-board").hidden = true;
      document.getElementById("company-empty-state").hidden = false;
      setSearchStatus("Unable to load that company right now. Please try again.");
    }
  });
}

async function initDashboard() {
  try {
    const [stats, trends, companyList] = await Promise.all([
      fetchJson("/api/stats/global"),
      fetchJson("/api/stats/trends"),
      fetchJson("/api/companies"),
    ]);

    companies = companyList;
    renderMetrics(stats);
    renderTopCompaniesChart(stats.top_companies);
    renderGlobalStageChart(stats.stage_distribution);
    renderGlobalOutcomeChart(stats.outcome_distribution);
    renderGlobalTrendChart(trends);
    renderComparisonChart(stats.stage_distribution, stats.outcome_distribution);
    renderCompanyOptions(companyList);
    bindCompanySearch();
    setSearchStatus("Search a company to open its detailed board.");
  } catch (error) {
    document.getElementById("metric-cards").innerHTML = metricCard("Dashboard", "Unable to load");
    setSearchStatus("Dashboard data could not be loaded.");
  }
}

initDashboard();
