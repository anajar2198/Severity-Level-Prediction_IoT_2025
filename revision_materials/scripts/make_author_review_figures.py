"""Restyle saved results to the original paper's visual pattern; no model fitting."""
from pathlib import Path
import sys,json,inspect
import numpy as np,pandas as pd
P=Path(__file__).resolve().parents[2];W=P.parent;sys.path.insert(0,str(W))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from reviewer_revision.paper_figure_style import apply_paper_style,save_paper_figure
style=apply_paper_style();D=P/'revision_materials/data';F=P/'figs_revised';C=W/'reviewer_revision/full_paper_rerun'
def save(fig,name):
 if fig.legends:
  from matplotlib.text import Text
  for t in fig.findobj(match=Text):
   if t.get_visible() and t.get_text().strip() and t.get_fontsize()<9.5:t.set_fontsize(9.5)
  fig.tight_layout(pad=.65,h_pad=1,w_pad=1,rect=(0,0,1,.9))
  fig.savefig(F/(name+'.pdf'));fig.savefig(F/(name+'.png'),dpi=600)
  texts=[t.get_fontsize() for t in fig.findobj(match=Text) if t.get_visible() and t.get_text().strip()]
  (F/(name+'.layout.json')).write_text(json.dumps(dict(width_in=float(fig.get_figwidth()),height_in=float(fig.get_figheight()),minimum_text_pt=min(texts),font_family=plt.rcParams['font.serif'][0],png_dpi=600,physical_size_preserved=True),indent=2)+'\n')
 else:save_paper_figure(fig,F/name)
 plt.close(fig)
def heat(ax,cm,labels,preds,title):
 pct=np.divide(cm,cm.sum(1,keepdims=True),out=np.zeros_like(cm,dtype=float),where=cm.sum(1,keepdims=True)!=0)*100
 ax.imshow(pct,cmap='Blues',vmin=0,vmax=100,aspect='equal')
 for i in range(len(labels)):
  for j in range(len(preds)):ax.text(j,i,f'{pct[i,j]:.1f}',ha='center',va='center',fontsize=9.5,color='white' if pct[i,j]>55 else 'black')
 ax.set(xticks=np.arange(len(preds)),xticklabels=preds,yticks=np.arange(len(labels)),yticklabels=labels);ax.set_title(title,fontsize=9.5,pad=4);ax.tick_params(length=0,pad=2)
fig,axs=plt.subplots(2,2,figsize=(3.5,3.4))
for i,task in enumerate(['binary','severity']):
 for j,stream in enumerate(['motor','pcc']):
  cm=pd.read_csv(D/f'{task}_{stream}_confusion_counts.csv',index_col=0).to_numpy();labels=['N','A'] if task=='binary' else ['N','L','M','H'];heat(axs[i,j],cm,labels,labels,f'({"abcd"[i*2+j]}) {stream.upper()}: '+('fdia2' if i==0 else 'severity4'))
fig.supxlabel('Predicted class',fontsize=10);fig.supylabel('Actual class',fontsize=10);save(fig,'figure5_confusion_matrices')
cm=pd.read_csv(D/'severity_pcc_confusion_counts.csv',index_col=0).to_numpy();dec=np.column_stack([cm[:,0],cm[:,1:].sum(1)]);binary=np.array([[cm[0,0],cm[0,1:].sum()],[cm[1:,0].sum(),cm[1:,1:].sum()]])
fig,axs=plt.subplots(1,2,figsize=(3.5,2.7));heat(axs[0],dec,['N','L','M','H'],['N','A'],'(a) By true class');heat(axs[1],binary,['N','A'],['N','A'],'(b) Collapsed')
fig.supxlabel('Predicted N (normal) / A (any attack)',fontsize=9.5);fig.supylabel('Actual class',fontsize=10);save(fig,'pcc_severity_and_detection_confusions')
# Original importance palette/layout, with explicit channel identities and whisker legend.
from tdms_to_numpy_continues_lfhf_per_channel import FEATURE_NAMES_PER_CHANNEL
palette={'LF':'#2c7fb8','HF':'#e66101','Time':'#32a567'}
fig,axs=plt.subplots(1,2,figsize=(7.16,3.6));importance=[]
for ax,stream in zip(axs,['motor','pcc']):
 r=pd.concat([pd.read_csv(D/f'importance_{stream}_{seed}.csv').assign(seed=seed) for seed in [1234,2234,3234]]);r=r.groupby('feature_index').importance_drop_bal_acc.agg(['mean','std']).sort_values('mean',ascending=False).head(10)
 labels=[f'Ch {int(i)//37+1}: {FEATURE_NAMES_PER_CHANNEL[int(i)%37]}' for i in r.index];colors=[palette['LF' if int(i)%37<18 else 'HF' if int(i)%37<29 else 'Time'] for i in r.index]
 y=np.arange(len(r));ax.barh(y,100*r['mean'],color=colors,xerr=100*r['std'],error_kw={'ecolor':'#222222','elinewidth':.7,'capsize':2});ax.set(yticks=y,yticklabels=labels,title=stream.upper()+' stream',xlabel='BA decrease (percentage points)');ax.invert_yaxis();ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True)
 importance.extend([dict(stream=stream,feature_index=int(i),mean_drop_pp=100*n['mean'],sd_drop_pp=100*n['std']) for i,n in r.iterrows()])
