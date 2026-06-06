import React, { useEffect, useMemo, useState } from "react";
import { Bar, Line } from "react-chartjs-2";

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
  slate: "#6777a7",
  ink: "#171717",
  muted: "#6b6962",
};

function humanize(value) {
  const label = value === "full_time" ? "Full Time" : value;
  return label
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function sortEntries(record) {
  return Object.entries(record).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}

function Card({ title, note, children, className = "" }) {
  return (
    <article className={`rounded-lg border border-stone-200 bg-white p-4 shadow-panel ${className}`}>
      <div className="mb-4">
        <h2 className="text-base font-semibold text-ink">{title}</h2>
        {note ? <p className="mt-1 text-sm text-stone-500">{note}</p> : null}
      </div>
      {children}
    </article>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-stone-200 bg-white p-4 shadow-panel">
      <p className="text-sm text-stone-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function FunnelStagePill({ label, value }) {
  return (
    <div className="rounded-lg border border-stone-200 bg-stone-50 px-3 py-2">
      <p className="text-sm text-stone-500">{label}</p>
      <p className="mt-1 text-base font-semibold text-ink">{value}%</p>
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
        ticks: { color: palette.muted, font: { size: compact ? 10 : 11 } },
        grid: { display: false },
        border: { display: false },
      },
      y: {
        beginAtZero: true,
        ticks: { color: palette.muted, precision: 0, font: { size: compact ? 10 : 11 } },
        grid: { color: "rgba(23,23,23,0.08)" },
        border: { display: false },
      },
    },
  };
}

function TrackSplitPanel({ entries }) {
  const total = entries.reduce((sum, [, count]) => sum + count, 0);
  const displayEntries = entries.length ? entries : [["No track data", 0]];

  return (
    <div className="space-y-4">
      {displayEntries.map(([label, count]) => {
        const percent = total ? Math.round((count / total) * 100) : 0;
        return (
          <div key={label} className="space-y-2">
            <div className="flex items-baseline justify-between gap-3">
              <span className="text-sm font-semibold text-ink">{humanize(label)}</span>
              <span className="font-mono text-xs text-stone-500">
                {total ? `${percent}%` : "empty"}
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-sm bg-stone-100">
              <div
                className="h-full rounded-sm bg-pine"
                style={{ width: `${Math.max(percent, total ? 7 : 0)}%` }}
              />
            </div>
            <p className="text-xs text-stone-500">{count} logged event{count === 1 ? "" : "s"}</p>
          </div>
        );
      })}
    </div>
  );
}

function RecentOffersPanel({ offers }) {
  if (!offers?.length) {
    return (
      <div className="rounded-lg border border-dashed border-stone-300 bg-stone-50 px-4 py-5 text-sm text-stone-500">
        No offers logged yet.
      </div>
    );
  }

  return (
    <div className="divide-y divide-stone-200 overflow-hidden rounded-lg border border-stone-200">
      {offers.map((offer, index) => (
        <div
          key={`${offer.company_slug}-${offer.occurred_at}-${index}`}
          className="px-3 py-2.5"
        >
          <span className="text-sm font-semibold text-ink">{offer.company}</span>
        </div>
      ))}
    </div>
  );
}

