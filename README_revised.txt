REVISED MANUSCRIPT — WORKING DRAFT

Open main_revised.pdf to review the compiled paper. Set main_revised.tex as the main document in Overleaf. The original main.tex, ref.bib, and figs/ remain unchanged. main_revised.tex uses the separate ref_revised.bib and figs_revised/ assets.

The original title, author list, eight main sections, subsection order, and existing appendix are retained. Original Tables I–XII and Figures 1–8 retain their roles. The appendix adds a detection-by-severity table/figure and a hyperparameter-sensitivity figure. The compiled draft includes references and an appendix; the current page count is recorded in revision_materials/validation.json. Final journal length/format requirements and author approval still need checking before submission.

RESULTS AND SCOPE
Only the completed clean full_paper_rerun campaign is used. All 60,054 existing windows are included: 54,000 scheduled and 6,054 author-confirmed zero-bias post-schedule normal windows. Main evaluation separates entire recordings and their episodes, with three repeated holdouts. Severity is maximum absolute injected phase bias; it is not a calibrated physical-harm or torque category. No new training or physical recordings were performed for this manuscript revision.

The revised abstract, methods, tables, plots, discussion, and conclusion use the final estimates. Lower accuracy, normal false alarms, transfer failures, competing baseline metrics, and limited pruning speedups are retained. Dynamic operating experiments, additional attack families, and topology/modulation generalization remain untested and are explicitly described as limitations. The paper is a preparation draft, not a claim that every previous reviewer request has been experimentally satisfied.

FILES
- figs_revised/: PDFs, PNG previews and layout/provenance records. Figures 1–4 preserve the original designs with minimal vector label corrections. Their inherited text retains its original size; a 9.5-point minimum is not asserted for those originals. New experimental result figures use Times-compatible Nimbus Roman with at least 9.5-point labels at their intended printed width. The paper retains IEEEtran's Times-family text.
- revision_materials/data/: final numeric summaries, validation rankings, main configurations, recording allocations, confusion counts and validation feature importance. Values named test_* generally use fractions; *_pct values use percentages. Timing is milliseconds; regression error is percentage points of nominal injected bias.
- revision_materials/reviewer_issue_tracker.csv: where each previous issue is addressed, including requests that remain outside the measured scope.
- revision_materials/validation.json: source integrity, cross-reference, figure and compilation checks.
- revision_materials/scripts/build_revision.py: recreates main_revised.tex from original main.tex plus archived final CSV results.
- revision_materials/scripts/make_revision_figures.py: plotting source for the corrected figures. Regeneration requires the existing local study workspace, completed predictions, TDMS recordings and original feature functions; it performs no model fitting. Compiling the paper does not require those datasets or Python.
- revision_materials/scripts/preserve_original_figures.py: embeds original Figures 1–4 and typesets minimal corrected labels; source assets are unchanged. Figure 2 original vector sources are included under figs_revised/original_sources/.
- revision_materials/scripts/compile_paper.py: compile using installed pdfLaTeX/BibTeX, with a fallback for the existing local portable TeX installation.

BUILD
With TeX Live/IEEEtran installed, run:
  pdflatex main_revised.tex
  bibtex main_revised
  pdflatex main_revised.tex
  pdflatex main_revised.tex
Or run python revision_materials/scripts/compile_paper.py. Required packages are amsmath, amsfonts, amssymb, array, graphicx, xcolor, booktabs, tabularx and url. Unused package dependencies from the original preamble were omitted without changing the document class or text font. The revised bibliography removes one duplicated entry, escapes accented names for BibTeX, and adds the verified MultiRocket reference; the original bibliography is preserved.

FIGURE INTERPRETATION
Figure 5 and the complementary PCC matrices pool predictions across repeated holdouts. A recording can appear in more than one repeat, so pooled counts are not independent physical replications. Tables average per-repeat metrics, and normal recall can differ slightly from the pooled matrix because normal-window counts differ across holdouts. The separately trained binary detector and the collapsed binary predictions of the severity model are different models and are identified accordingly.

Figures 6 and 8 use a prespecified alphabetic choice of held-out recording at seed 1234 rather than the best-looking trace. For the raw plots, PCC current is acquisition channel cDAQ9185-1EF7B78Mod4/ai0; the first PCC feature channel is voltage, not current. No ampere or torque calibration is inferred from recorded acquisition units. Figure 3 shows the implemented convolution kernels (39, 19 and 9), correcting the original schematic.

ORIGINAL FIGURE RESTORATION
Figure 1 retains the original apparatus artwork, with linear/nonlinear signal labels replaced by neutral sensing descriptions. Figure 2 retains the original seven-panel vector plots, which already have the correct LF 500/25 annotation. The later presentation PNGs have different axes/traces and are not substituted for the archived vector data. Zero is called reference time because attack-onset alignment could not be verified from the archived plot provenance. Figure 3 corrects kernel lengths to 39/19/9. Figure 4 adds PCC voltage, identifies acquisition output as a raw window, and removes the unsupported supervisory-command label. Original main.tex and figs/ are untouched. The restored figures are not fully redrawn vector diagrams: Figures 1, 3 and 4 embed the original raster artwork. Original small labels, especially Figure 2 axes, still require print-size readability review.
