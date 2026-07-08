import React, { useEffect, useMemo, useState } from "react";
import { Bar, Line } from "react-chartjs-2";
import { GravityStarsBackground } from "./components/animate-ui/components/backgrounds/gravity-stars";

const tracks = [
  { id: "all", label: "All" },
  { id: "intern", label: "Intern" },
  { id: "full_time", label: "Full-Time" },
];

const trendGranularities = [
  { id: "daily", label: "Daily" },
  { id: "weekly", label: "Weekly" },
  { id: "monthly", label: "Monthly" },
];

const stageOrder = ["oa", "behavioral", "technical", "offer"];
const stageLabels = {
  oa: "OA",
  behavioral: "Behavioral",
  technical: "Technical",
  offer: "Offer",
};

const editorial = {
  paper: "#F9F8F6",
  ink: "#1A1A1A",
  taupe: "#EBE5DE",
  muted: "#6C6863",
  gold: "#D4AF37",
};

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function humanize(value) {
  if (!value) return "Unknown";
  return (value === "full_time" ? "Full-Time" : value)
    .replaceAll("_", " ")
    .split(" ")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatNumber(value) {
  if (value === null || value === undefined || value === "—") return "—";
  if (typeof value === "string") return value;
  return new Intl.NumberFormat("en-US").format(value);
}

function formatDate(value) {
  if (!value) return "No activity";
  return new Date(value).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function startOfWeek(date) {
  const result = new Date(date);
  const day = result.getUTCDay();
  const offset = day === 0 ? -6 : 1 - day;
  result.setUTCDate(result.getUTCDate() + offset);
  return result;
}

function dateKey(date) {
  return date.toISOString().slice(0, 10);
}

function formatTrendLabel(key, granularity) {
  const date = new Date(`${key}T00:00:00Z`);
  if (granularity === "monthly") {
    return date.toLocaleDateString(undefined, { month: "short", year: "numeric", timeZone: "UTC" });
  }
  if (granularity === "weekly") {
    return `Week of ${date.toLocaleDateString(undefined, { month: "short", day: "numeric", timeZone: "UTC" })}`;
  }
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric", timeZone: "UTC" });
}

function trendBucketKey(value, granularity) {
  const date = new Date(`${value}T00:00:00Z`);
  if (granularity === "monthly") {
    return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}-01`;
  }
  if (granularity === "weekly") {
    return dateKey(startOfWeek(date));
  }
  return dateKey(date);
}

function aggregateTrendPoints(points, granularity) {
  const buckets = new Map();
  for (const point of points) {
    const key = trendBucketKey(point.period_start, granularity);
    buckets.set(key, (buckets.get(key) || 0) + point.events);
  }
  return Array.from(buckets.entries())
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, events]) => ({
      period_start: key,
      label: formatTrendLabel(key, granularity),
      events,
    }));
}

function orderedStageEntries(distribution = {}) {
  return stageOrder.map((stage) => [stage, distribution[stage] || 0]);
}

function outcomeCounts(distribution = {}) {
  return {
    offers: (distribution.offered || 0) + (distribution.accepted || 0),
    rejections: (distribution.rejected || 0) + (distribution.withdrawn || 0),
  };
}

function baseChartOptions({ horizontal = false, percent = false, categoryLabels = null } = {}) {
  const xTicks = {
    color: "rgba(249, 248, 246, 0.68)",
    font: { family: "Inter, Avenir Next, sans-serif", size: 11 },
    maxRotation: 0,
    minRotation: 0,
    autoSkip: true,
    maxTicksLimit: 9,
  };
  if (categoryLabels) {
    xTicks.callback = (_value, index) => categoryLabels[index] || "";
  } else if (percent) {
    xTicks.callback = (value) => `${value}%`;
  }

  return {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: horizontal ? "y" : "x",
    animation: {
      duration: 900,
      easing: "easeOutQuart",
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "rgba(26, 26, 26, 0.94)",
        titleColor: editorial.paper,
        bodyColor: "#EBE5DE",
        borderColor: "rgba(212, 175, 55, 0.45)",
        borderWidth: 1,
        padding: 12,
        displayColors: false,
        callbacks: percent ? { label: (context) => `${context.raw}%` } : undefined,
      },
    },
    scales: {
      x: {
        beginAtZero: true,
        ticks: xTicks,
        grid: { display: false },
        border: { color: "rgba(249, 248, 246, 0.16)" },
      },
      y: {
        beginAtZero: true,
        max: percent ? 100 : undefined,
        ticks: {
          color: "rgba(249, 248, 246, 0.68)",
          precision: 0,
          font: { family: "Inter, Avenir Next, sans-serif", size: 11 },
          callback: percent ? (value) => `${value}%` : undefined,
        },
        grid: { color: "rgba(249, 248, 246, 0.08)" },
        border: { color: "rgba(249, 248, 246, 0.16)" },
      },
    },
  };
}

function NoiseOverlay() {
  return <div className="paper-noise" aria-hidden="true" />;
}

function PrimaryButton({ children, type = "button", ...props }) {
  return (
    <button className="button-primary" type={type} {...props}>
      <span aria-hidden="true" />
      <strong>{children}</strong>
    </button>
  );
}

function SecondaryButton({ children, active, ...props }) {
  return (
    <button className={`button-secondary ${active ? "is-active" : ""}`} type="button" {...props}>
      {children}
    </button>
  );
}

function EditorialMetric({ label, value, note }) {
  const isTextValue = typeof value === "string" && value !== "—";
  return (
    <article className={`metric ${isTextValue ? "metric-text" : ""}`}>
      <p>{label}</p>
      <strong>{formatNumber(value)}</strong>
      <span>{note}</span>
    </article>
  );
}

function Header({ track, setTrack, companies, searchValue, setSearchValue, onSearch, status }) {
  return (
    <header className="site-header">
      <a className="wordmark" href="#overview" aria-label="ProcTracker home">
        proctracker
      </a>
      <form className="company-form" onSubmit={onSearch}>
        <input
          list="company-options"
          value={searchValue}
          onChange={(event) => setSearchValue(event.target.value)}
          placeholder="Search a company"
          aria-label="Search a company"
        />
        <datalist id="company-options">
          {companies.map((company) => (
            <option key={company.slug} value={company.name} />
          ))}
        </datalist>
        <PrimaryButton type="submit">Open</PrimaryButton>
      </form>
      <div className="track-switch" aria-label="Employment track">
        {tracks.map((item) => (
          <SecondaryButton
            key={item.id}
            active={track === item.id}
            onClick={() => setTrack(item.id)}
          >
            {item.label}
          </SecondaryButton>
        ))}
      </div>
      <p className="load-status">{status}</p>
    </header>
  );
}

function Hero({ overview }) {
  const stageEntries = orderedStageEntries(overview?.stage_distribution);
  const totalStageLogs = stageEntries.reduce((sum, [, count]) => sum + count, 0);
  const offerCount = overview?.stage_distribution?.offer || 0;
  const offerShare = totalStageLogs ? Math.round((offerCount / totalStageLogs) * 100) : 0;

  return (
    <section className="hero" id="overview">
      <div className="hero-copy">
        <h1>
          The recruiting <em>ledger</em> for computer science internships.
        </h1>
      </div>
      <div className="hero-plate" aria-label="Process activity summary">
        <div>
          <p>Current Process Arc</p>
          <strong>OA → Behavioral → Technical → Offer</strong>
        </div>
        <dl>
          <div>
            <dt>Process logs</dt>
            <dd>{formatNumber(totalStageLogs)}</dd>
          </div>
          <div>
            <dt>Offer share</dt>
            <dd>{offerShare}%</dd>
          </div>
        </dl>
      </div>
    </section>
  );
}

function StageIndex({ distribution }) {
  const entries = orderedStageEntries(distribution);

  return (
    <div className="stage-index">
      {entries.map(([stage, count], index) => (
        <article key={stage} className="stage-row">
          <span>{String(index + 1).padStart(2, "0")}</span>
          <div>
            <p>{stageLabels[stage]}</p>
          </div>
          <strong>{formatNumber(count)}</strong>
        </article>
      ))}
    </div>
  );
}

function OutcomeLedger({ distribution }) {
  const counts = outcomeCounts(distribution);
  const total = counts.offers + counts.rejections;

  return (
    <div className="outcome-ledger">
      <article>
        <p>Offers</p>
        <strong>{formatNumber(counts.offers)}</strong>
        <span>{total ? `${Math.round((counts.offers / total) * 100)}% of final outcomes` : "No final outcomes"}</span>
      </article>
      <article>
        <p>Rejections</p>
        <strong>{formatNumber(counts.rejections)}</strong>
        <span>{total ? `${Math.round((counts.rejections / total) * 100)}% of final outcomes` : "No final outcomes"}</span>
      </article>
    </div>
  );
}

function TopCompanies({ companies, onOpen }) {
  if (!companies?.length) {
    return <p className="empty-copy">Company rankings appear after process updates are logged.</p>;
  }

  return (
    <div className="company-table">
      {companies.slice(0, 8).map((company, index) => (
        <button key={company.label} type="button" onClick={() => onOpen(company.label)}>
          <span>{String(index + 1).padStart(2, "0")}</span>
          <strong>{company.label}</strong>
          <em>{formatNumber(company.value)}</em>
        </button>
      ))}
    </div>
  );
}

function RecentOffers({ offers }) {
  if (!offers?.length) {
    return <p className="empty-copy">Offer activity will appear here once candidates log positive outcomes.</p>;
  }

  return (
    <ol className="offer-list">
      {offers.slice(0, 6).map((offer, index) => (
        <li key={`${offer.company_slug}-${offer.occurred_at}-${index}`}>
          <span>{String(index + 1).padStart(2, "0")}</span>
          <div>
            <strong>{offer.company}</strong>
            <p>{formatDate(offer.occurred_at)}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}

function ProcessReadout({ overview, stageEntries }) {
  const totalStageLogs = stageEntries.reduce((sum, [, count]) => sum + count, 0);
  const dominantStage = stageEntries.reduce(
    (winner, entry) => (entry[1] > winner[1] ? entry : winner),
    stageEntries[0] || ["oa", 0],
  );
  const technicalReach = (overview?.stage_distribution?.technical || 0) + (overview?.stage_distribution?.offer || 0);
  const reachShare = totalStageLogs ? Math.round((technicalReach / totalStageLogs) * 100) : 0;
  const outcomes = outcomeCounts(overview?.outcome_distribution);
  const outcomeTotal = outcomes.offers + outcomes.rejections;
  const offerShare = outcomeTotal ? Math.round((outcomes.offers / outcomeTotal) * 100) : 0;

  return (
    <article className="chart-card readout-card wide">
      <div className="card-heading">
        <div>
          <p>Signal readout</p>
          <span>What the aggregate process logs are saying</span>
        </div>
      </div>

      <div className="readout-grid">
        <div className="readout-item">
          <span>Most active stage</span>
          <strong>{stageLabels[dominantStage[0]]}</strong>
          <p>{formatNumber(dominantStage[1])} normalized process logs</p>
        </div>
        <div className="readout-item">
          <span>Later-stage reach</span>
          <strong>{reachShare}%</strong>
          <p>Technical and offer logs after inferred progression</p>
        </div>
        <div className="readout-item">
          <span>Offer share</span>
          <strong>{offerShare}%</strong>
          <p>{formatNumber(outcomeTotal)} final outcome logs</p>
        </div>
      </div>
    </article>
  );
}

function ChartPanel({ overview }) {
  const [trendGranularity, setTrendGranularity] = useState("weekly");
  const trendPoints = overview?.trend_points || [];
  const visibleTrendPoints = useMemo(
    () => aggregateTrendPoints(trendPoints, trendGranularity),
    [trendPoints, trendGranularity],
  );
  const stageEntries = orderedStageEntries(overview?.stage_distribution);

  return (
    <section className="dark-section" id="process">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Process Index</p>
          <h2>The shape of the pipeline.</h2>
        </div>
        <p>
          Later-stage logs imply earlier stages, so a technical update counts as OA and Behavioral reach.
          Rejections remain separate outcomes rather than forward progress.
        </p>
      </div>

      <div className="analytics-grid">
        <article className="chart-card wide">
          <div className="card-heading">
            <div>
              <p>Activity over time</p>
              <span>Logged Discord process updates</span>
            </div>
            <div className="time-switch" aria-label="Activity time range">
              {trendGranularities.map((item) => (
                <button
                  key={item.id}
                  className={trendGranularity === item.id ? "is-active" : ""}
                  type="button"
                  onClick={() => setTrendGranularity(item.id)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
          <div className="chart-frame">
            <Line
              options={baseChartOptions()}
              data={{
                labels: visibleTrendPoints.map((point) => point.label),
                datasets: [
                  {
                    label: "Events",
                    data: visibleTrendPoints.map((point) => point.events),
                    borderColor: editorial.gold,
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    tension: 0.32,
                    fill: true,
                    backgroundColor: "rgba(212, 175, 55, 0.12)",
                  },
                ],
              }}
            />
          </div>
        </article>

        <article className="chart-card">
          <div className="card-heading">
            <p>Stage volume</p>
            <span>Grouped recruiting steps</span>
          </div>
          <div className="chart-frame compact">
            <Bar
              options={baseChartOptions({ categoryLabels: stageEntries.map(([stage]) => stageLabels[stage]) })}
              data={{
                labels: stageEntries.map(([stage]) => stageLabels[stage]),
                datasets: [
                  {
                    label: "Logs",
                    data: stageEntries.map(([, count]) => count),
                    backgroundColor: "rgba(249, 248, 246, 0.82)",
                    hoverBackgroundColor: editorial.gold,
                    borderColor: "rgba(249, 248, 246, 0.18)",
                    borderWidth: 1,
                    borderRadius: 0,
                    maxBarThickness: 42,
                  },
                ],
              }}
            />
          </div>
        </article>

        <article className="chart-card">
          <div className="card-heading">
            <p>Process ledger</p>
            <span>OA through offer</span>
          </div>
          <StageIndex distribution={overview?.stage_distribution || {}} />
        </article>

        <ProcessReadout overview={overview} stageEntries={stageEntries} />
      </div>
    </section>
  );
}

function CompanyModal({ data, track, onClose }) {
  return (
    <div className="modal-layer">
      <button className="modal-scrim" type="button" aria-label="Close company detail" onClick={onClose} />
      <section className="company-modal" aria-modal="true" role="dialog">
        <div className="modal-header">
          <div>
            <p className="eyebrow">{humanize(track)} company dossier</p>
            <h2>{data.company}</h2>
          </div>
          <SecondaryButton onClick={onClose}>Close</SecondaryButton>
        </div>

        <div className="modal-metrics">
          <EditorialMetric label="Events" value={data.total_events} note="Company process logs" />
          <EditorialMetric label="Candidates" value={data.total_candidates} note="Unique candidate IDs" />
          <EditorialMetric label="Offers" value={data.offers} note="Positive final outcomes" />
          <EditorialMetric label="Latest" value={formatDate(data.latest_activity)} note="Most recent activity" />
        </div>

        <div className="modal-body">
          <article className="modal-section">
            <h3 className="modal-section-title">Company Process</h3>
            <StageIndex distribution={data.stage_distribution || {}} />
          </article>
          <article className="modal-section">
            <h3 className="modal-section-title">Final Outcomes</h3>
            <OutcomeLedger distribution={data.outcome_distribution || {}} />
          </article>
        </div>
      </section>
    </div>
  );
}

export default function App() {
  const [overview, setOverview] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [track, setTrack] = useState("all");
  const [status, setStatus] = useState("Loading dashboard...");
  const [searchValue, setSearchValue] = useState("");
  const [selectedCompany, setSelectedCompany] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function loadDashboard() {
      setStatus(`Loading ${humanize(track).toLowerCase()} data...`);
      try {
        const [overviewData, companyData] = await Promise.all([
          fetchJson(`/api/dashboard/overview?employment_type=${track}`),
          fetchJson("/api/companies"),
        ]);
        if (cancelled) return;
        setOverview(overviewData);
        setCompanies(companyData);
        setStatus(`Showing ${humanize(track).toLowerCase()} aggregate process data.`);
      } catch (error) {
        if (!cancelled) {
          setStatus("Could not reach the dashboard API. Start FastAPI on port 8000 or use the production app.");
        }
      }
    }
    loadDashboard();
    return () => {
      cancelled = true;
    };
  }, [track]);

  const metrics = useMemo(() => {
    const outcomes = outcomeCounts(overview?.outcome_distribution);
    return [
      ["Events", overview?.total_events ?? "—", "All logged process updates"],
      ["Candidates", overview?.total_candidates ?? "—", "Unique Discord users"],
      ["Companies", overview?.total_companies ?? "—", "Employers in the index"],
      ["Offers", outcomes.offers, "Positive final outcomes"],
    ];
  }, [overview]);

  async function openCompany(companyName) {
    if (!companyName.trim()) {
      setStatus("Type a company name, then open its process dossier.");
      return;
    }
    const match = companies.find((company) => company.name.toLowerCase() === companyName.trim().toLowerCase());
    if (!match) {
      setStatus("Company not found. Choose a company already present in the process index.");
      return;
    }
    try {
      setStatus(`Opening ${match.name}...`);
      const companyData = await fetchJson(`/api/dashboard/company/${match.slug}?employment_type=${track}`);
      if (!companyData.total_events) {
        setStatus(`No ${humanize(track).toLowerCase()} process data is available for ${match.name} yet.`);
        return;
      }
      setSelectedCompany(companyData);
      setStatus(`Opened ${match.name}.`);
    } catch (error) {
      setStatus("Unable to load that company right now.");
    }
  }

  function handleSearch(event) {
    event.preventDefault();
    openCompany(searchValue);
  }

  return (
    <>
      <GravityStarsBackground className="app-stars" starColor={editorial.gold} />
      <NoiseOverlay />
      <div className="site-shell">
        <Header
          track={track}
          setTrack={(nextTrack) => {
            setTrack(nextTrack);
            setSelectedCompany(null);
          }}
          companies={companies}
          searchValue={searchValue}
          setSearchValue={setSearchValue}
          onSearch={handleSearch}
          status={status}
        />

        <main>
          <Hero overview={overview} />

          <section className="metrics-strip" aria-label="Dashboard metrics">
            {metrics.map(([label, value, note]) => (
              <EditorialMetric key={label} label={label} value={value} note={note} />
            ))}
          </section>

          <ChartPanel overview={overview} />

          <section className="ledger-section" id="companies">
            <div className="section-heading light">
              <div>
                <p className="eyebrow">Company Intelligence</p>
                <h2>Where the community is seeing motion.</h2>
              </div>
            </div>

            <div className="ledger-grid">
              <article className="ledger-card">
                <p className="eyebrow">Top Companies</p>
                <TopCompanies companies={overview?.top_companies || []} onOpen={openCompany} />
              </article>
              <article className="ledger-card" id="outcomes">
                <p className="eyebrow">Outcome Ledger</p>
                <OutcomeLedger distribution={overview?.outcome_distribution || {}} />
              </article>
              <article className="ledger-card">
                <p className="eyebrow">Recent Offers</p>
                <RecentOffers offers={overview?.recent_offers || []} />
              </article>
            </div>
          </section>
        </main>

        <footer className="site-footer">
          <span>ProcTracker</span>
          <a href="https://discord.gg/cscareers" target="_blank" rel="noreferrer">
            Join the CS Careers Discord
          </a>
        </footer>
      </div>

      {selectedCompany ? (
        <CompanyModal data={selectedCompany} track={track} onClose={() => setSelectedCompany(null)} />
      ) : null}
    </>
  );
}
