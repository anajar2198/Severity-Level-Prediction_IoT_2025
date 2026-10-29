"""Typeset original Figures 1–4 with minimal vector label corrections.

Original raster artwork is embedded unchanged. Figure 2 uses the original
Matplotlib vector plots, not the later presentation PNGs. No traces are redrawn.
"""
from pathlib import Path
import os, json, re, shutil, subprocess, hashlib
from PIL import Image
P=Path(__file__).resolve().parents[2]; F=P/'figs_revised'; SRC=F/'original_sources'; SRC.mkdir(exist_ok=True)
W=515.52 # 7.16 inches, PDF points
latex=shutil.which('pdflatex'); env=os.environ.copy()
if not latex:
 root=Path('/tmp/ieee-tex-root'); latex=str(root/'usr/bin/pdflatex')
 env.update(LD_LIBRARY_PATH=str(root/'usr/lib/x86_64-linux-gnu'),TEXMFCNF=str(root/'portable-cnf')+':'+str(root/'usr/share/texlive/texmf-dist/web2c'),TEXFORMATS='/tmp/ieee-tex-format',TEXFONTMAPS='/tmp/shushan-tex-maps:')
records=[]
def rect(x,y,w,h,color='1,1,1'):
 return rf'\put({x:.4f},{y:.4f}){{\color[rgb]{{{color}}}\rule{{{w:.4f}bp}}{{{h:.4f}bp}}}}'
def label(x,y,text,size=8,color='0,0,0',bold=False):
 return rf'\put({x:.4f},{y:.4f}){{\makebox(0,0){{\color[rgb]{{{color}}}\fontsize{{{size}bp}}{{{size+1}bp}}\selectfont '+('\\bfseries ' if bold else '')+text+'}}'
