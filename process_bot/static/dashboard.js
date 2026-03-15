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
  accent: "#d56f45",
  accentDeep: "#8f3f22",
  gold: "#f1b15c",
  teal: "#3b8274",
  rose: "#c96a7a",
  ink: "#1f1a17",
  muted: "#66594f",
  soft: ["#d56f45", "#f1b15c", "#3b8274", "#c96a7a", "#8f3f22", "#a8b765", "#5b6fb3", "#e58c8a"],
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

function baseOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: palette.muted,
          font: {
            family: "Avenir Next, Segoe UI, sans-serif",
          },
        },
      },
      tooltip: {
        backgroundColor: "rgba(31, 26, 23, 0.92)",
        titleColor: "#fffaf6",
        bodyColor: "#fffaf6",
        padding: 12,
      },
    },
    scales: {
      x: {
        ticks: { color: palette.muted },
        grid: { color: "rgba(31, 26, 23, 0.06)" },
      },
      y: {
        beginAtZero: true,
        ticks: { color: palette.muted, precision: 0 },
        grid: { color: "rgba(31, 26, 23, 0.08)" },
      },
    },
  };
}

function renderMetrics(stats) {
  const container = document.getElementById("metric-cards");
  container.innerHTML = [
    metricCard("Total events", stats.total_events),
    metricCard("Members logging", stats.total_users),
    metricCard("Companies tracked", stats.total_companies),
  ].join("");
}

function renderSummary(stats) {
  const latestActivity = stats.latest_activity
    ? new Date(stats.latest_activity).toLocaleDateString()
    : "No activity yet";
  const container = document.getElementById("company-summary");
  container.innerHTML = [
    ["Company", stats.company],
    ["Events", stats.total_events],
    ["Candidates", stats.total_candidates],
    ["Latest activity", latestActivity],
  ]
    .map(
      ([label, value]) => `
        <article class="summary-card">
          <p>${label}</p>
          <strong>${value}</strong>
        </article>
      `
    )
    .join("");
}

function setSearchStatus(message, tone = "default") {
  const status = document.getElementById("company-search-status");
  status.textContent = message;
  status.style.color = tone === "success" ? "var(--success)" : "var(--muted)";
}

function renderCompanyOptions(items) {
  const datalist = document.getElementById("company-options");
  datalist.innerHTML = items.map((company) => `<option value="${company.name}"></option>`).join("");
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
          backgroundColor: palette.soft,
          borderRadius: 12,
        },
      ],
    },
    options: {
      ...baseOptions(),
      plugins: { ...baseOptions().plugins, legend: { display: false } },
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
          backgroundColor: palette.soft,
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: baseOptions().plugins,
    },
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
          backgroundColor: palette.soft,
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: baseOptions().plugins,
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
          backgroundColor: "rgba(213, 111, 69, 0.16)",
          fill: true,
          tension: 0.28,
          pointBackgroundColor: palette.accentDeep,
          pointRadius: 4,
        },
      ],
    },
    options: baseOptions(),
  });
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
          backgroundColor: [palette.accent, palette.gold, palette.teal, palette.rose, palette.accentDeep],
          borderRadius: 12,
        },
      ],
    },
    options: {
      ...baseOptions(),
      plugins: { ...baseOptions().plugins, legend: { display: false } },
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
          backgroundColor: entries.length ? palette.soft : ["rgba(31, 26, 23, 0.12)"],
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: baseOptions().plugins,
    },
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
          backgroundColor: "rgba(59, 130, 116, 0.15)",
          fill: true,
          tension: 0.3,
          pointBackgroundColor: palette.teal,
          pointRadius: 4,
        },
      ],
    },
    options: baseOptions(),
  });
}

async function loadCompanyDetails(company) {
  const [stats, trends] = await Promise.all([
    fetchJson(`/api/stats/company/${company.slug}`),
    fetchJson(`/api/stats/trends?company_slug=${encodeURIComponent(company.slug)}`),
  ]);
  renderSummary(stats);
  renderCompanyStageChart(stats.stage_distribution);
  renderCompanyOutcomeChart(stats.outcome_distribution);
  renderCompanyTrendChart(trends);
  document.getElementById("company-details").hidden = false;
  setSearchStatus(`Showing exact stats for ${stats.company}.`, "success");
}

function bindCompanySearch() {
  const form = document.getElementById("company-search-form");
  const input = document.getElementById("company-search-input");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const company = findCompanyByName(input.value);
    if (!company) {
      document.getElementById("company-details").hidden = true;
      setSearchStatus("Company not found. Choose one of the tracked company names from the suggestions.");
      return;
    }

    setSearchStatus(`Loading exact stats for ${company.name}...`);
    try {
      await loadCompanyDetails(company);
    } catch (error) {
      document.getElementById("company-details").hidden = true;
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
    renderCompanyOptions(companyList);
    bindCompanySearch();

    if (companyList.length) {
      document.getElementById("company-search-input").value = companyList[0].name;
      await loadCompanyDetails(companyList[0]);
    } else {
      setSearchStatus("No companies tracked yet. Run `/process` in Discord to populate the dashboard.");
    }
  } catch (error) {
    document.getElementById("metric-cards").innerHTML = metricCard("Dashboard", "Unable to load");
    setSearchStatus("Dashboard data could not be loaded.");
  }
}

initDashboard();
