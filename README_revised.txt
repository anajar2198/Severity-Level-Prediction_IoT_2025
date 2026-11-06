OVERLEAF MANUSCRIPT

Set main_revised.tex as the main document in Overleaf and use pdfLaTeX.
The paper uses ref_revised.bib, figs_revised/, and the original assets in figs/.
The original main.tex, ref.bib, and figs/ are preserved.

The current source contains the corrected experimental results. Compile main_revised.tex to obtain the latest paper; an older tracked main_revised.pdf may predate source changes.
diff.tex and diff.pdf show the differences between the original main.tex and current main_revised.tex.

BUILD
  pdflatex main_revised.tex
  bibtex main_revised
  pdflatex main_revised.tex
  pdflatex main_revised.tex

The comparison document can be compiled by setting diff.tex as the main document. It uses the same figure/bibliography assets plus the standard ulem and adjustbox packages.

LOCAL SUPPORT FILES
Experimental summaries, timing observations, scripts, validation records, and reviewer working materials are kept outside this GitHub/Overleaf repository, in the sibling revision_materials/ directory in the local workspace. They are not required to compile either manuscript. The repository ignores /revision_materials/ to prevent accidental reintroduction.

Table X expresses speedup as percentage increase in processing rate:
  100 * (full-feature total time / subset total time - 1).
The full-feature baseline is 0%. Measured extraction times, total times, BA, and F1 are unchanged by this presentation change.
