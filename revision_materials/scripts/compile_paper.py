"""Build with system pdfLaTeX, or the existing portable TeX installation locally."""
from pathlib import Path
import os,shutil,subprocess
P=Path(__file__).resolve().parents[2];env=os.environ.copy();latex=shutil.which('pdflatex');bib=shutil.which('bibtex')
if not latex:
 root=Path('/tmp/ieee-tex-root');latex=str(root/'usr/bin/pdflatex');bib=str(root/'usr/bin/bibtex.original')
 if not Path(latex).exists():raise SystemExit('Install TeX Live (IEEEtran, recommended LaTeX packages/fonts, BibTeX), then rerun.')
 maps=root/'usr/share/texlive/texmf-dist/fonts/map/dvips';dest=Path('/tmp/shushan-tex-maps');dest.mkdir(exist_ok=True)
 files=['amsfonts/cm.map','amsfonts/cmextra.map','amsfonts/latxfont.map','amsfonts/symbols.map','tetex/ps2pk35.map']
 (dest/'pdftex.map').write_text('\n'.join((maps/f).read_text() for f in files))
 env.update(LD_LIBRARY_PATH=str(root/'usr/lib/x86_64-linux-gnu'),TEXMFCNF=str(root/'portable-cnf')+':'+str(root/'usr/share/texlive/texmf-dist/web2c'),TEXFORMATS='/tmp/ieee-tex-format',TEXFONTMAPS=str(dest)+':')
for args in [[latex,'-interaction=nonstopmode','-halt-on-error','main_revised.tex'],[bib,'main_revised'],[latex,'-interaction=nonstopmode','-halt-on-error','main_revised.tex'],[latex,'-interaction=nonstopmode','-halt-on-error','main_revised.tex']]:
 r=subprocess.run(args,cwd=P,env=env,capture_output=True,text=True)
 log=P/'revision_materials'/('bibtex_build.log' if args[0]==bib else 'latex_build.log');log.write_text(r.stdout+r.stderr)
 if r.returncode:print((r.stdout+r.stderr)[-4500:]);raise SystemExit(r.returncode)
print('Compiled main_revised.pdf successfully with BibTeX and three LaTeX passes.')
