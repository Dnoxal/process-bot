from __future__ import annotations

import csv
from dataclasses import dataclass
from importlib import resources
import re


@dataclass(frozen=True, slots=True)
class CompanyRegistryEntry:
    id: str
    display_name: str
    aliases: tuple[str, ...] = ()
    category: str = "Other"
    active: bool = True


def company_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _entry(display_name: str, category: str, aliases: tuple[str, ...] = ()) -> CompanyRegistryEntry:
    return CompanyRegistryEntry(
        id=company_key(display_name),
        display_name=display_name,
        aliases=aliases,
        category=category,
    )


MANUAL_COMPANY_REGISTRY: tuple[CompanyRegistryEntry, ...] = (
    _entry("Google", "Big Tech / Consumer", ("goog", "ggl", "alphabet")),
    _entry("Meta", "Big Tech / Consumer", ("facebook", "fb")),
    _entry("Apple", "Big Tech / Consumer", ("aapl", "appl")),
    _entry("Microsoft", "Big Tech / Consumer", ("msft",)),
    _entry("Amazon", "Big Tech / Consumer", ("amzn", "amazonn", "zon")),
    _entry("Netflix", "Big Tech / Consumer", ("nflx",)),
    _entry("NVIDIA", "Big Tech / Consumer", ("nvda", "nvidia corporation")),
    _entry("Tesla", "Big Tech / Consumer", ("tsla",)),
    _entry("Adobe", "Big Tech / Consumer", ("adbe",)),
    _entry("Salesforce", "Big Tech / Consumer", ("sfdc",)),
    _entry("Oracle", "Big Tech / Consumer", ("orcl",)),
    _entry("Cisco", "Big Tech / Consumer", ("csco",)),
    _entry("Intel", "Big Tech / Consumer", ("intc",)),
    _entry("AMD", "Big Tech / Consumer", ("advanced micro devices",)),
    _entry("Qualcomm", "Big Tech / Consumer", ("qcom",)),
    _entry("IBM", "Big Tech / Consumer", ("international business machines",)),
    _entry("HP", "Big Tech / Consumer", ("hewlett packard", "hp inc")),
    _entry("Dell Technologies", "Big Tech / Consumer", ("dell",)),
    _entry("Broadcom", "Big Tech / Consumer", ("avgo",)),
    _entry("Samsung Electronics", "Big Tech / Consumer", ("samsung",)),
    _entry("Sony", "Big Tech / Consumer", ()),
    _entry("TikTok", "Big Tech / Consumer", ("tt",)),
    _entry("ByteDance", "Big Tech / Consumer", ("bytedance", "byte dance")),
    _entry("Snap", "Big Tech / Consumer", ("snapchat",)),
    _entry("Pinterest", "Big Tech / Consumer", ("pin", "pins", "pint")),
    _entry("Reddit", "Big Tech / Consumer", ()),
    _entry("Discord", "Big Tech / Consumer", ()),
    _entry("LinkedIn", "Big Tech / Consumer", ("linkedin",)),
    _entry("Uber", "Big Tech / Consumer", ()),
    _entry("Lyft", "Big Tech / Consumer", ()),
    _entry("Airbnb", "Big Tech / Consumer", ()),
    _entry("DoorDash", "Big Tech / Consumer", ("doordash", "dd")),
    _entry("Instacart", "Big Tech / Consumer", ("insta",)),
    _entry("Coinbase", "Big Tech / Consumer", ()),
    _entry("Dropbox", "Big Tech / Consumer", ()),
    _entry("eBay", "Big Tech / Consumer", ()),
    _entry("PayPal", "Big Tech / Consumer", ()),
    _entry("Square", "Big Tech / Consumer", ()),
    _entry("Block", "Big Tech / Consumer", ("sq",)),
    _entry("Shopify", "Big Tech / Consumer", ()),
    _entry("Canva", "Big Tech / Consumer", ()),
    _entry("Spotify", "Big Tech / Consumer", ()),
    _entry("Roblox", "Big Tech / Consumer", ()),
    _entry("Electronic Arts", "Big Tech / Consumer", ("ea",)),
    _entry("Epic Games", "Big Tech / Consumer", ("epic",)),
    _entry("Unity", "Big Tech / Consumer", ("unity technologies",)),
    _entry("Riot Games", "Big Tech / Consumer", ("riot",)),
    _entry("Valve", "Big Tech / Consumer", ("valve software",)),
    _entry("Blizzard Entertainment", "Big Tech / Consumer", ("blizzard",)),
    _entry("Jane Street", "Quant / HFT / Prop Trading", ("js",)),
    _entry("Citadel", "Quant / HFT / Prop Trading", ()),
    _entry("Citadel Securities", "Quant / HFT / Prop Trading", ("citsec",)),
    _entry("Hudson River Trading", "Quant / HFT / Prop Trading", ("hrt",)),
    _entry("Jump Trading", "Quant / HFT / Prop Trading", ("jump",)),
    _entry("IMC Trading", "Quant / HFT / Prop Trading", ("imc",)),
    _entry("Optiver", "Quant / HFT / Prop Trading", ()),
    _entry("DRW", "Quant / HFT / Prop Trading", ()),
    _entry("Susquehanna International Group", "Quant / HFT / Prop Trading", ("sig",)),
    _entry("Akuna Capital", "Quant / HFT / Prop Trading", ("akuna",)),
    _entry("Tower Research Capital", "Quant / HFT / Prop Trading", ("tower research",)),
    _entry("Two Sigma", "Quant / HFT / Prop Trading", ("2s",)),
    _entry("Five Rings", "Quant / HFT / Prop Trading", ()),
    _entry("Flow Traders", "Quant / HFT / Prop Trading", ()),
    _entry("Maven Securities", "Quant / HFT / Prop Trading", ("maven",)),
    _entry("Old Mission", "Quant / HFT / Prop Trading", ("old mission capital",)),
    _entry("Belvedere Trading", "Quant / HFT / Prop Trading", ()),
    _entry("Chicago Trading Company", "Quant / HFT / Prop Trading", ("ctc",)),
    _entry("Geneva Trading", "Quant / HFT / Prop Trading", ()),
    _entry("Group One Trading", "Quant / HFT / Prop Trading", ("group one",)),
    _entry("XR Trading", "Quant / HFT / Prop Trading", ()),
    _entry("Headlands Technologies", "Quant / HFT / Prop Trading", ("headlands",)),
    _entry("Aquatic Capital Management", "Quant / HFT / Prop Trading", ("aquatic",)),
    _entry("PDT Partners", "Quant / HFT / Prop Trading", ("pdt",)),
    _entry("Radix Trading", "Quant / HFT / Prop Trading", ("radix",)),
    _entry("Sun Trading", "Quant / HFT / Prop Trading", ()),
    _entry("Valkyrie Trading", "Quant / HFT / Prop Trading", ()),
    _entry("Virtu Financial", "Quant / HFT / Prop Trading", ("virtu",)),
    _entry("Tradeweb", "Quant / HFT / Prop Trading", ()),
    _entry("GTS", "Quant / HFT / Prop Trading", ()),
    _entry("Cumberland", "Quant / HFT / Prop Trading", ()),
    _entry("Wintermute", "Quant / HFT / Prop Trading", ()),
    _entry("Bridgewater Associates", "Hedge Funds", ("bridgewater",)),
    _entry("Point72", "Hedge Funds", ("p72",)),
    _entry("Millennium Management", "Hedge Funds", ("millennium",)),
    _entry("DE Shaw", "Hedge Funds", ("d e shaw", "deshaw")),
    _entry("AQR Capital Management", "Hedge Funds", ("aqr",)),
    _entry("Renaissance Technologies", "Hedge Funds", ("rentec", "renaissance")),
    _entry("Balyasny Asset Management", "Hedge Funds", ("bam", "balyasny")),
    _entry("Schonfeld", "Hedge Funds", ()),
    _entry("Marshall Wace", "Hedge Funds", ()),
    _entry("Capula Investment Management", "Hedge Funds", ("capula",)),
    _entry("Citco", "Hedge Funds", ()),
    _entry("Stripe", "Fintech", ()),
    _entry("Brex", "Fintech", ()),
    _entry("Ramp", "Fintech", ()),
    _entry("Plaid", "Fintech", ()),
    _entry("Mercury", "Fintech", ()),
    _entry("Robinhood", "Fintech", ("rh", "rf")),
    _entry("Chime", "Fintech", ()),
    _entry("Affirm", "Fintech", ()),
    _entry("SoFi", "Fintech", ()),
    _entry("Marqeta", "Fintech", ()),
    _entry("Adyen", "Fintech", ()),
    _entry("Wise", "Fintech", ("transferwise",)),
    _entry("OpenAI", "AI Companies", ("oai",)),
    _entry("Anthropic", "AI Companies", ()),
    _entry("xAI", "AI Companies", ("x ai",)),
    _entry("Cohere", "AI Companies", ()),
    _entry("Perplexity", "AI Companies", ("perplexity ai",)),
    _entry("Scale AI", "AI Companies", ("scale",)),
    _entry("Mistral AI", "AI Companies", ("mistral",)),
    _entry("Adept AI", "AI Companies", ("adept",)),
    _entry("Harvey", "AI Companies", ("harvey ai",)),
    _entry("Runway", "AI Companies", ("runwayml", "runway ml")),
    _entry("Character.AI", "AI Companies", ("character ai", "characterai")),
    _entry("Cursor", "AI Companies", ("anysphere cursor",)),
    _entry("Anysphere", "AI Companies", ()),
    _entry("Replit", "AI Companies", ()),
    _entry("Hugging Face", "AI Companies", ("hf", "huggingface")),
    _entry("Weights & Biases", "AI Companies", ("wandb", "weights and biases")),
    _entry("Databricks", "AI Companies", ()),
    _entry("Snowflake", "Enterprise / Cloud", ()),
    _entry("Cloudflare", "Enterprise / Cloud", ("cf",)),
    _entry("Datadog", "Enterprise / Cloud", ("ddog",)),
    _entry("Confluent", "Enterprise / Cloud", ()),
    _entry("MongoDB", "Enterprise / Cloud", ("mongo",)),
    _entry("Elastic", "Enterprise / Cloud", ("elasticsearch",)),
    _entry("HashiCorp", "Enterprise / Cloud", ("hashicorp",)),
    _entry("Palantir", "Enterprise / Cloud", ("pltr",)),
    _entry("Splunk", "Enterprise / Cloud", ()),
    _entry("Twilio", "Enterprise / Cloud", ()),
    _entry("Atlassian", "Enterprise / Cloud", ()),
    _entry("GitLab", "Enterprise / Cloud", ("gitlab",)),
    _entry("GitHub", "Enterprise / Cloud", ("github",)),
    _entry("Okta", "Enterprise / Cloud", ()),
    _entry("CrowdStrike", "Enterprise / Cloud", ("crowdstrike",)),
    _entry("Palo Alto Networks", "Enterprise / Cloud", ("panw", "palo alto")),
    _entry("Zscaler", "Enterprise / Cloud", ()),
    _entry("ServiceNow", "Enterprise / Cloud", ("snow",)),
    _entry("Workday", "Enterprise / Cloud", ()),
    _entry("Box", "Enterprise / Cloud", ()),
    _entry("Asana", "Enterprise / Cloud", ()),
    _entry("Zoom", "Enterprise / Cloud", ("zoom video communications",)),
    _entry("Anduril Industries", "Defense / Aerospace", ("anduril",)),
    _entry("SpaceX", "Defense / Aerospace", ("spacex",)),
    _entry("Blue Origin", "Defense / Aerospace", ()),
    _entry("Lockheed Martin", "Defense / Aerospace", ("lhm",)),
    _entry("Northrop Grumman", "Defense / Aerospace", ("northrop",)),
    _entry("Raytheon", "Defense / Aerospace", ("rtx", "raytheon technologies")),
    _entry("Boeing", "Defense / Aerospace", ()),
    _entry("General Dynamics", "Defense / Aerospace", ("gd",)),
    _entry("L3Harris Technologies", "Defense / Aerospace", ("l3harris", "l3 harris")),
    _entry("Shield AI", "Defense / Aerospace", ()),
    _entry("Saronic", "Defense / Aerospace", ()),
    _entry("JPMorgan Chase", "Banks", ("jp", "jpm", "jpmc", "jp morgan", "jp morgan chase")),
    _entry("Goldman Sachs", "Banks", ("gs",)),
    _entry("Morgan Stanley", "Banks", ("ms",)),
    _entry("Bank of America", "Banks", ("bofa", "boa")),
    _entry("Capital One", "Banks", ("c1",)),
    _entry("American Express", "Banks", ("amex",)),
    _entry("Wells Fargo", "Banks", ("wf",)),
    _entry("Citibank", "Banks", ("citi", "citigroup")),
    _entry("Barclays", "Banks", ()),
    _entry("BNY", "Banks", ("bank of new york", "bny mellon")),
    _entry("Figma", "Unicorn / Growth Startups", ()),
    _entry("Notion", "Unicorn / Growth Startups", ()),
    _entry("Linear", "Unicorn / Growth Startups", ()),
    _entry("Vercel", "Unicorn / Growth Startups", ()),
    _entry("Neon", "Unicorn / Growth Startups", ("neon database",)),
    _entry("Supabase", "Unicorn / Growth Startups", ()),
    _entry("PlanetScale", "Unicorn / Growth Startups", ("planetscale",)),
    _entry("Render", "Unicorn / Growth Startups", ()),
    _entry("Rippling", "Unicorn / Growth Startups", ()),
    _entry("Deel", "Unicorn / Growth Startups", ()),
    _entry("Airtable", "Unicorn / Growth Startups", ()),
    _entry("Retool", "Unicorn / Growth Startups", ()),
    _entry("ClickHouse", "Unicorn / Growth Startups", ("clickhouse",)),
    _entry("Cockroach Labs", "Unicorn / Growth Startups", ("cockroachdb", "cockroach")),
    _entry("Planet", "Unicorn / Growth Startups", ("planet labs",)),
    _entry("General Motors", "Automotive / Industrial", ("gm",)),
)