def compile_figure(name,height,parts,source,notes,added=None):
 tex=r'''\documentclass{article}
\usepackage{graphicx,xcolor}
\renewcommand{\rmdefault}{ptm}
\pagestyle{empty}
\pdfhorigin=0bp\pdfvorigin=0bp
'''+rf'\pdfpagewidth={W}bp\pdfpageheight={height:.4f}bp'+'\n'+r'''\setlength{\unitlength}{1bp}
\begin{document}
'''+rf'\pdfpagewidth={W}bp\pdfpageheight={height:.4f}bp'+'\n'+r'''\setbox0=\hbox{\begin{picture}'''+f'({W},{height:.4f})'+'\n'+'\n'.join(parts)+'\n'+r'''\end{picture}}
\shipout\box0
\end{document}
'''
 path=F/(name+'.tex');path.write_text(tex)
 r=subprocess.run([latex,'-interaction=nonstopmode','-halt-on-error','-output-directory=figs_revised',str(path.relative_to(P))],cwd=P,env=env,capture_output=True,text=True)
 if r.returncode: raise RuntimeError(r.stdout[-3500:])
 for ext in ['aux','log']: (F/(name+'.'+ext)).unlink(missing_ok=True)
 subprocess.run(['pdftoppm','-singlefile','-scale-to','2400','-png',str(F/(name+'.pdf')),str(F/name)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 meta={'artwork':'preserved_original','width_in':7.16,'height_in':height/72,'minimum_text_pt':None,'minimum_added_label_pt':added,'font_note':'Original embedded artwork retains its original typography; no blanket minimum-font claim is made. Added labels use Times-compatible Nimbus Roman.','sources':source,'corrections':notes}
 (F/(name+'.layout.json')).write_text(json.dumps(meta,indent=2)+'\n');records.append({'figure':name,**meta})
def bitmap(name,file,patches,notes):
 path=P/'figs'/file
 with Image.open(path) as im: height=W*im.height/im.width
 parts=[rf'\put(0,0){{\includegraphics[width={W}bp]{{figs/{file}}}}}']
 scale=W/2048
 for x,y,w,h,text,size,color,bg in patches:
  parts += [rect(x*scale,height-(y+h)*scale,w*scale,h*scale,bg),label((x+w/2)*scale,height-(y+h/2)*scale,text,size,color)]
 compile_figure(name,height,parts,[str(path.relative_to(P))],notes,min([p[5] for p in patches],default=None))
bitmap('figure1_platform','diagram2.png',[
 (1072,108,182,26,'PCC signals',6.5,'0,0,0','1,1,1'),
 (1072,426,182,24,'current signals',6.5,'0,0,0','1,1,1'),
],['Original platform artwork restored; replaced unsupported linear/nonlinear sensing labels with signal descriptions.'])
bitmap('figure3_architecture','inceptiontime_architecture_lfhf.png',[
 (614,149,126,34,'k = 39',8,'0,0,0','0.933333,0.960784,0.988235'),
 (614,250,126,34,'k = 19',8,'0,0,0','0.933333,0.960784,0.988235'),
 (614,352,126,34,'k = 9',8,'0,0,0','0.933333,0.960784,0.988235'),
],['Corrected convolution kernel lengths to 39, 19, and 9; retained all original shapes, connections, and layout.'])
bitmap('figure4_pipeline','online_fdia_architecture.png',[
 (426,365,176,42,r'\shortstack{PCC voltage\\and current}',7.5,'0.05,0.32,0.09','1,1,1'),
 (683,473,186,53,r'\shortstack{2,000-sample\\raw window}',8,'0,0,0','1,1,1'),
 (1849,433,169,77,r'\shortstack{Alerts, logs,\\visualization}',7.5,'0,0,0','1,1,1'),
],['PCC measurement label now includes voltage and current.','Acquisition output is a raw 2,000-sample window; the 61-step representation belongs to feature extraction.','Removed supervisory-command claim; automatic mitigation was not evaluated.'])
# Figure 2: original vector traces and panel layout, with neutral reference-time labels.
parts=[]; sources=[]; panelwidth=(W-10)/2; height=0
for i,motor in enumerate(['acim','pcc']):
 name=f'tdms_lfhf_window_example_{motor}_179p9s_separate.pdf'; dest=SRC/name
 if not dest.exists():
  original=P.parent/'figs'/name
  if not original.exists():raise FileNotFoundError(f'Original vector source needed: {original}')
  shutil.copy2(original,dest)
 info=subprocess.check_output(['pdfinfo',str(dest)],text=True);pw,ph=map(float,re.search(r'Page size:\s+([\d.]+) x ([\d.]+)',info).groups());s=panelwidth/pw;x=i*(panelwidth+10);height=max(height,ph*s)
 sources.append(str(dest.relative_to(P)))
 parts.append(rf'\put({x:.4f},0){{\includegraphics[width={panelwidth}bp]{{{dest.relative_to(P)}}}}}')
 # Overlay only title/annotation text. Data and original axis coordinates remain untouched.
 parts += [rect(x,ph*s-22*s,panelwidth,22*s),label(x+panelwidth/2,ph*s-11*s,('Motor current' if i==0 else 'PCC current')+' and feature illustration',8)]
 ay=32.114942 if i==0 else 33.925002; ax=396.747037 if i==0 else 392.768572
 parts += [rect(x+(ax-3)*s,(ph-ay-18)*s,140*s,21*s),label(x+(ax+57)*s,(ph-ay-8)*s,'Reference time',7,'0.7,0,0')]
compile_figure('figure2_feature_example',height,parts,sources,['Restored original seven-panel vector plots, including their original LF window=500, stride=25 label and -200 to +200 ms axes.','Original vector curves were retained unchanged; the later presentation PNGs differ and are not used.','Onset alignment could not be verified from archived provenance, so zero is labeled reference time rather than a validated attack onset.'],7)
(F/'original_figure_restoration.json').write_text(json.dumps({'figures':records,'source_sha256':{s:hashlib.sha256((P/s).read_bytes()).hexdigest() for r in records for s in r['sources']}},indent=2)+'\n')
print('Restored original Figures 1–4 with minimal typeset label corrections.')
