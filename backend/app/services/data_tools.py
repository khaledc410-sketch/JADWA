"""
Shared data access tools for all JADWA sub-agents.
Loads Saudi seed data from JSON files and provides accessor methods.
"""

import json
import os
from functools import lru_cache
from typing import Any, Optional

from app.core.config import settings


# Sector alias map — seed files and agents use different keys
SECTOR_ALIASES = {
    "food_beverage": "fnb",
    "food_and_beverage": "fnb",
    "f&b": "fnb",
    "fnb": "fnb",
    "retail": "retail",
    "healthcare": "healthcare",
    "education": "education",
    "technology": "technology",
    "tech": "technology",
    "real_estate": "real_estate",
    "realestate": "real_estate",
    "franchise": "franchise",
    "manufacturing": "manufacturing",
    "logistics": "logistics",
    "hospitality": "hospitality",
    "construction": "construction",
    "automotive": "automotive",
    "finance": "finance",
    "it_telecom": "it_telecom",
}


def normalize_sector(sector: str) -> str:
    """Normalize sector key to canonical form used in seed files."""
    return SECTOR_ALIASES.get(sector.lower().strip(), sector.lower().strip())


@lru_cache(maxsize=10)
def _load_json(filename: str) -> dict | list:
    """Load and cache a JSON seed file."""
    path = os.path.join(settings.DATA_SEED_PATH, filename)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_seed(source: str) -> dict | list:
    """Load a seed JSON file by source name.

    Valid sources: sama_rates, rfta_franchises, gastat_demographics,
                   hrdf_nitaqat_ratios, vision2030_kpis, mci_licenses
    """
    filename_map = {
        "sama_rates": "sama_rates.json",
        "sama": "sama_rates.json",
        "rfta_franchises": "rfta_franchises.json",
        "rfta": "rfta_franchises.json",
        "gastat_demographics": "gastat_demographics.json",
        "gastat": "gastat_demographics.json",
        "hrdf_nitaqat_ratios": "hrdf_nitaqat_ratios.json",
        "hrdf": "hrdf_nitaqat_ratios.json",
        "vision2030_kpis": "vision2030_kpis.json",
        "vision2030": "vision2030_kpis.json",
        "mci_licenses": "mci_licenses.json",
        "mci": "mci_licenses.json",
    }
    filename = filename_map.get(source.lower(), f"{source}.json")
    return _load_json(filename)


# ── SAMA Rates ──────────────────────────────────────────────────────────────


def get_sama_rates() -> dict:
    """Full SAMA rates data including SAIBOR, repo, tax rates, SIDF programs."""
    return load_seed("sama_rates")


def get_saibor_3m() -> float:
    """Current 3-month SAIBOR rate."""
    data = load_seed("sama_rates")
    try:
        return data["saibor_rates"]["3_month"] / 100
    except (KeyError, TypeError):
        return 0.0595  # fallback


def get_vat_rate() -> float:
    data = load_seed("sama_rates")
    try:
        return data["tax_rates"]["vat_standard_percent"] / 100
    except (KeyError, TypeError):
        return 0.15


def get_zakat_rate() -> float:
    data = load_seed("sama_rates")
    try:
        return data["tax_rates"]["zakat_rate_percent"] / 100
    except (KeyError, TypeError):
        return 0.025


def get_sidf_programs() -> list:
    data = load_seed("sama_rates")
    return data.get("sidf_programs", [])


# ── RFTA Franchises ─────────────────────────────────────────────────────────


def _build_franchise_index() -> dict:
    """Build a lookup index for franchise data."""
    data = load_seed("rfta_franchises")
    franchises = data.get("franchises", data if isinstance(data, list) else [])
    index = {}
    for f in franchises:
        name_en = f.get("name_en", "").lower().strip()
        name_ar = f.get("name_ar", "").strip()
        if name_en:
            index[name_en] = f
        if name_ar:
            index[name_ar] = f
    return index


def lookup_franchise(brand_name: str) -> Optional[dict]:
    """Look up franchise by name (English or Arabic). Supports partial match."""
    index = _build_franchise_index()
    key = brand_name.lower().strip()
    # Exact match
    if key in index:
        return index[key]
    # Partial match
    for name, data in index.items():
        if key in name or name in key:
            return data
    return None


def search_franchises(sector: str = None, query: str = None, limit: int = 20) -> list:
    """Search franchises by sector and/or text query."""
    data = load_seed("rfta_franchises")
    franchises = data.get("franchises", data if isinstance(data, list) else [])
    results = franchises
    if sector:
        norm = normalize_sector(sector)
        results = [f for f in results if normalize_sector(f.get("sector", "")) == norm]
    if query:
        q = query.lower()
        results = [
            f
            for f in results
            if q in f.get("name_en", "").lower() or q in f.get("name_ar", "")
        ]
    return results[:limit]


# ── GASTAT Demographics ─────────────────────────────────────────────────────


def get_population_data() -> dict:
    """Population data from GASTAT."""
    data = load_seed("gastat_demographics")
    return data.get("population", data)


