import React, { useEffect, useMemo, useState } from "react";
import { Bar, Doughnut, Line } from "react-chartjs-2";

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

const tracks = [
  { id: "all", label: "All" },
  { id: "intern", label: "Intern" },
  { id: "full_time", label: "Full Time" },
];

const palette = {
  pine: "#1a5d52",
  brass: "#c99641",
  blush: "#b86a73",
  slate: "#6777a7",
  ink: "#171717",
  muted: "#6b6962",
  set: ["#1a5d52", "#c99641", "#b86a73", "#6777a7", "#171717"],
};

function humanize(value) {
  const label = value === "full_time" ? "Full Time" : value;
  return label
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function canonicalStage(stage) {
  return stage === "onsite" ? "technical" : stage;
}

function groupCounts(values) {
  return values.reduce((acc, value) => {
    acc[value] = (acc[value] || 0) + 1;
    return acc;
  }, {});
}

function sortEntries(record) {
  return Object.entries(record).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}

function Card({ title, kicker, children, className = "" }) {
  return (
    <article className={`rounded-2xl border border-black/5 bg-white/85 p-4 shadow-panel backdrop-blur animate-rise ${className}`}>
      <div className="mb-3 flex items-end justify-between gap-3">
        <div>
          <p className="mb-1 text-[0.65rem] font-bold uppercase tracking-[0.18em] text-stone-500">{kicker}</p>
          <h2 className="text-base font-semibold text-ink">{title}</h2>
        </div>
      </div>
      {children}
    </article>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-2xl border border-black/5 bg-white/90 p-4 shadow-panel animate-rise">
      <p className="mb-2 text-[0.65rem] font-bold uppercase tracking-[0.18em] text-stone-500">{label}</p>
      <p className="text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function chartOptions({ legend = true, horizontal = false, compact = false } = {}) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: horizontal ? "y" : "x",
    plugins: {
      legend: {
        display: legend,
        labels: {
          color: palette.muted,
          boxWidth: 8,
          usePointStyle: true,
          font: { family: "Avenir Next", size: 11 },
        },
      },
      tooltip: {
        backgroundColor: "rgba(23, 23, 23, 0.92)",
        titleColor: "#ffffff",
        bodyColor: "#ffffff",
        padding: 10,
      },
    },
    scales: {
      x: {
        ticks: { color: palette.muted, font: { size: compact ? 9 : 10 } },
        grid: { display: false },
        border: { display: false },
      },
      y: {
        beginAtZero: true,
        ticks: { color: palette.muted, precision: 0, font: { size: compact ? 9 : 10 } },
        grid: { color: "rgba(23,23,23,0.06)" },
        border: { display: false },
      },
    },
  };
}

function buildOverview(events) {
  const stageCounts = groupCounts(events.map((event) => canonicalStage(event.stage)));
  const outcomeCounts = groupCounts(events.filter((event) => event.outcome).map((event) => event.outcome));
  const companyCounts = groupCounts(events.map((event) => event.company));
  const employmentCounts = groupCounts(events.filter((event) => event.employment_type).map((event) => event.employment_type));
  const trendCounts = events.reduce((acc, event) => {
    const day = new Date(event.occurred_at).toISOString().slice(0, 10);
    acc[day] = (acc[day] || 0) + 1;
    return acc;
  }, {});

  return {
    totalEvents: events.length,
    totalCandidates: new Set(events.map((event) => event.username)).size,
    totalCompanies: new Set(events.map((event) => event.company_slug)).size,
    offers: outcomeCounts.offered || 0,
    stageCounts,
    outcomeCounts,
    companyCounts,
    employmentCounts,
    trendPoints: Object.entries(trendCounts)
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([date, count]) => ({ date, count })),
  };
}

function filterEvents(events, track) {
  if (track === "all") {
    return events;
  }
  return events.filter((event) => event.employment_type === track);
}

