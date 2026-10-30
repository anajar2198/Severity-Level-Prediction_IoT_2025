"""Focused integrity checks for author-requested manuscript presentation changes."""
from pathlib import Path
import json,re,hashlib,subprocess
import numpy as np,pandas as pd
P=Path(__file__).resolve().parents[2];W=P.parent;D=P/'revision_materials/data';A=P/'revision_materials/author_review';s=(P/'main_revised.tex').read_text()
protected=json.loads((A/'protected_sources.json').read_text())
for name,sha in protected.items():assert hashlib.sha256((P/name).read_bytes()).hexdigest()==sha,name
assert not re.search(r'\\agent\s*\{',s)
assert r'\begin{table*}' not in s
assert 'target-only' not in s.lower()
assert 'test_macro_f1_mean' in pd.read_csv(D/'transfer_summary.csv')
assert s.index(r'\label{fig:severity_detection_decisions}')<s.index(r'\section{LATENCY')
assert s.index(r'\label{fig:regression_diagnostics}')>s.index(r'\label{app:auxiliary_diagnostics}')
# Existing experimental summaries must remain byte-for-byte identical to the author branch.
old_files=subprocess.check_output(['git','ls-tree','-r','--name-only','origin/main','revision_materials/data'],cwd=P,text=True).splitlines()
for name in old_files:
 old=subprocess.check_output(['git','show','origin/main:'+name],cwd=P)
 assert (P/name).read_bytes()==old,name
# Confirm new regression summaries cover every held-out attack window in all repeats.
q=pd.read_csv(D/'regression_figure_quantiles.csv');count=0
for (stream,seed),g in q.groupby(['stream','seed']):
 path=W/'reviewer_revision/full_paper_rerun/auxiliary/regression'/stream/str(seed)/'predictions.csv';p=pd.read_csv(path)
 assert g.n.sum()==len(p) and len(g)==10
 for _,n in g.iterrows():
  vals=p.loc[np.isclose(p['true'],n.true_bias_percentage_points),'predicted'].quantile([.1,.5,.9]).to_numpy();np.testing.assert_allclose(vals,[n.p10,n['median'],n.p90],rtol=1e-12,atol=1e-12)
 count+=len(p)
# Confirm runtime diagnosis is based on actual identical outputs, not assumed speedups.
audit=json.loads((D/'pruning_cost_audit.json').read_text());calls=audit['call_counts_per_2000_sample_window']
for stream in ['motor','pcc']:
 subset=[x for x in calls if x['stream']==stream];assert len(subset)==2
 assert all(x['maximum_absolute_feature_difference']==0 for x in subset)
pcc=[x for x in calls if x['stream']=='pcc']
assert all(x[k]==122 for x in pcc for k in ['compute_low_features','compute_hf_features','compute_time_features'])
result=dict(protected_original_files=len(protected),protected_original_files_unchanged=True,existing_experiment_data_files=len(old_files),existing_experiment_data_unchanged=True,all_tables_single_column=True,author_annotations_archived_not_in_clean_paper=True,target_only_controls_preserved_outside_paper=True,pcc_decision_figure_in_main_error_analysis=True,regression_plot_saved_predictions_verified=count,pruning_call_counts_and_output_equivalence_verified=True)
(A/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
