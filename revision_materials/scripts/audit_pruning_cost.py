"""Explain archived pruning timings by counting actual feature-family evaluations.
No model fitting, data relabeling, or replacement of archived runtime measurements.
"""
from pathlib import Path
import sys,json,collections
import numpy as np,pandas as pd
P=Path(__file__).resolve().parents[2];W=P.parent;sys.path.insert(0,str(W))
import tdms_to_numpy_continues_lfhf_per_channel as fe
from reviewer_revision.benchmark_corrected_models import raw_window
D=P/'revision_materials/data';C=W/'reviewer_revision/full_paper_rerun';main=pd.read_csv(D/'main_runs.csv');rows=[];calls=[]
for stream in ['pcc','motor']:
 raw,_=raw_window(stream)
 for seed in [1234,2234,3234]:
  full=Path(main.query('task=="binary" and stream==@stream and seed==@seed').iloc[0].model_path)
  if not full.is_absolute():full=W/full
  for variant in ['full','top75','top50','top25','per_channel15','per_channel10']:
   model=full if variant=='full' else C/'pruning'/stream/str(seed)/variant
   cols=np.load(model/'normalization.npz')['feature_indices'];plan=fe.compile_global_feature_plan(cols,raw.shape[1])
   for ch,p in enumerate(plan['channel_plans']):
    indices=p['selected_feature_indices'];names=[fe.FEATURE_NAMES_PER_CHANNEL[i] for i in indices]
    rows.append(dict(stream=stream,seed=seed,variant=variant,channel=ch+1,retained=len(indices),LF=int(p['need_low']),HF=int(p['need_hf']),TD=int(p['need_time']),computed_base_statistics=15*int(p['need_low'])+11*int(p['need_hf'])+8*int(p['need_time']),names=';'.join(names)))
   if seed==1234 and variant in ['full','top25']:
    counter=collections.Counter();original={k:getattr(fe,k) for k in ['compute_low_features','compute_hf_features','compute_time_features']}
    for k,func in original.items():
     def counted(*args,_key=k,_func=func,**kwargs):counter[_key]+=1;return _func(*args,**kwargs)
     setattr(fe,k,counted)
    try:out=fe.extract_window_features_per_channel(raw,10000.,2000,500,250,25,29,fixed_time_steps=61,feature_plan=plan)[0]
    finally:
     for k,f in original.items():setattr(fe,k,f)
    reference=fe.extract_window_features_per_channel(raw,10000.,2000,500,250,25,29,fixed_time_steps=61)[0][:,:,cols]
    np.testing.assert_allclose(out,reference,rtol=1e-5,atol=1e-6)
    calls.append(dict(stream=stream,variant=variant,retained=len(cols),**counter,maximum_absolute_feature_difference=float(np.max(np.abs(out-reference)))))
pd.DataFrame(rows).to_csv(D/'pruning_dependency_audit.csv',index=False)
report={'finding':'Extraction skips unused LF/HF/TD families per channel, but computes all statistics within each retained family before selecting output columns. This is family-level selection, not individual-feature selection.','call_counts_per_2000_sample_window':calls,'equivalence':'Selected outputs match corresponding full-feature columns within rtol=1e-5, atol=1e-6.','scope':'The audit describes the archived implementation. Existing saved runtimes remain unchanged. It does not measure an optimized individual-feature implementation.'}
(D/'pruning_cost_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
