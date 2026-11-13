"""Rebuild the two raw extracts in data/ directly from HUD and the Census Bureau.

This is the one step that is not in R. HUD publishes the Point-in-Time counts
only as .xlsb (binary Excel), and the R reader for that format (readxlsb) has no
build for the R version this project was written against. Rather than ship
hand-made CSVs with no provenance, the extraction lives here in Python and the
R scripts take over from the CSVs it writes.

Writes:
    data/ma_pit_2007_2025.csv   Massachusetts PIT counts, one row per year
    data/ma_pop.csv             Census population estimates, the rate denominators

Run:  python3 src/00_fetch.py            # writes into data/
      python3 src/00_fetch.py --check    # rebuilds to a temp dir and diffs
                                         # against the committed files instead

Requires: pandas, pyxlsb, certifi  (pip install pandas pyxlsb certifi)
"""

import argparse
import io
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

HUD_PIT = ("https://www.huduser.gov/portal/sites/default/files/xls/"
           "2007-2025-PIT-Counts-by-State.xlsb")

# Census state population totals. Three vintages are needed to span 2007-2025;
# the splice points (2010, 2020) are noted in the memo rather than smoothed.
CENSUS = {
    "2007-2009": ("https://www2.census.gov/programs-surveys/popest/datasets/"
                  "2000-2010/intercensal/state/st-est00int-alldata.csv"),
    "2010-2019": ("https://www2.census.gov/programs-surveys/popest/datasets/"
                  "2010-2020/state/totals/nst-est2020.csv"),
    "2020-2025": ("https://www2.census.gov/programs-surveys/popest/datasets/"
                  "2020-2025/state/totals/NST-EST2025-ALLDATA.csv"),
}

UA = {"User-Agent": "Mozilla/5.0 (research script; ma-homelessness-trend-break)"}

# PIT column headings are stable across years but sit among ~1,000 columns, so
# each series is matched on an exact heading rather than by position.
PIT_FIELDS = {
    "total":         r"Overall Homeless",
    "sheltered":     r"Sheltered Total Homeless",
    "unsheltered":   r"Unsheltered Homeless",
    "in_families":   r"Overall Homeless People in Families",
    "individuals":   r"Overall Homeless Individuals",
    "chronic":       r"Overall Chronically Homeless",
    "chronic_indiv": r"Overall Chronically Homeless Individuals",
    "veterans":      r"Overall Homeless Veterans",
    "shel_families": r"Sheltered Total Homeless People in Families",
}

YEARS = range(2007, 2026)
STATE = "MA"


def _ssl_context() -> ssl.SSLContext:
    """Verify certificates, preferring certifi's bundle.

    Python installed from python.org on macOS does not wire itself into the
    system keychain, so the default context fails on these hosts. certifi is
    used when present; verification is never disabled.
    """
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def get(url: str, attempts: int = 3, min_bytes: int = 1024) -> bytes:
    """Download a URL, retrying on transient failures.

    HUD rate-limits repeated requests and answers with an empty body rather
    than an error status, which would otherwise be written out as a truncated
    file. A short payload is therefore treated as a failure, not a result.
    """
    req = urllib.request.Request(url, headers=UA)
    last = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=120, context=_ssl_context()) as r:
                body = r.read()
            if len(body) < min_bytes:
                raise OSError(f"server returned {len(body)} bytes (rate limited?)")
            return body
        except urllib.error.URLError as e:
            if isinstance(getattr(e, "reason", None), ssl.SSLCertVerificationError):
                raise SystemExit(
                    "TLS certificate verification failed. Install certifi "
                    "(pip install certifi) and re-run."
                ) from e
            last = e
        except OSError as e:
            last = e
        if attempt < attempts:
            wait = 5 * attempt
            print(f"    attempt {attempt} failed ({last}); retrying in {wait}s", flush=True)
            time.sleep(wait)
    raise SystemExit(f"could not download {url}: {last}")