fig.legend(handles=[Patch(color=c,label=k) for k,c in palette.items()],loc='upper center',ncol=3,bbox_to_anchor=(.5,1.005),frameon=False)
save(fig,'figure7_validation_feature_importance');pd.DataFrame(importance).to_csv(D/'importance_figure_values.csv',index=False)
# Read existing raw recordings and saved held-out predictions. No inference or model retraining.
from tdms_to_numpy import read_tdms_folder,DEFAULT_ACIM_MOTOR_CHANNELS,DEFAULT_PMSM_MOTOR_CHANNELS,DEFAULT_PCC_CHANNELS
from plot_dual_stream_detection_over_signal import make_dual_plot
from plot_model_detection_over_signal import compute_continuous_feature_trace
manifest=pd.read_csv(C/'splits/1234/manifest.csv');main=pd.read_csv(D/'main_runs.csv');bundles={};recordings=[]
for motor in ['acim','pmsm']:
 m=manifest[(manifest.motor_type==motor)&(manifest.split=='test')];folder=sorted(m.folder_name.unique())[0];m=m[m.folder_name==folder].sort_values('window_start_second')
 channel=(DEFAULT_ACIM_MOTOR_CHANNELS if motor=='acim' else DEFAULT_PMSM_MOTOR_CHANNELS)[0];raw,fs=read_tdms_folder(W/'540case_for_shushan_paper_final_20260220'/folder,(channel,DEFAULT_PCC_CHANNELS[1]));intervals=[]
 for episode,g in m[~m.is_post_schedule_normal].groupby('episode_id',sort=False):
  start=float(g.window_start_second.min());bias=float(g.target_regression.max());intervals.extend([dict(start_second=start,end_second=start+10,segment_type='normal',severity_label=0),dict(start_second=start+10,end_second=start+20,segment_type='attack',severity_label=bias)])
 intervals.append(dict(start_second=600,end_second=len(raw)/fs,segment_type='tail_normal',severity_label=0));bs={}
 for j,stream in enumerate(['motor','pcc']):
  row=main[(main.task=='binary')&(main.stream==stream)&(main.seed==1234)].iloc[0];path=Path(row.model_path);path=path if path.is_absolute() else W/path;a=pd.read_csv(path/'predictions.csv');a=a[a.folder_name==folder].sort_values('window_end_second');assert len(a)==len(m)
  prob='p_class1' if 'p_class1' in a else 'p_attack';a=a.rename(columns={prob:'attack_probability','predicted':'pred_label','true':'true_label'})
  bs[stream]=dict(raw_data=raw[:,j:j+1],fs=fs,plot_channel_idx=0,scores_df=a)
 bundles[motor]=(bs,intervals,folder);recordings.append(dict(motor=motor,folder=folder,seed=1234,partition='test',motor_channel=channel,pcc_channel=DEFAULT_PCC_CHANNELS[1]))
# Reuse the original routine's five-row plotting code; adapt page size/font and remove redundant titles.
# Keep the original function in a provenance copy. Output uses identical plot layers, colors, and line roles.
code=inspect.getsource(make_dual_plot);(P/'revision_materials/author_review/original_detection_plot_function.py').write_text(code)
code=code.replace('def make_dual_plot(', 'def original_style_plot(').replace('figsize=(14, 10)','figsize=(3.5, 5.2)').replace('fontsize=8','fontsize=9.5').replace('fontsize=9,','fontsize=9.5,')
code=code.replace("f\"{interval['severity_label']:.1f}\"", "f\"{interval['severity_label']:.2f}\"")
code=code.replace('ha="center", va="center", fontsize=9.5','ha="center", va="center", fontsize=9.5, rotation=90')
code=code[:code.index('    fig.tight_layout()')]+'''    for ax in axes:
        ax.set_title('')
        ax.set_xlim(start_second, start_second+duration_seconds)
        ax.tick_params(labelsize=9.5)
    sched_ax.set_title(('(a) 0–200 s' if duration_seconds==200 else '(b) 0–22 s'),fontsize=10)
    motor_sig_ax.set_ylabel('Motor\\nRMS')
    pcc_sig_ax.set_ylabel('PCC\\nRMS')
    motor_score_ax.set_ylabel('Motor\\nscore')
    pcc_score_ax.set_ylabel('PCC\\nscore')
    motor_score_ax.get_legend().remove()
    return fig, axes
'''
namespace=dict(make_dual_plot.__globals__);exec(code,namespace);plot=namespace['original_style_plot'];panels=[]
for duration in [200,22]:
 bs,intervals,folder=bundles['acim'];fig,axs=plot(folder,bs['motor'],bs['pcc'],intervals,0,duration,F/'unused',.2,'feature_trace','rms','mean',True)
 # Store separate vector panels; TeX combines them without shrinking font sizes.
 name='figure6_overview_original_style' if duration==200 else 'figure6_zoom_original_style';save(fig,name);panels.append(name)
