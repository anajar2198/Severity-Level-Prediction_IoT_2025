"""Validate the assembled paper against preserved sources and archived final results."""
from pathlib import Path
import re,json,hashlib,subprocess,collections
import pandas as pd
P=Path(__file__).resolve().parents[2];D=P/'revision_materials/data';s=(P/'main_revised.tex').read_text();old=(P/'main.tex').read_text();log=(P/'main_revised.log').read_text()
active=lambda x:'\n'.join(l for l in x.splitlines() if not l.lstrip().startswith('%'))
headings=lambda x:re.findall(r'\\(?:subsection|section)\{[^}]+\}',active(x))
it=iter(headings(s));assert all(any(n==h for n in it) for h in headings(old))
labels=re.findall(r'\\label\{([^}]+)\}',s);assert len(labels)==len(set(labels));refs=re.findall(r'\\(?:ref|eqref)\{([^}]+)\}',s);assert set(refs)<=set(labels)
assert not any(t in log for t in ['Overfull','undefined references','multiply defined','Float too large'])
original_ok=subprocess.run(['git','diff','--exit-code','--','main.tex','ref.bib','figs'],cwd=P,capture_output=True).returncode==0;assert original_ok
assets=re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}',s)
for a in assets:
 assert (P/a).is_file(),a
 meta=json.loads((P/a).with_suffix('.layout.json').read_text())
 if meta.get('artwork')=='preserved_original':
  assert meta['minimum_text_pt'] is None
  assert all((P/src).exists() for src in meta['sources'])
 else: assert meta['minimum_text_pt']>=9.49
v=pd.read_csv(D/'validation_rankings.csv');assert (v.groupby(['task','stream','seed']).size()==100).all()
main=pd.read_csv(D/'main_runs.csv');assert len(main)==12
for _,n in main.iterrows():
 maxval=v[(v.task==n.task)&(v.stream==n.stream)&(v.seed==n.seed)].validation_balanced_accuracy.max();assert abs(maxval-n.val_metric)<1e-10
for seed in [1234,2234,3234]:
 r=pd.read_csv(D/f'recordings_{seed}.csv');assert r.folder_name.nunique()==len(r)==18;assert r.split.value_counts().to_dict()=={'train':10,'val':4,'test':4}
for task in ['binary','severity']:
 for stream in ['motor','pcc']:
  cm=pd.read_csv(D/f'{task}_{stream}_confusion_counts.csv',index_col=0);n=main[(main.task==task)&(main.stream==stream)].test_n.sum();assert int(cm.to_numpy().sum())==int(n)
info=subprocess.run(['pdfinfo',str(P/'main_revised.pdf')],capture_output=True,text=True,check=True).stdout;pages=int(re.search(r'Pages:\s+(\d+)',info).group(1))
fonts=subprocess.run(['pdffonts',str(P/'main_revised.pdf')],capture_output=True,text=True,check=True).stdout
assert 'Nimbus' in fonts and not re.search(r'\sno\s+(?:yes|no)\s+(?:yes|no)\s+\d+\s+\d+\s*$',fonts,re.M)
status={'original_source_unchanged':original_ok,'original_main_sha256':hashlib.sha256((P/'main.tex').read_bytes()).hexdigest(),'revised_main_sha256':hashlib.sha256((P/'main_revised.tex').read_bytes()).hexdigest(),'all_original_headings_preserved':True,'unique_labels':True,'references_resolved':True,'no_overfull_boxes':True,'pdf_pages':pages,'paper_figures':len(assets),'minimum_new_result_figure_font_pt':min(m['minimum_text_pt'] for a in assets if (m:=json.loads((P/a).with_suffix('.layout.json').read_text()))['minimum_text_pt'] is not None),'original_artwork_font_note':'Figures 1–4 retain original typography; inherited raster text has no verified minimum font size.','fonts_embedded':True,'validated_main_repeats':len(main),'search_rows':len(v),'validation_winners_verified':True,'recording_allocations_verified':True,'pooled_confusion_counts_verified':True,'limitations':'No claim of independent external validation, dynamic operating tests, new attack families or new topology/modulation experiments.'}
(P/'revision_materials/validation.json').write_text(json.dumps(status,indent=2)+'\n')
(P/'revision_materials/asset_sha256.json').write_text(json.dumps({str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [P/'main_revised.tex',P/'main_revised.pdf',P/'ref_revised.bib',*[P/a for a in assets],*sorted(D.glob('*.csv'))]},indent=2)+'\n')
print(json.dumps(status,indent=2))
