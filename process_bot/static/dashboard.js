async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

let companies = [];

function humanizeLabel(value) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function renderMetrics(stats) {
  const container = document.getElementById("metric-cards");
  const metrics = [
    ["Total events", stats.total_events],
    ["Members logging", stats.total_users],
    ["Companies tracked", stats.total_companies],
  ];
  container.innerHTML = metrics
    .map(
      ([label, value]) => `
        <article class="metric-card">
          <div class="metric-label">${label}</div>
          <div class="metric-value">${value}</div>
        </article>
      `
    )
    .join("");
}

function renderList(containerId, entries, keyLabel) {
  const container = document.getElementById(containerId);
  if (!entries.length) {
    container.innerHTML = `<div class="list-row"><strong>No data yet</strong><span>Start logging in Discord</span></div>`;
    return;
  }

  container.innerHTML = entries
    .map(
      ([label, value]) => `
        <div class="list-row">
          <strong>${label}</strong>
          <span>${value} ${keyLabel}</span>
        </div>
      `
    )
    .join("");
}

function renderTopCompanies(topCompanies) {
  const entries = topCompanies.map((row) => [row.company, row.events]);
  renderList("top-companies", entries, "events");
}

function renderDistribution(containerId, values) {
  renderList(
    containerId,
    Object.entries(values).map(([label, value]) => [humanizeLabel(label), value]),
    "logs"
  );
}

function renderTrends(points) {
  const container = document.getElementById("trend-chart");
  if (!points.length) {
    container.innerHTML = `<div class="list-row"><strong>No trend data yet</strong><span>Events appear after your first logs</span></div>`;
    return;
  }

  const maxEvents = Math.max(...points.map((point) => point.events), 1);
  container.innerHTML = points
    .map((point) => {
      const width = `${Math.max((point.events / maxEvents) * 100, 4)}%`;
      return `
        <div class="trend-row">
          <span>${point.period_start}</span>
          <div class="trend-bar">
            <div class="trend-bar-fill" style="width: ${width}"></div>
          </div>
          <strong>${point.events}</strong>
        </div>
      `;
    })
    .join("");
}

function renderCompanyOptions(items) {
  const datalist = document.getElementById("company-options");
  datalist.innerHTML = items
    .map((company) => `<option value="${company.name}"></option>`)
    .join("");
}

function setSearchStatus(message, tone = "default") {
  const status = document.getElementById("company-search-status");
  status.textContent = message;
  status.style.color = tone === "success" ? "var(--success)" : "var(--muted)";
}

function renderSummary(stats) {
  const summary = document.getElementById("company-summary");
  const latestActivity = stats.latest_activity
    ? new Date(stats.latest_activity).toLocaleDateString()
    : "No activity yet";
  const cards = [
    ["Company", stats.company],
    ["Events", stats.total_events],
    ["Candidates", stats.total_candidates],
    ["Latest activity", latestActivity],
  ];
  summary.innerHTML = cards
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

function renderBarChart(containerId, values, emptyMessage) {
  const container = document.getElementById(containerId);
  const entries = Object.entries(values).sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]));
  if (!entries.length) {
    container.innerHTML = `<div class="list-row"><strong>${emptyMessage}</strong><span>Log more data in Discord</span></div>`;
    return;
  }

  const maxValue = Math.max(...entries.map(([, value]) => value), 1);
  container.innerHTML = entries
    .map(([label, value]) => {
      const width = `${Math.max((value / maxValue) * 100, 6)}%`;
      const readableLabel = humanizeLabel(label);
      return `
        <div class="chart-row">
          <span class="chart-label">${readableLabel}</span>
          <div class="chart-track" aria-hidden="true">
            <div class="chart-fill" style="width: ${width}"></div>
          </div>
          <span class="chart-value">${value}</span>
        </div>
      `;
    })
    .join("");
}

function renderTrendPlot(points) {
  const container = document.getElementById("company-trend-chart");
  if (!points.length) {
    container.innerHTML = `<div class="list-row"><strong>No trend data yet</strong><span>Track a few events first</span></div>`;
    return;
  }

  const width = 720;
  const height = 220;
  const padding = 22;
  const maxEvents = Math.max(...points.map((point) => point.events), 1);
  const step = points.length === 1 ? width - padding * 2 : (width - padding * 2) / (points.length - 1);
  const coordinates = points.map((point, index) => {
    const x = padding + index * step;
    const y = height - padding - ((height - padding * 2) * point.events) / maxEvents;
    return { ...point, x, y };
  });
  const polyline = coordinates.map((point) => `${point.x},${point.y}`).join(" ");

  container.innerHTML = `
    <div class="trend-svg-wrap">
      <svg viewBox="0 0 ${width} ${height}" aria-hidden="true">
        <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="rgba(31, 26, 23, 0.18)" stroke-width="2"></line>
        <line x1="${padding}" y1="${padding}" x2="${padding}" y2="${height - padding}" stroke="rgba(31, 26, 23, 0.12)" stroke-width="2"></line>
        <polyline fill="none" stroke="#d97143" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" points="${polyline}"></polyline>
        ${coordinates
          .map(
            (point) => `
              <circle cx="${point.x}" cy="${point.y}" r="5" fill="#9f4720">
                <title>${point.period_start}: ${point.events} events</title>
              </circle>
            `
          )
          .join("")}
      </svg>
    </div>
    <div class="trend-axis">
      <span>${points[0].period_start}</span>
      <span>${points[points.length - 1].period_start}</span>
    </div>
    <div class="trend-caption">
      <span>Peak volume: ${maxEvents} events</span>
      <span>${points.length} day${points.length === 1 ? "" : "s"} tracked</span>
    </div>
  `;
}

function findCompanyByName(name) {
  return companies.find((company) => company.name.toLowerCase() === name.trim().toLowerCase()) || null;
}

async function loadCompanyDetails(company) {
  const [stats, trends] = await Promise.all([
    fetchJson(`/api/stats/company/${company.slug}`),
    fetchJson(`/api/stats/trends?company_slug=${encodeURIComponent(company.slug)}`),
  ]);
  renderSummary(stats);
  renderBarChart("company-stage-chart", stats.stage_distribution, "No stage data yet");
  renderBarChart("company-outcome-chart", stats.outcome_distribution, "No outcome data yet");
  renderTrendPlot(trends);
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
      setSearchStatus("Company not found. Pick one of the tracked company names from the suggestions.");
      return;
    }

    setSearchStatus(`Loading stats for ${company.name}...`);
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
    renderTopCompanies(stats.top_companies);
    renderDistribution("stage-distribution", stats.stage_distribution);
    renderDistribution("outcome-distribution", stats.outcome_distribution);
    renderTrends(trends);
    renderCompanyOptions(companyList);
    bindCompanySearch();
    if (companyList.length) {
      document.getElementById("company-search-input").value = companyList[0].name;
      await loadCompanyDetails(companyList[0]);
    } else {
      setSearchStatus("No companies tracked yet. Log a few `!process` commands to populate search.");
    }
  } catch (error) {
    const panel = document.getElementById("metric-cards");
    panel.innerHTML = `<article class="metric-card"><div class="metric-label">Dashboard</div><div>Unable to load data yet.</div></article>`;
    setSearchStatus("Dashboard data could not be loaded.");
  }
}

initDashboard();