def get_market_data(sector: str) -> dict:
    """Get sector-specific market data from GASTAT."""
    data = load_seed("gastat_demographics")
    norm = normalize_sector(sector)
    # Check if there's sector-specific market data
    sectors = data.get("sector_data", data.get("sectors", {}))
    if isinstance(sectors, dict):
        return sectors.get(norm, sectors.get(sector, {}))
    return {}


def get_regional_data(city: str = None) -> Any:
    """Get regional/city data from GASTAT."""
    data = load_seed("gastat_demographics")
    cities = data.get("cities", data.get("regions", []))
    if city and isinstance(cities, list):
        city_lower = city.lower()
        for c in cities:
            if city_lower in c.get("name_en", "").lower() or city_lower in c.get(
                "name_ar", ""
            ):
                return c
    return cities


def get_consumer_segments() -> list:
    """Consumer segments from GASTAT."""
    data = load_seed("gastat_demographics")
    return data.get("consumer_segments", data.get("consumer_spending", []))


# ── HRDF / Nitaqat ──────────────────────────────────────────────────────────


def get_nitaqat_thresholds(sector: str) -> dict:
    """Nitaqat Saudization thresholds for a sector."""
    data = load_seed("hrdf_nitaqat_ratios")
    norm = normalize_sector(sector)
    sectors = data.get("sector_ratios", data.get("sectors", {}))
    if isinstance(sectors, dict):
        return sectors.get(norm, sectors.get(sector, {}))
    if isinstance(sectors, list):
        for s in sectors:
            if normalize_sector(s.get("sector", "")) == norm:
                return s
    return {}


def get_nitaqat_bands() -> dict:
    """All Nitaqat band definitions."""
    data = load_seed("hrdf_nitaqat_ratios")
    return data.get("nitaqat_bands", data.get("bands", {}))


def get_salary_benchmarks() -> dict:
    """Salary benchmarks from HRDF data."""
    data = load_seed("hrdf_nitaqat_ratios")
    return data.get("salary_benchmarks", data.get("salaries", {}))


def get_gosi_rates() -> dict:
    """GOSI contribution rates."""
    data = load_seed("hrdf_nitaqat_ratios")
    return data.get("gosi_rates", data.get("gosi", {}))


def get_hrdf_subsidy_info() -> dict:
    """HRDF subsidy programs and rates."""
    data = load_seed("hrdf_nitaqat_ratios")
    return data.get("hrdf_programs", data.get("subsidies", {}))


# ── Vision 2030 ─────────────────────────────────────────────────────────────


def get_vision_pillars() -> dict:
    """Vision 2030 three pillars with targets."""
    data = load_seed("vision2030_kpis")
    return data.get("pillars", {})


def get_incentive_programs(sector: str = None) -> list:
    """Government incentive programs, optionally filtered by sector."""
    data = load_seed("vision2030_kpis")
    programs = data.get("incentive_programs", [])
    if sector:
        norm = normalize_sector(sector)
        return [
            p
            for p in programs
            if not p.get("eligible_sectors")
            or norm in [normalize_sector(s) for s in p.get("eligible_sectors", [])]
        ]
    return programs


def get_giga_projects() -> list:
    """Mega/giga-projects from Vision 2030."""
    data = load_seed("vision2030_kpis")
    return data.get("giga_projects", data.get("mega_projects", []))


def get_sez_benefits(sector: str = None) -> list:
    """Special Economic Zone benefits."""
    data = load_seed("vision2030_kpis")
    return data.get("special_economic_zones", [])


# ── MCI Licenses ────────────────────────────────────────────────────────────


def get_licenses(sector: str) -> list:
    """Get required licenses for a sector from MCI data."""
    data = load_seed("mci_licenses")
    norm = normalize_sector(sector)
    sectors = data.get("sectors", data)
    if isinstance(sectors, dict):
        return sectors.get(norm, sectors.get(sector, []))
    if isinstance(sectors, list):
        for s in sectors:
            if normalize_sector(s.get("sector", "")) == norm:
                return s.get("licenses", [])
    return []


# ── Bulk seed to DB ─────────────────────────────────────────────────────────


def seed_all_data(db) -> int:
    """Bulk load all seed files into the DataCache table. Returns count of entries."""
    from datetime import datetime, timedelta
    from app.models.data_cache import DataCache

    sources = [
        "sama_rates",
        "rfta_franchises",
        "gastat_demographics",
        "hrdf_nitaqat_ratios",
        "vision2030_kpis",
        "mci_licenses",
    ]
    count = 0
    expires = datetime.utcnow() + timedelta(days=90)

    for source in sources:
        data = load_seed(source)
        if not data:
            continue
        existing = (
            db.query(DataCache)
            .filter(DataCache.source == source, DataCache.cache_key == "full")
            .first()
        )
        if existing:
            existing.data = data
            existing.expires_at = expires
            existing.updated_at = datetime.utcnow()
        else:
            entry = DataCache(
                source=source,
                cache_key="full",
                data=data,
                expires_at=expires,
            )
            db.add(entry)
        count += 1

    db.commit()
    return count


def clear_cache():
    """Clear the lru_cache for seed files (useful after refresh)."""
    _load_json.cache_clear()
