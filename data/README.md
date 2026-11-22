# Data and provenance

`raw/` is reserved for byte-for-byte provider responses and is intentionally not
committed. `processed/` contains generated outputs and is also intentionally
not committed. The source inventory in `source_inventory.csv` records the
intended official sources and the acquisition status observed in this run.

**Current status:** no external dataset has been downloaded or verified. The
runtime denied outbound source access. The inventory URLs and API patterns are
configured as leads for reproducible retrieval, not proof that a request
succeeded. No observations, statistics, charts, model results, or findings are
claimed in the current repository.

When access is available, run `python -m src.run_pipeline`. If KSH remains
unavailable through the script, open the relevant KSH table page from the
inventory, use its table download/export control to obtain the published
workbook/CSV, save the original file under `data/raw/ksh/`, and record its
exact file URL, format, retrieval date, and license in the inventory before
adding a parser. Do not copy/paste or edit the source data in a spreadsheet.