function CompanyModal({ company, track, onClose, data }) {
  const stageEntries = sortEntries(data.stage_distribution || {});
  const outcomeEntries = sortEntries(data.outcome_distribution || {});
  const funnelPercentages = data.funnel_points || [];

  return (
    <div className="fixed inset-0 z-30">
      <button className="absolute inset-0 bg-black/35" aria-label="Close modal" onClick={onClose} />
      <section className="relative z-10 mx-auto my-3 max-h-[calc(100vh-24px)] w-[min(980px,calc(100%-24px))] overflow-auto rounded-3xl border border-black/5 bg-white/95 p-4 shadow-panel backdrop-blur">
        <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="mb-1 text-[0.65rem] font-bold uppercase tracking-[0.18em] text-stone-500">ProcTracker</p>
            <h2 className="text-2xl font-semibold text-ink">{company.name}</h2>
            <p className="text-sm text-stone-500">{humanize(track)} view</p>
          </div>
          <button className="rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white" onClick={onClose}>Close</button>
        </div>

        <div className="mb-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="Company" value={company.name} />
          <Metric label="Events" value={data.total_events} />
          <Metric label="Candidates" value={data.total_candidates} />
          <Metric label="Offers" value={data.offers} />
          <Metric label="Latest" value={data.latest_activity ? new Date(data.latest_activity).toLocaleDateString() : "—"} />
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <Card kicker="Company" title="Activity" className="xl:col-span-2">
            <div className="h-48">
              <Line
                options={chartOptions({ legend: false, compact: true })}
                data={{
                  labels: (data.trend_points || []).map((point) => point.period_start),
                  datasets: [
                    {
                      label: "Events",
                      data: (data.trend_points || []).map((point) => point.events),
                      borderColor: palette.slate,
                      borderWidth: 2,
                      pointRadius: 0,
                      tension: 0.35,
                      fill: true,
                      backgroundColor: "rgba(103,119,167,0.15)",
                    },
                  ],
                }}
              />
            </div>
          </Card>

          <Card kicker="Company" title="Stage mix">
            <div className="h-48">
              <Doughnut
                options={{ ...chartOptions(), cutout: "70%", scales: undefined }}
                data={{
                  labels: stageEntries.length ? stageEntries.map(([label]) => humanize(label)) : ["No stage data"],
                  datasets: [{ data: stageEntries.length ? stageEntries.map(([, count]) => count) : [1], backgroundColor: stageEntries.length ? palette.set : ["rgba(23,23,23,0.08)"], borderWidth: 0 }],
                }}
              />
            </div>
          </Card>

          <Card kicker="Company" title="Outcome mix">
            <div className="h-48">
              <Doughnut
                options={{ ...chartOptions(), cutout: "70%", scales: undefined }}
                data={{
                  labels: outcomeEntries.length ? outcomeEntries.map(([label]) => humanize(label)) : ["No outcome data"],
                  datasets: [{ data: outcomeEntries.length ? outcomeEntries.map(([, count]) => count) : [1], backgroundColor: outcomeEntries.length ? palette.set : ["rgba(23,23,23,0.08)"], borderWidth: 0 }],
                }}
              />
            </div>
          </Card>

          <Card kicker="Company" title="Funnel progression" className="md:col-span-2 xl:col-span-2">
            <div className="h-48">
              <Line
                options={{
                  ...chartOptions({ legend: false, compact: true }),
                  scales: {
                    x: {
                      ticks: { color: palette.muted, font: { size: 10 } },
                      grid: { display: false },
                      border: { display: false },
                    },
                    y: {
                      beginAtZero: true,
                      suggestedMax: 100,
                      ticks: {
                        color: palette.muted,
                        callback: (value) => `${value}%`,
                        font: { size: 10 },
                      },
                      grid: { color: "rgba(23,23,23,0.06)" },
                      border: { display: false },
                    },
                  },
                }}
                data={{
                  labels: funnelPercentages.length ? funnelPercentages.map((step) => step.label) : ["No funnel data"],
                  datasets: [
                    {
                      label: "Progression",
                      data: funnelPercentages.length ? funnelPercentages.map((step) => step.value) : [0],
                      borderColor: palette.pine,
                      borderWidth: 2.5,
                      pointRadius: 4,
                      pointHoverRadius: 5,
                      pointBackgroundColor: palette.pine,
                      tension: 0.28,
                      fill: false,
                    },
                  ],
                }}
              />
            </div>
          </Card>
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
    async function load() {
      try {
        const [overviewData, companyData] = await Promise.all([
          fetchJson(`/api/dashboard/overview?employment_type=${track}`),
          fetchJson("/api/companies"),
        ]);
        setOverview(overviewData);
        setCompanies(companyData);
        setStatus(`Showing ${humanize(track).toLowerCase()} activity. Search a company to open its popup.`);
      } catch (error) {
        setStatus("Dashboard data could not be loaded.");
      }
    }
    load();
  }, [track]);

  const stageEntries = useMemo(
    () => sortEntries(overview?.stage_distribution || {}),
    [overview]
  );
  const outcomeEntries = useMemo(
    () => sortEntries(overview?.outcome_distribution || {}),
    [overview]
  );
  const companyEntries = useMemo(
    () => (overview?.top_companies || []).map((entry) => [entry.label, entry.value]),
    [overview]
  );
  const employmentEntries = useMemo(
    () => sortEntries(overview?.employment_distribution || {}),
    [overview]
  );

  async function handleSubmit(event) {
    event.preventDefault();
    const match = companies.find((company) => company.name.toLowerCase() === searchValue.trim().toLowerCase());
    if (!match) {
      setStatus("Company not found. Choose one of the tracked company names from the suggestions.");
      return;
    }
    try {
      const companyData = await fetchJson(`/api/dashboard/company/${match.slug}?employment_type=${track}`);
      if (!companyData.total_events) {
        setStatus(`No ${humanize(track).toLowerCase()} data is available for ${match.name} yet.`);
        return;
      }
      setSelectedCompany(companyData);
      setStatus(`Opened ${match.name} in ${humanize(track).toLowerCase()} view.`);
    } catch (error) {
      setStatus("Unable to load that company right now.");
    }
  }

  return (
    <>
      <main className="mx-auto w-[min(1180px,calc(100%-24px))] py-5">
        <header className="mb-3 grid gap-3 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
          <section className="rounded-2xl border border-black/5 bg-white/88 p-5 shadow-panel">
            <p className="mb-1 text-[0.68rem] font-bold uppercase tracking-[0.18em] text-stone-500">ProcTracker</p>
            <h1 className="mb-2 text-4xl font-semibold leading-none tracking-tight text-ink sm:text-5xl">Recruiting signals in one compact view.</h1>
            <p className="max-w-2xl text-sm leading-6 text-stone-500">Switch between tracks, compare trends quickly, and open a company popup only when you need a deeper read.</p>
          </section>

          <section className="rounded-2xl border border-black/5 bg-white/96 p-4 shadow-panel">
            <div className="mb-3 inline-flex gap-1 rounded-full bg-black/[0.04] p-1">
              {tracks.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    setTrack(item.id);
                    setSelectedCompany(null);
                    setStatus(`Loading ${humanize(item.id).toLowerCase()} activity...`);
                  }}
                  className={`rounded-full px-3 py-2 text-sm font-semibold transition ${track === item.id ? "bg-ink text-white" : "text-stone-500 hover:bg-black/[0.05] hover:text-ink"}`}
                >
                  {item.label}
                </button>
              ))}
            </div>

            <form className="grid grid-cols-[1fr_auto] gap-2" onSubmit={handleSubmit}>
              <input
                id="company-search-input"
                list="company-options"
                value={searchValue}
                onChange={(event) => setSearchValue(event.target.value)}
                placeholder="Search company"
                className="rounded-xl border border-black/10 bg-white px-3 py-3 text-sm outline-none transition focus:border-pine"
              />
              <datalist id="company-options">
                {companies.map((company) => (
                  <option key={company.slug} value={company.name} />
                ))}
              </datalist>
              <button type="submit" className="rounded-xl bg-pine px-4 py-3 text-sm font-semibold text-white">Open</button>
            </form>
          </section>
        </header>

        <p className="mb-3 min-h-5 text-sm text-stone-500">{status}</p>

        <section className="mb-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Metric label="Events" value={overview?.total_events ?? "—"} />
          <Metric label="Candidates" value={overview?.total_candidates ?? "—"} />
          <Metric label="Companies" value={overview?.total_companies ?? "—"} />
          <Metric label="Offers" value={overview?.offers ?? "—"} />
        </section>

        <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <Card kicker="Overview" title="Activity trend" className="xl:col-span-2">
            <div className="h-44">
              <Line
                options={chartOptions({ legend: false, compact: true })}
                data={{
                  labels: overview?.trend_points?.map((point) => point.period_start) || [],
                  datasets: [
                    {
                      label: "Events",
                      data: overview?.trend_points?.map((point) => point.events) || [],
                      borderColor: palette.pine,
                      borderWidth: 2,
                      pointRadius: 0,
                      tension: 0.35,
                      fill: true,
                      backgroundColor: "rgba(26,93,82,0.14)",
                    },
                  ],
                }}
              />
            </div>
          </Card>

          <Card kicker="Overview" title="Top companies">
            <div className="h-44">
              <Bar
                options={chartOptions({ legend: false, horizontal: true, compact: true })}
                data={{
                  labels: companyEntries.map(([label]) => label),
                  datasets: [{ label: "Events", data: companyEntries.map(([, count]) => count), backgroundColor: palette.pine, borderRadius: 8, maxBarThickness: 18 }],
                }}
              />
            </div>
          </Card>

          <Card kicker="Overview" title="Stage mix">
            <div className="h-44">
              <Doughnut
                options={{ ...chartOptions(), cutout: "72%", scales: undefined }}
                data={{
                  labels: stageEntries.length ? stageEntries.map(([label]) => humanize(label)) : ["No stage data"],
                  datasets: [{ data: stageEntries.length ? stageEntries.map(([, count]) => count) : [1], backgroundColor: stageEntries.length ? palette.set : ["rgba(23,23,23,0.08)"], borderWidth: 0 }],
                }}
              />
            </div>
          </Card>

          <Card kicker="Overview" title="Outcome mix">
            <div className="h-44">
              <Doughnut
                options={{ ...chartOptions(), cutout: "72%", scales: undefined }}
                data={{
                  labels: outcomeEntries.length ? outcomeEntries.map(([label]) => humanize(label)) : ["No outcome data"],
                  datasets: [{ data: outcomeEntries.length ? outcomeEntries.map(([, count]) => count) : [1], backgroundColor: outcomeEntries.length ? palette.set : ["rgba(23,23,23,0.08)"], borderWidth: 0 }],
                }}
              />
            </div>
          </Card>

          <Card kicker="Overview" title="Track split">
            <div className="h-44">
              <Bar
                options={chartOptions({ legend: false, compact: true })}
                data={{
                  labels: employmentEntries.map(([label]) => humanize(label)),
                  datasets: [{ label: "Events", data: employmentEntries.map(([, count]) => count), backgroundColor: palette.slate, borderRadius: 8, maxBarThickness: 24 }],
                }}
              />
            </div>
          </Card>
        </section>
      </main>

      {selectedCompany ? (
        <CompanyModal
          company={{ name: selectedCompany.company }}
          events={[]}
          track={track}
          onClose={() => setSelectedCompany(null)}
          data={selectedCompany}
        />
      ) : null}
    </>
  );
}