# Three-row schedule/RMS figure for both motor families, same palette and continuous RMS convention.
fig,axs=plt.subplots(3,2,figsize=(7.16,3.9),sharex='col',gridspec_kw={'height_ratios':[.7,1.2,1.2]})
for col,motor in enumerate(['acim','pmsm']):
 bs,intervals,folder=bundles[motor]
 for it in intervals:
  a,b=it['start_second'],it['end_second']
  if a>=200:continue
  attack=it['segment_type']=='attack';axs[0,col].axvspan(a,min(b,200),color='#fb6a4a' if attack else '#9ecae1',alpha=.85)
  if attack:
   axs[0,col].text((a+min(b,200))/2,.5,f'{it["severity_label"]:.2f}',ha='center',va='center',rotation=90,fontsize=9.5)
   for ax in axs[1:,col]:ax.axvspan(a,min(b,200),color='#fb6a4a',alpha=.10)
 axs[0,col].set(yticks=[],ylim=(0,1),ylabel='Bias (%)',title=motor.upper())
 for row,stream,color in [(1,'motor','#08519c'),(2,'pcc','#6a51a3')]:
  b=bs[stream];t,y=compute_continuous_feature_trace(b['raw_data'][:int(200*b['fs']),0],b['fs'],'rms',0);axs[row,col].plot(t,y,color=color,lw=.55);axs[row,col].set_ylabel(stream.upper()+' RMS');axs[row,col].grid(alpha=.2)
 axs[-1,col].set(xlim=(0,200),xlabel='Time (s)')
save(fig,'figure8_original_style')
# Regression: all attack windows in each repeat, no cherry-picked runs or clipped predictions.
fig,axs=plt.subplots(1,2,figsize=(7.16,3.3));reg=[];seedcolors=['#285279','#d95f02','#39755c']
for ax,stream in zip(axs,['motor','pcc']):
 for j,seed in enumerate([1234,2234,3234]):
  a=pd.read_csv(C/'auxiliary/regression'/stream/str(seed)/'predictions.csv');assert (a.target_binary==1).all();a['bias']=a['true'].round(6);g=a.groupby('bias').predicted
  summary=g.quantile([.1,.5,.9]).unstack();med=summary[.5];ax.errorbar(summary.index+(j-1)*.004,med,yerr=[med-summary[.1],summary[.9]-med],fmt=['o','s','^'][j],ms=3,capsize=2,lw=.8,color=seedcolors[j],label=str(seed))
  for bias,n in summary.iterrows():reg.append(dict(stream=stream,seed=seed,true_bias_percentage_points=bias,p10=n[.1],median=n[.5],p90=n[.9],n=int(g.count().loc[bias])))
 ax.plot([0,.55],[0,.55],'--',color='#777777',lw=.9);ax.set(title=stream.upper(),xlabel='True injected bias (%)',ylabel='Predicted bias (%)',xlim=(.025,.525));ax.grid(alpha=.2)
fig.legend(*axs[0].get_legend_handles_labels(),loc='upper center',ncol=3,title='Holdout seed',frameon=False,bbox_to_anchor=(.5,1.02));save(fig,'regression_diagnostics');pd.DataFrame(reg).to_csv(D/'regression_figure_quantiles.csv',index=False)
(F/'author_review_figure_provenance.json').write_text(json.dumps({'style':style,'recordings':recordings,'detection_source':'plot_dual_stream_detection_over_signal.py::make_dual_plot; original code archived in revision_materials/author_review/','notes':['Timeline and RMS figures preserve original color/layer conventions but use corrected held-out predictions and documented maximum-bias schedules.','Regressions show all saved attack-window predictions by repeat.','Feature importance is ranked from validation data; whiskers are sample SD across repeats.','Matrix percentages are pooled row-normalized counts; no test outputs were regenerated.']},indent=2)+'\n')
print('Generated original-style diagnostics, single-column matrices, and regression figure from saved results.')