def fetch_pit() -> pd.DataFrame:
    """Massachusetts rows from every year sheet of the HUD PIT workbook."""
    print(f"  downloading {HUD_PIT.rsplit('/', 1)[-1]} ...", flush=True)
    book = pd.ExcelFile(io.BytesIO(get(HUD_PIT)), engine="pyxlsb")

    rows = []
    for year in YEARS:
        sheet = str(year)
        if sheet not in book.sheet_names:
            raise SystemExit(f"HUD workbook has no sheet for {year}")
        df = pd.read_excel(book, sheet_name=sheet, engine="pyxlsb")
        df.columns = [str(c).strip() for c in df.columns]

        state_col = df.columns[0]
        ma = df[df[state_col].astype(str).str.strip() == STATE]
        if len(ma) != 1:
            raise SystemExit(f"{year}: expected 1 {STATE} row, found {len(ma)}")

        rec = {"year": year}
        for name, heading in PIT_FIELDS.items():
            hit = [c for c in df.columns if re.fullmatch(heading, c)]
            # 'chronic' is absent before 2011 - a real definitional gap, kept as NA
            rec[name] = pd.to_numeric(ma.iloc[0][hit[0]], errors="coerce") if hit else None
        rows.append(rec)
        print(f"    {year}: total {rec['total']:,.0f}", flush=True)

    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)


def fetch_population() -> pd.DataFrame:
    """Massachusetts population, spliced across three Census vintages."""
    pop = {}

    print("  downloading Census 2000-2010 intercensal ...", flush=True)
    intercensal = pd.read_csv(io.BytesIO(get(CENSUS["2007-2009"])), encoding="latin-1")
    ma = intercensal[(intercensal.NAME.astype(str).str.strip() == "Massachusetts")
                     & (intercensal.SEX == 0) & (intercensal.ORIGIN == 0)
                     & (intercensal.RACE == 0) & (intercensal.AGEGRP == 0)]
    if len(ma) != 1:
        raise SystemExit(f"intercensal: expected 1 total row, found {len(ma)}")
    for y in (2007, 2008, 2009):
        pop[y] = int(ma.iloc[0][f"POPESTIMATE{y}"])

    print("  downloading Census Vintage 2020 ...", flush=True)
    v2020 = pd.read_csv(io.BytesIO(get(CENSUS["2010-2019"])))
    ma = v2020[v2020.NAME.astype(str).str.strip() == "Massachusetts"]
    for y in range(2010, 2020):
        pop[y] = int(ma.iloc[0][f"POPESTIMATE{y}"])

    print("  downloading Census Vintage 2025 ...", flush=True)
    v2025 = pd.read_csv(io.BytesIO(get(CENSUS["2020-2025"])))
    ma = v2025[v2025.NAME.astype(str).str.strip() == "Massachusetts"]
    for y in range(2020, 2026):
        pop[y] = int(ma.iloc[0][f"POPESTIMATE{y}"])

    missing = [y for y in YEARS if y not in pop]
    if missing:
        raise SystemExit(f"no population estimate for {missing}")
    return pd.DataFrame({"year": list(YEARS), "population": [pop[y] for y in YEARS]})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="rebuild to a temp directory and diff against the committed files")
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent
    committed = root / "data"
    target = (root / ".fetch_check") if args.check else committed
    target.mkdir(parents=True, exist_ok=True)

    print("HUD Point-in-Time counts")
    pit = fetch_pit()
    print("Census population estimates")
    popn = fetch_population()

    # Guards: these are the assumptions every downstream number rests on.
    assert len(pit) == 19, f"expected 19 state-years, got {len(pit)}"
    assert len(popn) == 19, f"expected 19 population years, got {len(popn)}"
    assert pit.total.notna().all(), "a year is missing its overall count"
    assert (pit.sheltered + pit.unsheltered - pit.total).abs().max() < 1, \
        "sheltered + unsheltered does not reconcile to the total"
    # Families + individuals need not equal the total: HUD counts a third
    # household type, people in households with only children. In this series
    # it is non-zero once (16 people in 2021), so the residual is required to
    # be non-negative and small rather than zero.
    residual = pit.total - pit.in_families - pit.individuals
    assert (residual >= 0).all(), "families + individuals exceed the overall count"
    assert (residual / pit.total).max() < 0.005, \
        "unexplained household-type residual above 0.5% of the total"

    pit.to_csv(target / "ma_pit_2007_2025.csv", index=False)
    popn.to_csv(target / "ma_pop.csv", index=False)
    print(f"\nwrote {target / 'ma_pit_2007_2025.csv'}")
    print(f"wrote {target / 'ma_pop.csv'}")

    if args.check:
        ok = True
        for name in ("ma_pit_2007_2025.csv", "ma_pop.csv"):
            fresh = pd.read_csv(target / name)
            old = pd.read_csv(committed / name)
            try:
                # Values, not storage format: a count written as 15127 and as
                # 15127.0 is the same datum.
                pd.testing.assert_frame_equal(fresh, old, check_dtype=False)
                same = True
            except AssertionError as e:
                same = False
                print(f"  {name}: {e}")
            ok &= same
            print(f"  {name}: {'matches' if same else 'DIFFERS FROM'} the committed file")
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
