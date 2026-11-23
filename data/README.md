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
