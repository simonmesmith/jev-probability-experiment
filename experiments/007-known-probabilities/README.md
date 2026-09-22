# Experiment 007: Jev on known probabilities

User-facing results: `../../outputs/known-probabilities/README.md`.

- `PROTOCOL.md`: frozen pre-inference design and scoring plan.
- `src/build_data.py`: authors 60 binary and 8 full-distribution cases, computes exact rational answers, checks enumeration.
- `data/cases.json`: model-facing scenarios and question candidates.
- `data/answers.json`: local mathematical truth and derivations; never included in shared API state.
- `src/method.py`: pinned model and prompt variants.
- `src/run.py`: immutable named runs, request/response retention, shared US$5 budget enforcement.
- `src/analyze.py`: scores saved responses without API access.
- `src/report.py`: produces Markdown, CSV-linked report and scientific figures; requires matplotlib and numpy.
- `sources/frozen.json`: pre-run hashes of protocol, cases, answers and inference source.
- `sources/docs-provenance.json`: current official source retrieval record.
- `runs/primary-v1`, `runs/repeat-1`, `runs/repeat-2`: 88 completed requests, 504 question responses, no retries or failures.

Budget US$5; estimated actual US$0.002614332. Credentials are read from `TYPESAFE_API_KEY` and are not saved. The runner intentionally refuses to overwrite existing named runs. Reproduce analysis with `python3 src/analyze.py` and report with `python3 src/report.py` from this experiment directory. Do not regenerate frozen data to tune against these results. A new inference experiment needs new named runs and an explicit protocol.

This diagnostic measures fidelity to analytically known probabilities, not general deployment calibration. Choice output probabilities, Noul yes probabilities, and confidence in a correct numerical answer are evaluated as distinct quantities.
