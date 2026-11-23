# Data and provenance

`raw/` contains byte-for-byte provider responses and is intentionally not
committed. `processed/` contains generated outputs and is also intentionally
not committed. Run `python -m src.data_collection` to fetch the official
Eurostat, World Bank, KSH, and ECB inputs and write `raw/SHA256SUMS.txt` with
the SHA-256 digest of every retrieved response. Failed HTTP requests or
unexpected provider payloads stop acquisition and are surfaced to the caller.

Run `python -m src.run_pipeline` to acquire and process the raw data, or
`python -m src.run_pipeline --skip-download` to process only files already
under `raw/`. The provider parsers read the raw files without modifying them.

[`source_inventory.csv`](source_inventory.csv) records the source table and
exact download URL, geography, frequency, variables, observed/requested
coverage, response format and licensing notes for every input. Eurostat and
World Bank originals were already present locally and matched the live
provider responses byte-for-byte on 2026-11-23. KSH terms were not stated on
the linked table page; confirm the current reuse conditions before
redistributing KSH data. Raw data files are not included in the repository.

Cleaning rules are deliberately conservative: provider values are parsed to
numeric types, time values to dates, and coded identifiers are trimmed and
uppercased where applicable. Rows with an invalid/missing time or value (or
missing World Bank country code) are excluded; no value is imputed or
interpolated. Exact duplicate observations are removed, while conflicting
values for the same provider observation key stop processing with an error.
Eurostat's monthly and annual datasets remain separate. The World Bank long
table is also pivoted into `world_bank_indicators_wide.csv` by country and
year; blank indicator cells remain missing. KSH tables are additionally
stacked in `ksh_tourism_monthly.csv` with their source dataset ID retained.
The KSH and Eurostat datasets are not merged because their geographic levels,
coverage and definitions differ. Monthly outputs include derived year/month
fields; annual Eurostat outputs include year only.
