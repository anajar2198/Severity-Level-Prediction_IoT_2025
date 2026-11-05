Selective-feature runtime correction, 5 November 2026

Table X uses table_x.csv (three-split BA/F1 unchanged; seed-1234 runtime).
summary.csv contains stage medians, quartiles, 95th percentiles and repetition counts.
samples.csv contains all individual observations, including randomized variant order.
runtime_table.csv covers pruning and all six reduced-family ablations.
protocol.json records the exact timing scope, source hashes, hardware, versions and raw window.
model_hashes.json identifies every validated saved model and normalization file.
validation.json and equivalence_checks.csv record 913 passing equality checks over 3,335,936 values.
feature_plans.csv records retained outputs and required base statistics/derivative sources.
previous_family_level/ preserves the superseded runtime CSVs.

Feature-to-feature comparisons use exact float64 equality. Comparisons with stored dataset tensors use exact float32 equality, the model input precision. Re-extraction of stored float64 data can differ at roundoff scale without changing float32 model inputs. The checks cover all 18 recordings at 0 s (normal), 15 s (attack), and 610 s (post-schedule normal). All pruning subsets for seeds 1234/2234/3234 and seed-1234 ablations are checked on representative ACIM/PMSM windows in those three contexts. Model logits match exactly. Synthetic checks cover every feature individually, zero/constant signals, reordering/duplicate indices, empty subsets, multiple windows and resampling. Guards fail if representative isolated paths execute unrelated FFT, envelope, moment or derivative computations.

No training, feature ranking, labels, normalization, splits or performance summaries changed. Timing uses the same representative ACIM raw window as the previous runtime study, with plan compilation outside the measured loop. Full and reduced variants use the same selective implementation. Timing is from one workstation and one recorded window; it excludes acquisition and disk I/O and is not an embedded worst-case guarantee.

Scripts: ../../scripts/selective_feature_extraction.py, benchmark_selective_runtime.py, refresh_selective_runtime.py.
