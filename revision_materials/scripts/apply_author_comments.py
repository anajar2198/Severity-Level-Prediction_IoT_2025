"""Apply the 19 archived author comments after the evidence-based manuscript build.
Original main.tex and all original figures are read-only reference material.
"""
from pathlib import Path
import re
import pandas as pd
P=Path(__file__).resolve().parents[2];D=P/'revision_materials/data'
def apply(s):
 read=lambda n:pd.read_csv(D/(n+'.csv'))
 M,A,T,R=[read(n) for n in ['main_mean_sd','auxiliary_summary','transfer_summary','runtime_reductions']]
 def env(label,new,kind='table'):
  nonlocal s
  pat=r'\\begin\{'+kind+r'\*?\}.*?\\end\{'+kind+r'\*?\}'
  ms=[m for m in re.finditer(pat,s,re.S) if '\\label{'+label+'}' in m.group()];assert len(ms)==1,(label,len(ms));m=ms[0];s=s[:m.start()]+new+s[m.end():]
 def section(label,text):
  nonlocal s
  start=s.index('\\label{'+label+'}')+len('\\label{'+label+'}');m=re.search(r'\\(?:subsection|section|appendices|bibliographystyle)\b',s[start:]);assert m
  s=s[:start]+'\n\n'+text.strip()+'\n\n'+s[start+m.start():]
 def group(text,n):return r'\hline\multicolumn{'+str(n)+r'}{c}{\textit{'+text+r'}} \\\hline'
 def tab(label,caption,heads,rows,note='',size='footnotesize',sep=2.2,cols=None):
  n=len(heads);cols=cols or '@{}l'+'c'*(n-1)+'@{}'
  return '\n'.join([r'\begin{table}[t]',r'\centering','\\'+size,r'\caption{'+caption+'}',r'\label{'+label+'}',r'\renewcommand{\arraystretch}{1.15}',rf'\setlength{{\tabcolsep}}{{{sep}pt}}',r'\begin{tabular}{'+cols+'}',r'\hline',' & '.join(heads)+r' \\\hline',*[(r if isinstance(r,str) else ' & '.join(map(str,r))+r' \\') for r in rows],r'\hline\end{tabular}',r'\par\smallskip\begin{minipage}{\columnwidth}\scriptsize '+note+r'\end{minipage}' if note else '',r'\end{table}'])
 def f(n,m='test_bal_acc',bold=False,scale=100):
  mean=f'{n[m+"_mean"]*scale:.2f}';sd=f'{n[m+"_std"]*scale:.2f}'
  if bold:mean=r'\textbf{'+mean+'}'
  return r'\shortstack{'+mean+r'\\($\pm$'+sd+')}'
 def fig(label,file,caption,wide=False):
  k='figure*' if wide else 'figure'
  graphics=r'\includegraphics[width=\linewidth]{figs_revised/'+file+'.pdf}'
  if file=='figure6_detection_original_style':
   graphics=r'\includegraphics[width=0.49\linewidth]{figs_revised/figure6_overview_original_style.pdf}\hfill\includegraphics[width=0.49\linewidth]{figs_revised/figure6_zoom_original_style.pdf}'
  return '\n'.join([r'\begin{'+k+'}[t]',r'\centering',graphics,r'\caption{'+caption+'}',r'\label{'+label+'}',r'\end{'+k+'}'])
 # Consistent task identifiers, defined once; preserve all original subsection headings.
 s=s.replace('The study evaluates binary detection, four-level injected-bias assessment, cross-domain transfer, and processing cost',r'The study evaluates binary detection (\texttt{fdia2}), four-level injected-bias assessment (\texttt{severity4}), cross-domain transfer, and processing cost')
 # Avoid revision-history language in paper captions.
 s=s.replace(', retaining the original apparatus illustration','').replace('Original motor-current (left) and PCC-current (right) signal and feature illustrations, retained from the archived vector plots.','Motor-current (left) and PCC-current (right) signal and feature illustrations.').replace('Original InceptionTime schematic with convolution lengths corrected to 39, 19, and 9.','InceptionTime architecture for \\texttt{fdia2} and \\texttt{severity4}, with convolution lengths 39, 19, and 9.').replace('Original monitoring pipeline with corrected sensing and acquisition labels.','Monitoring pipeline for motor-side and PCC-side sensing.')
 s=s.replace('illustrates representative attack-onset responses and the corresponding LF/HF windows. In both cases, the raw signal is shown around the attack-transition instant, and representative LF and HF windows are overlaid to illustrate the two-scale extraction procedure. The motor-side signals exhibit stronger and more localized variations, whereas PCC-side responses are more distributed due to their aggregated nature.', 'illustrates the motor-current and PCC-current waveforms together with representative LF/HF windows. Each trace is plotted relative to a display reference time. The overlaid frames show the two temporal scales used for feature extraction, while the lower panels show how selected features vary along the signal. These examples illustrate the extraction procedure; detection and severity performance are evaluated separately on held-out recordings.')
 s=s.replace('Zero denotes the display reference time; its alignment with an attack onset is not established by the archived plot provenance. These descriptive traces are not held-out detector outputs.', 'Zero denotes the display reference time. These descriptive traces illustrate feature extraction and do not establish attack-onset timing or detector performance.')
 # Table III: restore grouped original structure and spell out slash-separated allocations.
 rows=[]
 def addg(t):rows.append(group(t,2))
 addg('Data dimensions')
 rows += [['Complete windows','60,054; 2,000 samples (0.2 s) each'],['Recordings / episodes','18 recordings; 540 scheduled episodes'],['Motor distribution','ACIM: 30,204; PMSM: 29,850'],['Normal / attack windows','33,054 normal; 27,000 attack'],['Normal tail windows','6,054; included with parent recording']]
 addg('Input configuration')
 rows += [['Features per channel','18 LF; 11 HF; 8 TD'],['Temporal feature steps','61 per outer window'],['Motor input',r'$61\times222$; six current channels'],['PCC input',r'$61\times74$; voltage and current']]
 addg(r'Severity labels (\texttt{severity4})')
 rows += [['Normal / low','33,054 / 5,400 windows'],['Medium / high','7,200 / 14,400 windows']]
 addg('Protocol 1: mixed-motor holdouts')
 rows += [['Recordings per motor','5 training; 2 validation; 2 test'],['Repeat 1 (seed 1234)','33,718 training; 13,279 validation; 13,057 test windows'],['Repeat 2 (seed 2234)','33,275 training; 13,250 validation; 13,529 test windows'],['Repeat 3 (seed 3234)','33,560 training; 13,227 validation; 13,267 test windows']]
 addg('Protocol 2: cross-motor adaptation')
 rows += [['Source recordings','6 training; 3 validation'],['Target recordings','6 adaptation-pool; 3 held-out test'],['Target adaptation budgets',r'1/5/10/20\%: 2/9/18/36 complete episode groups, respectively, from 180 groups']]
 env('tab:evaluation_protocols',tab('tab:evaluation_protocols','Dataset dimensions and recording-disjoint evaluation protocols.',['Parameter','Value / configuration'],rows,'Each recording and all its episodes remain in one partition within a repeat.',cols=r'@{}p{0.35\columnwidth}p{0.61\columnwidth}@{}'))
 # Top configurations: original nine-column layout with stream section rows.
 V=read('validation_rankings');rows=[]
 for stream in ['motor','pcc']:
  rows.append(group(stream.upper()+' stream',9))
  for _,n in V[(V.task=='severity')&(V.stream==stream)&(V.seed==1234)].sort_values('rank').head(5).iterrows():
   rows.append([int(n['rank']),int(n.depth),int(n.n_filters),int(n.bottleneck_size),f'{n.dropout_rate:.2f}',f'{n.lr:g}',r'$10^{-4}$' if n.weight_decay==.0001 else r'$5\!\times\!10^{-5}$',int(n.batch_size),(r'\textbf{'+f'{n.validation_balanced_accuracy*100:.2f}'+'}') if n['rank']==1 else f'{n.validation_balanced_accuracy*100:.2f}'])
 env('tab:search_top5_combined',tab('tab:search_top5_combined',r'Top five configurations by validation balanced accuracy on \texttt{severity4}, seed 1234.',['Rank','D','F','BN','Dr','LR','WD','BS',r'Val. BA'],rows,'D: depth; F: filters; BN: bottleneck; Dr: dropout; LR: learning rate; WD: weight decay; BS: batch size. Bold: highest validation BA within each stream. Test scores are not used for ranking.',size='footnotesize',sep=2.2))
 # Repeated metrics are stacked mean/SD to retain readable single-column tables.
 rows=[];metrics=['test_accuracy','test_bal_acc','test_macro_precision','test_macro_recall','test_macro_f1']
 for stream in ['pcc','motor']:
  rows.append(group(stream.upper()+' stream',6))
  for task,name in [('binary',r'\texttt{fdia2}'),('severity',r'\texttt{severity4}'),('motor_type','Motor type')]:
   data=A if task=='motor_type' else M;n=data.query('task==@task and stream==@stream').iloc[0];q=data.query('task==@task')
   rows.append([name]+[f(n,m,n[m+'_mean']==q[m+'_mean'].max()) for m in metrics])
 env('tab:all_tasks_in_domain',tab('tab:all_tasks_in_domain',r'Mixed ACIM/PMSM performance on held-out recordings (\%).',['Task','Acc.','BA','Prec.','Recall','F1'],rows,'Cells show mean above ($\\pm$ sample SD), over three holdouts; this is not a range or confidence interval. BA: balanced accuracy. Precision, recall, and F1 are macro-averaged. Bold compares streams for the same task and metric, not different tasks.',sep=1.7))
 B=read('baselines_summary');mr=read('additional_multirocket');mr['task']=mr.task.replace({'magnitude4':'severity'});mr=mr.groupby(['task','stream']).agg({m:['mean','std'] for m in ['test_accuracy','test_bal_acc','test_macro_f1']});mr.columns=['_'.join(c) for c in mr.columns];mr=mr.reset_index();rows=[]
 for task,label in [('binary','fdia2'),('severity','severity4')]:
  rows.append(group(r'\texttt{'+label+'}',4));ns=[]
  for method,name,data in [('inception','InceptionTime',M),('resnet','ResNet',B),('mlstmfcn','LSTM-FCN',B),('random_forest','Rand. Forest',B),('xgboost','XGBoost',B),('multirocket','MultiRocket',mr)]:
   q=data.query('task==@task and stream=="pcc"');q=q[q.method==method] if 'method' in q else q;ns.append((name,q.iloc[0]))
  for name,n in ns:rows.append([name]+[f(n,m,n[m+'_mean']==max(v[m+'_mean'] for _,v in ns)) for m in ['test_accuracy','test_bal_acc','test_macro_f1']])
 env('tab:model_comparison_hard_tasks',tab('tab:model_comparison_hard_tasks',r'PCC baseline comparison on \texttt{fdia2} and \texttt{severity4} (\%).',['Method','Accuracy','BA','Macro F1'],rows,'Mean above ($\\pm$ SD). Bold: highest mean for each metric within a task; it does not indicate statistical significance.'))
 rows=[]
 for stream in ['motor','pcc']:
  rows.append(group(stream.upper()+' stream',4))
  for source in ['acim','pmsm']:
   n=T.query('task=="binary" and stream==@stream and source==@source and mode=="source_only"').iloc[0];rows.append([r'ACIM $\to$ PMSM' if source=='acim' else r'PMSM $\to$ ACIM',f(n,'test_accuracy'),f(n),f(n,'test_macro_f1')])
 env('tab:cross_domain_source_only',tab('tab:cross_domain_source_only',r'Source-only \texttt{fdia2} transfer without target adaptation (\%).',['Direction','Accuracy','BA','Macro F1'],rows,'Mean above ($\\pm$ SD). Directions are different target-domain tests, so no best direction is highlighted.'))
 rows=[]
 for stream in ['motor','pcc']:
  rows.append(group(stream.upper()+' stream',6))
  for source in ['acim','pmsm']:
   a=T.query('task=="binary" and stream==@stream and source==@source');ns=[a[a['mode']=='source_only'].iloc[0]]+[a[(a['mode']=='fine_tune')&(a.requested_pool_fraction==v)].iloc[0] for v in [.01,.05,.1,.2]];best=max(n.test_bal_acc_mean for n in ns)
   rows.append([r'\shortstack{ACIM $\to$\\PMSM}' if source=='acim' else r'\shortstack{PMSM $\to$\\ACIM}']+[f(n,bold=n.test_bal_acc_mean==best) for n in ns])
 env('tab:domain_adaptation_anomaly2',tab('tab:domain_adaptation_anomaly2',r'Few-shot \texttt{fdia2} adaptation by labeled target-domain fine-tuning: balanced accuracy (\%).',['Direction',r'\shortstack{Source\\only}',r'1\%',r'5\%',r'10\%',r'20\%'],rows,'Mean above ($\\pm$ SD). Bold: highest observed mean within each direction and stream; no test-based configuration selection. Budgets refer to the target episode-group pool.',sep=1.7))
 # Remove target-only comparison from the paper while preserving all supporting results.
 s=s.replace('source-only transfer, supervised adaptation, and target-only training','source-only transfer and supervised adaptation')
 s=s.replace(' Target-only controls are trained from random initialization on exactly the same labeled target subsets for 20 epochs, using the selected architecture, its original learning rate, and normalization fitted on that subset. These are controls under the stated training budget, not exhaustive target-only optimization.','')
 s=s.replace('Target-domain fine-tuning and matched target-only controls test whether labeled target episodes alleviate this mismatch.','Target-domain fine-tuning tests whether labeled target episodes alleviate this mismatch.')
 s=s.replace('reports binary balanced accuracy for all target budgets, including matched target-only controls.','reports \\texttt{fdia2} balanced accuracy before and after target-domain fine-tuning.')
 start=s.index('Fine-tuning is not uniformly preferable to target-only training.');end=s.index('\n\\begin{table}',start)
 s=s[:start]+r'''The benefit is direction dependent. At the 1\% budget, motor ACIM-to-PMSM performance remains near the source-only result, whereas PMSM-to-ACIM performance improves substantially. Increasing the target budget generally helps, but the PCC ACIM-to-PMSM sequence is not monotonic. These comparisons measure improvement over the source-only model; they do not establish superiority over training directly on the same target labels.
'''+s[end:]
 start=s.index('The target-only comparison is essential.');end=s.index('\n\\subsection',start)
 s=s[:start]+r'''The adaptation results therefore support direction-specific target calibration. In particular, the strong PCC PMSM-to-ACIM gain is not reproduced in the reverse direction. Source-only and fine-tuned results quantify the benefit of updating a source model with target labels; they do not isolate the contribution of source pretraining from the benefit of those labels.'''+s[end:]
 s=s.replace('unsupervised adaptation and exhaustive target-only optimization are outside its scope','unsupervised adaptation is outside its scope').replace('; matched target-only controls prevented attributing every gain to pretraining','; the source-only comparison does not establish a universal benefit of pretraining')
 # Compact matrices at real single-column print size; complementary PCC decisions beside error analysis.
 env('fig:main_confusion_matrices',fig('fig:main_confusion_matrices','figure5_confusion_matrices','Confusion matrices for \\texttt{fdia2} and \\texttt{severity4}. Rows are actual and columns predicted classes. Percentages normalize pooled prediction counts within each row across three holdouts; repeated appearances of a recording are not independent replications. N/L/M/H denote normal/low/medium/high bias.'),'figure')
 complementary=fig('fig:severity_detection_decisions','pcc_severity_and_detection_confusions','PCC \\texttt{severity4} outputs interpreted as (a) normal/any-attack decisions by actual class and (b) a collapsed binary decision. Row percentages pool three holdouts. These decisions come from the severity model, not the separately trained \\texttt{fdia2} detector.')
 env('fig:severity_detection_decisions','',kind='figure')
 needle=r'\label{fig:main_confusion_matrices}';end=s.index(r'\end{figure}',s.index(needle))+len(r'\end{figure}');s=s[:end]+'\n'+complementary+s[end:]
 s=s.replace('Exact-severity and any-attack recall are reported together in Appendix~\\ref{app:severity_detection}.',r'Fig.~\ref{fig:severity_detection_decisions} presents the complementary PCC decisions here. A low-bias attack predicted as medium or high is detected but its exact severity is incorrect. Normal false alarms must be considered alongside any-attack recall. Mean and SD values are listed in Appendix~\ref{app:severity_detection}.')
 # Restore original five-row detection plot, 200-s overview and 0–22-s zoom, using held-out predictions.
 env('fig:case1_30_motor_pcc_detection_examples',fig('fig:case1_30_motor_pcc_detection_examples','figure6_detection_original_style','Held-out ACIM detection: schedule, motor RMS, motor decision, PCC RMS, and PCC decision. (a) First 200 s; (b) first 22 s, including the first low-bias attack. The recording is the first alphabetically among seed-1234 test recordings. Curves use saved held-out predictions at window ends; RMS uses 500-sample frames at stride 25. Green: attack probability; red: predicted label; dashed gray: true label; dotted line: 0.5 threshold. Shading denotes scheduled attacks. Complete-recording and PMSM plots accompany the paper.',True),'figure')
 s=s.replace('shows the complete held-out ACIM recording, including the post-schedule normal tail.','shows a 200-s overview and a 22-s transition detail from a held-out ACIM recording.').replace('A corresponding held-out PMSM trace is supplied with the revision materials.','The complete recording, including its normal tail, and a corresponding held-out PMSM trace are supplied with the revision materials.')
 # Runtime: original stage columns, with clearly identified median and p95 rows.
 raw=read('runtime');rows=[]
 for stream in ['pcc','motor']:
  rows.append(group(stream.upper()+' stream',5))
  for stat,label in [('median_ms','Median'),('p95_ms','95th pct.')]:
   q=raw[(raw.stream==stream)&(raw.device=='cuda')&(raw.feature_set=='full')].set_index('stage');total=q.loc['end_to_end_processing',stat]
   rows.append([label,f'{q.loc["feature_extraction",stat]:.2f}',f'{q.loc["normalization_transfer_inference",stat]:.2f}',f'{total:.2f}',f'{1000/total:.2f}' if stat=='median_ms' else '--'])
 env('tab:runtime_latency',tab('tab:runtime_latency','GPU-assisted per-window latency and processing rate.',['Statistic',r'\shortstack{Feature\\extract.\\(ms)}',r'\shortstack{Norm./transfer\\+ inference\\(ms)}',r'\shortstack{Total\\processing\\(ms)}',r'\shortstack{Rate\\(windows/s)}'],rows,'Rate is the reciprocal of median total processing time. Stages are timed within each iteration; marginal percentiles need not sum. Acquisition (200 ms) is excluded. CPU measurements are supplied with the results.',size='footnotesize',sep=2))
 # Pruning: report the implementation limitation established by the code/call-count audit.
 old='Selective extraction must still compute shared spectral intermediates when retained features depend on them, which limits savings.'
 new=r'''The extractor skips an LF, HF, or TD family only when that entire family is absent from a channel; otherwise it computes every statistic in that family before selecting the requested columns. In the seed-1234 PCC top-25\% subset, all three families remain active on both channels: each family routine is called 122 times per window, exactly as for full input. Motor top-25\% removes the HF family on two channels, reducing HF calls from 366 to 244. Thus, the current implementation provides family-level computational pruning, not individual-feature computation. The nearly unchanged PCC latency reflects this implementation limit; it does not establish that a feature-level optimized extractor could not be faster.'''
 assert old in s;s=s.replace(old,new)
 pr=read('pruning_summary');rows=[];counts={'pcc':[74,56,37,18,30,20],'motor':[222,166,111,56,90,60]}
 for stream in ['pcc','motor']:
  rows.append(group(stream.upper()+' stream',7));ns=[]
  for i,(v,label) in enumerate([('full','Full'),('top75',r'75\%'),('top50',r'50\%'),('top25',r'25\%'),('per_channel15','15/ch.'),('per_channel10','10/ch.')]):
   n=M.query('task=="binary" and stream==@stream').iloc[0] if v=='full' else pr[(pr.stream==stream)&(pr.variant==v)].iloc[0];t=R[(R.stream==stream)&(R.device=='cuda')&(R.feature_set==v)].iloc[0];ex=raw[(raw.stream==stream)&(raw.device=='cuda')&(raw.feature_set==v)&(raw.stage=='feature_extraction')].iloc[0];ns.append((label,counts[stream][i],n,t,ex))
  for label,count,n,t,ex in ns:rows.append([label,count,f(n,bold=n.test_bal_acc_mean==max(x[2].test_bal_acc_mean for x in ns)),f(n,'test_macro_f1',n.test_macro_f1_mean==max(x[2].test_macro_f1_mean for x in ns)),f'{ex.median_ms:.2f}',(r'\textbf{'+f'{t.median_ms:.2f}'+'}') if t.median_ms==min(x[3].median_ms for x in ns) else f'{t.median_ms:.2f}',f'{t.speedup:.2f}'])
 env('tab:feature_pruning_anomaly2_runtime',tab('tab:feature_pruning_anomaly2_runtime',r'Feature pruning for \texttt{fdia2}: performance and runtime.',['Subset','No.',r'\shortstack{BA\\(\%)}',r'\shortstack{F1\\(\%)}',r'\shortstack{Extract.\\(ms)}',r'\shortstack{Total\\(ms)}',r'\shortstack{Speedup\\($\times$)}'],rows,'Performance: mean above ($\\pm$ SD). Timing: seed-1234 GPU-assisted median; 95th percentiles are supplied in the results. Bold: highest BA/F1 or lowest total latency within a stream. Only whole unused feature families are skipped.',size='scriptsize',sep=1.7))
 env('fig:top10_feature_importance',fig('fig:top10_feature_importance','figure7_validation_feature_importance','Top ten channel-specific features ranked by mean validation permutation importance. Blue, orange, and green bars denote LF, HF, and time-domain features, respectively. Bar length is the mean balanced-accuracy decrease; black whiskers indicate one SD across three holdouts. Channels 1--3/4--6 are ACIM/PMSM currents; PCC channels 1/2 are voltage/current.',True),'figure')
 ab=read('ablations_summary');counts={'pcc':[74,36,22,16,58,52,38],'motor':[222,108,66,48,174,156,114]};rows=[]
 for stream in ['pcc','motor']:
  rows.append(group(stream.upper()+' stream',5));ns=[]
  for i,(v,label) in enumerate([('full','Full'),('lf_only','LF only'),('hf_only','HF only'),('time_only','Time only'),('lf_hf','LF + HF'),('lf_time','LF + Time'),('hf_time','HF + Time')]):
   n=M.query('task=="binary" and stream==@stream').iloc[0] if v=='full' else ab[(ab.task=='binary')&(ab.stream==stream)&(ab.variant==v)].iloc[0];ns.append((label,counts[stream][i],n))
  for label,count,n in ns:rows.append([label,count]+[f(n,m,n[m+'_mean']==max(x[2][m+'_mean'] for x in ns)) for m in ['test_accuracy','test_bal_acc','test_macro_f1']])
 env('tab:lfhf_ablation_anomaly2',tab('tab:lfhf_ablation_anomaly2',r'LF/HF/TD ablation for \texttt{fdia2} (\%).',['Features','No.','Accuracy','BA','Macro F1'],rows,'Mean above ($\\pm$ SD). Bold: highest mean within each stream; these test comparisons do not select a replacement primary model.'))
 env('fig:app_attack_process_examples',fig('fig:app_attack_process_examples','figure8_original_style',r'First 200 s of prespecified held-out ACIM and PMSM recordings, showing the schedule and current RMS. Blue and red schedule blocks denote normal and attack intervals; numbers give maximum injected bias (\%). Middle/bottom: motor/PCC RMS over 500-sample frames at stride 25, in acquisition units. These are descriptive electrical traces, not calibrated torque measurements.',True),'figure')
 s=s.replace('over each complete recording, including the normal post-schedule tail. RMS is computed over each 2,000-sample outer window for these descriptive plots. It must be distinguished from the TD RMS feature, which uses 500-sample subwindows, and from HF band-limited RMS.','during the first 200 s of each selected recording. RMS uses 500-sample frames at stride 25, matching the time-domain RMS definition. Complete-recording diagnostics retain the post-schedule normal tails.')
 # Auxiliary metrics remain supplementary, but the PCC decision figure is now in error analysis.
 rows=[];dr=read('detection_summary')
 for stream in ['motor','pcc']:
  rows.append(group(stream.upper()+' stream',4))
  for severity in ['Low','Medium','High']:
   n=dr[(dr.stream==stream)&(dr.severity==severity)].iloc[0];rows.append([severity,f(n,'exact_severity_recall_pct',scale=1),f(n,'attack_detection_recall_pct',scale=1),f(n,'normal_false_alarm_pct',scale=1)])
 env('tab:severity_detection_recall',tab('tab:severity_detection_recall',r'Exact-severity and any-attack recall from four-class predictions (\%).',['True bias',r'\shortstack{Exact\\recall}',r'\shortstack{Any-attack\\recall}',r'\shortstack{Normal false\\alarms}'],rows,'Mean above ($\\pm$ SD). False alarms refer to the same normal class for all three attack levels. Different metrics are not competing methods, so none is highlighted as best.'))
 s=s.replace(r'\end{document}',fig('fig:regression_diagnostics','regression_diagnostics','Attack-only injected-bias regression on held-out recordings. Points and whiskers show the median and 10th--90th percentiles of predictions at each true bias, separately for each holdout seed; slight horizontal offsets separate repeats. The dashed diagonal is ideal agreement. All held-out attack windows are included; repeated appearances across holdouts are not independent recordings.',True)+'\n'+r'\end{document}')
 s=s.replace('These are estimates of injected amplitude on attacked windows, not measured mechanical impact.',r'Fig.~\ref{fig:regression_diagnostics} shows prediction distributions at every tested bias level for each repeat. These are estimates of injected amplitude on attacked windows, not measured mechanical impact.')
 assert 'target-only' not in s.lower()
 return s