function DistributionList({ entries, emptyLabel = "No data yet" }) {
  const total = entries.reduce((sum, [, count]) => sum + count, 0);
  if (!entries.length) {
    return <p className="rounded-lg border border-dashed border-stone-300 bg-stone-50 p-4 text-sm text-stone-500">{emptyLabel}</p>;
  }

  return (
    <div className="divide-y divide-stone-200 rounded-lg border border-stone-200">
      {entries.map(([label, count]) => {
        const percent = total ? Math.round((count / total) * 100) : 0;
        return (
          <div key={label} className="grid grid-cols-[minmax(0,1fr)_auto] gap-3 px-3 py-2.5">
            <div>
              <p className="text-sm font-medium text-ink">{humanize(label)}</p>
              <div className="mt-2 h-1.5 overflow-hidden rounded-sm bg-stone-100">
                <div className="h-full rounded-sm bg-pine" style={{ width: `${Math.max(percent, 4)}%` }} />
              </div>
            </div>
            <div className="text-right">
              <p className="font-mono text-sm text-ink">{count}</p>
              <p className="font-mono text-xs text-stone-500">{percent}%</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function CompanyModal({ company, track, onClose, data }) {
  const stageEntries = sortEntries(data.stage_distribution || {});
  const outcomeEntries = sortEntries(data.outcome_distribution || {});
  const funnelPercentages = data.funnel_points || [];

  return (
    <div className="fixed inset-0 z-30">
      <button className="absolute inset-0 bg-black/35" aria-label="Close modal" onClick={onClose} />
      <section className="relative z-10 mx-auto my-4 max-h-[calc(100vh-32px)] w-[min(1040px,calc(100%-24px))] overflow-auto rounded-lg border border-stone-200 bg-white p-5 shadow-panel">
        <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-ink">{company.name}</h2>
            <p className="text-sm text-stone-500">{humanize(track)} view</p>
          </div>
          <button className="rounded-md bg-ink px-3 py-2 text-sm font-semibold text-white" onClick={onClose}>Close</button>
        </div>

        <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <Metric label="Company" value={company.name} />
          <Metric label="Events" value={data.total_events} />
          <Metric label="Candidates" value={data.total_candidates} />
          <Metric label="Offers" value={data.offers} />
          <Metric label="Latest" value={data.latest_activity ? new Date(data.latest_activity).toLocaleDateString() : "—"} />
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <Card title="Activity" className="xl:col-span-2">
            <div className="h-56">
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

          <Card title="Stage mix">
            <DistributionList entries={stageEntries} emptyLabel="No stage data" />
          </Card>

          <Card title="Outcome mix">
            <DistributionList entries={outcomeEntries} emptyLabel="No outcome data" />
          </Card>

          <Card title="Funnel progression" className="md:col-span-2 xl:col-span-2">
            <div className="rounded-lg border border-stone-200 bg-stone-50 p-3">
              <div className="mb-3 flex items-center justify-between">
                <p className="text-sm font-medium text-ink">Candidate progression</p>
                <p className="text-xs text-stone-500">Percent of funnel</p>
              </div>
              <div className="h-48">
              <Line
                options={{
                  ...chartOptions({ legend: false, compact: true }),
                  interaction: {
                    intersect: false,
                    mode: "index",
                  },
                  scales: {
                    x: {
                      ticks: { color: palette.muted, font: { size: 11, weight: "600" }, maxRotation: 0, minRotation: 0 },
                      grid: { display: false },
                      border: { display: false },
                    },
                    y: {
                      beginAtZero: true,
                      max: 100,
                      ticks: {
                        color: palette.muted,
                        callback: (value) => `${value}%`,
                        stepSize: 25,
                        font: { size: 10 },
                      },
                      grid: { color: "rgba(23,23,23,0.08)" },
                      border: { display: false },
                    },
                  },
                  plugins: {
                    ...chartOptions({ legend: false, compact: true }).plugins,
                    tooltip: {
                      ...chartOptions({ legend: false, compact: true }).plugins.tooltip,
                      callbacks: {
                        label: (context) => `${context.raw}%`,
                      },
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
                      borderWidth: 4,
                      pointRadius: 0,
                      pointHoverRadius: 6,
                      pointBackgroundColor: "#ffffff",
                      pointBorderColor: palette.pine,
                      pointBorderWidth: 3,
                      stepped: "before",
                      fill: true,
                      backgroundColor: "rgba(26,93,82,0.16)",
                      tension: 0,
                    },
                  ],
                }}
              />
              </div>
              {funnelPercentages.length ? (
                <div className="mt-3 grid gap-2 sm:grid-cols-3 lg:grid-cols-5">
                  {funnelPercentages.map((step) => (
                    <FunnelStagePill key={step.label} label={step.label} value={step.value} />
                  ))}
                </div>
              ) : null}
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
      <main className="mx-auto w-[min(1240px,calc(100%-28px))] py-6">
        <header className="mb-4 grid gap-4 lg:grid-cols-[1.15fr_0.85fr] lg:items-stretch">
          <section className="rounded-lg border border-stone-200 bg-white p-5 shadow-panel">
            <h1 className="text-2xl font-semibold text-ink">Process dashboard</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-500">Aggregate recruiting activity from Discord. Individual process history stays private.</p>
          </section>

          <section className="rounded-lg border border-stone-200 bg-white p-5 shadow-panel">
            <div className="mb-3 flex gap-2">
              {tracks.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    setTrack(item.id);
                    setSelectedCompany(null);
                    setStatus(`Loading ${humanize(item.id).toLowerCase()} activity...`);
                  }}
                  className={`rounded-md border px-3 py-2 text-sm font-medium transition-colors ${track === item.id ? "border-ink bg-ink text-white" : "border-stone-200 bg-white text-stone-600 hover:border-stone-300 hover:text-ink"}`}
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
                className="rounded-md border border-stone-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-pine focus:ring-2 focus:ring-pine/15"
              />
              <datalist id="company-options">
                {companies.map((company) => (
                  <option key={company.slug} value={company.name} />
                ))}
              </datalist>
              <button type="submit" className="rounded-md bg-pine px-4 py-2.5 text-sm font-semibold text-white">Open</button>
            </form>
          </section>
        </header>

        <p className="mb-4 min-h-5 text-sm text-stone-500">{status}</p>

        <section className="mb-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Metric label="Events" value={overview?.total_events ?? "—"} />
          <Metric label="Candidates" value={overview?.total_candidates ?? "—"} />
          <Metric label="Companies" value={overview?.total_companies ?? "—"} />
          <Metric label="Offers" value={overview?.offers ?? "—"} />
        </section>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <Card title="Activity trend" className="xl:col-span-2">
            <div className="h-60">
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

          <Card title="Top companies">
            <div className="h-60">
              <Bar
                options={chartOptions({ legend: false, horizontal: true, compact: true })}
                data={{
                  labels: companyEntries.map(([label]) => label),
                  datasets: [{ label: "Events", data: companyEntries.map(([, count]) => count), backgroundColor: palette.pine, borderRadius: 8, maxBarThickness: 18 }],
                }}
              />
            </div>
          </Card>

          <Card title="Track split">
            <TrackSplitPanel entries={employmentEntries} />
          </Card>

          <Card title="Stage mix">
            <DistributionList entries={stageEntries} emptyLabel="No stage data" />
          </Card>

          <Card title="Outcome mix">
            <DistributionList entries={outcomeEntries} emptyLabel="No outcome data" />
          </Card>

          <Card title="Recent offers">
            <RecentOffersPanel offers={overview?.recent_offers || []} />
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