def _split_aliases(value: str) -> tuple[str, ...]:
    return tuple(alias.strip() for alias in value.split("|") if alias.strip())


def _load_csv_registry() -> tuple[CompanyRegistryEntry, ...]:
    registry_path = resources.files("process_bot").joinpath("company_data/cs_careers_companies_900.csv")
    with registry_path.open(newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        return tuple(
            CompanyRegistryEntry(
                id=(row["company_id"] or company_key(row["company_name"])).replace("_", "-"),
                display_name=row["company_name"].strip(),
                aliases=_split_aliases(row.get("aliases", "")),
                category=(row.get("primary_category") or "Other").strip() or "Other",
                active=row.get("allowed", "true").strip().lower() == "true",
            )
            for row in rows
            if row.get("company_name", "").strip()
        )


def _merge_registry_entries(entries: tuple[CompanyRegistryEntry, ...]) -> tuple[CompanyRegistryEntry, ...]:
    merged: dict[str, CompanyRegistryEntry] = {}
    order: list[str] = []

    for entry in entries:
        key = company_key(entry.display_name)
        if not key:
            continue
        if key not in merged:
            merged[key] = entry
            order.append(key)
            continue

        existing = merged[key]
        aliases = tuple(dict.fromkeys((*existing.aliases, *entry.aliases)))
        merged[key] = CompanyRegistryEntry(
            id=existing.id,
            display_name=existing.display_name,
            aliases=aliases,
            category=existing.category,
            active=existing.active or entry.active,
        )

    return tuple(merged[key] for key in order)


COMPANY_REGISTRY: tuple[CompanyRegistryEntry, ...] = _merge_registry_entries(
    (*_load_csv_registry(), *MANUAL_COMPANY_REGISTRY)
)


_COMPANIES_BY_KEY: dict[str, CompanyRegistryEntry] = {}
_ALIASES_BY_KEY: dict[str, CompanyRegistryEntry] = {}

for entry in COMPANY_REGISTRY:
    _COMPANIES_BY_KEY[company_key(entry.display_name)] = entry
    _ALIASES_BY_KEY[company_key(entry.display_name)] = entry
    for alias in entry.aliases:
        _ALIASES_BY_KEY[company_key(alias)] = entry


def resolve_company(value: str) -> CompanyRegistryEntry | None:
    key = company_key(value)
    if not key:
        return None
    entry = _ALIASES_BY_KEY.get(key)
    if entry and entry.active:
        return entry
    return None


def is_known_company(value: str) -> bool:
    return resolve_company(value) is not None


def is_known_company_slug(slug: str) -> bool:
    entry = _COMPANIES_BY_KEY.get(slug)
    return bool(entry and entry.active)
