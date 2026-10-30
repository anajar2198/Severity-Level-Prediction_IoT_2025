"""Publication figures from saved data; does not fit or evaluate new models."""
from pathlib import Path
import sys,json
P=Path(__file__).resolve().parents[2];W=P.parent;sys.path.insert(0,str(W))
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from reviewer_revision.paper_figure_style import apply_paper_style,save_paper_figure
style=apply_paper_style();F=P/'figs_revised';F.mkdir(exist_ok=True)
D=P/'revision_materials/data';C=W/'reviewer_revision/full_paper_rerun'
blue='#285279';green='#39755c';red='#a63737'
def save(fig,name):save_paper_figure(fig,F/name);plt.close(fig)
def canvas(height):
 fig,ax=plt.subplots(figsize=(7.16,height));ax.set(xlim=(0,10),ylim=(0,5));ax.axis('off');return fig,ax
def box(ax,x,y,w,h,text,color=blue,fs=10):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.025,rounding_size=0.07',edgecolor=color,facecolor='#f4f7fa',lw=.9));ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=fs)
def arrow(ax,a,b,color=blue,style='-'):
 ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',color=color,lw=1,linestyle=style))
# Figures 1–4 preserve the original artwork; see preserve_original_figures.py.
# Load only the two pre-specified held-out recordings. Correct PCC current is channel 2.
from tdms_to_numpy import read_tdms_folder,DEFAULT_ACIM_MOTOR_CHANNELS,DEFAULT_PMSM_MOTOR_CHANNELS,DEFAULT_PCC_CHANNELS
from tdms_to_numpy_continues_lfhf_per_channel import compute_low_features,compute_hf_features,compute_time_features
manifest=pd.read_csv(C/'splits/1234/manifest.csv');raws={};sources=[]
for motor in ['acim','pmsm']:
 m=manifest[(manifest.motor_type==motor)&(manifest.split=='test')];folder=sorted(m.folder_name.unique())[0];m=m[m.folder_name==folder].sort_values('window_start_second')
 channel=(DEFAULT_ACIM_MOTOR_CHANNELS if motor=='acim' else DEFAULT_PMSM_MOTOR_CHANNELS)[0]
 raw,fs=read_tdms_folder(W/'540case_for_shushan_paper_final_20260220'/folder,(channel,DEFAULT_PCC_CHANNELS[1]));raws[motor]=(raw,fs,m,folder)
 sources.append({'motor':motor,'recording':folder,'motor_channel':channel,'pcc_channel':DEFAULT_PCC_CHANNELS[1],'split':'test','seed':1234})
fig,axs=plt.subplots(3,2,figsize=(7.16,4.1),sharex='col')
for col,motor in enumerate(['acim','pmsm']):
 raw,fs,m,folder=raws[motor];n=len(raw)//2000*2000;rms=np.sqrt(np.mean(raw[:n].reshape(-1,2000,2)**2,axis=1));t=(np.arange(len(rms))+1)*.2
 axs[0,col].step(m.window_start_second,m.target_regression,where='post',color=red);axs[0,col].set_title(motor.upper())
 for j in range(2):axs[j+1,col].plot(t,rms[:,j],lw=.65,color=blue if j==0 else green)
 for i,label in enumerate(['Max bias (%)','Motor RMS','PCC RMS']):axs[i,col].set_ylabel(label);axs[i,col].axvline(600,ls=':',color='gray');axs[i,col].grid(alpha=.15)
 axs[-1,col].set_xlabel('Recording time (s)')
save(fig,'figure8_raw_rms')
# Additional sensitivity figure reports every named perturbation; no test-based selection.
S=pd.read_csv(D/'sensitivity_summary.csv');M=pd.read_csv(D/'main_mean_sd.csv');variants=['selected','depth3','depth9','dropout01','dropout04','lr00003','lr0003'];labels=['Selected','Depth 3','Depth 9','Dropout 0.1','Dropout 0.4','LR 0.0003','LR 0.003']
fig,axs=plt.subplots(2,2,figsize=(7.16,4.6),sharex=True)
for i,task in enumerate(['binary','severity']):
 for j,stream in enumerate(['motor','pcc']):
  ax=axs[i,j];means=[];sd=[]
  for v in variants:
   n=M[(M.task==task)&(M.stream==stream)].iloc[0] if v=='selected' else S[(S.task==task)&(S.stream==stream)&(S.variant==v)].iloc[0];means.append(n.test_bal_acc_mean*100);sd.append(n.test_bal_acc_std*100)
  y=np.arange(len(labels));ax.errorbar(means,y,xerr=sd,fmt='o',capsize=2,color=blue,ms=4);ax.set(yticks=y,yticklabels=labels,title=f'{stream.upper()}: {task}',xlim=(40,105));ax.invert_yaxis();ax.grid(axis='x',alpha=.2);ax.set_xlabel('Balanced accuracy (%)')
save(fig,'hyperparameter_sensitivity')
(F/'revision_figure_provenance.json').write_text(json.dumps({'style':style,'source_recordings':sources,'note':'All new data plots use saved results or existing recordings. No new fitting. PCC current uses DEFAULT_PCC_CHANNELS[1]; channel 0 is voltage. Figures 1–4 retain original artwork; see original_figure_restoration.json for corrections and separate provenance.'},indent=2))
print('Generated figure 8 and sensitivity with Times-family typography.')
# Re-export existing confusion/importance/timeline results at compact print sizes.
from reviewer_revision.full_paper_figures import heat
labels=['Normal','Low','Medium','High']
fig,axs=plt.subplots(2,2,figsize=(7.16,4.6))
for i,task in enumerate(['binary','severity']):
 for j,stream in enumerate(['motor','pcc']):
  cm=pd.read_csv(D/f'{task}_{stream}_confusion_counts.csv',index_col=0).to_numpy();lab=labels if task=='severity' else ['Normal','Attack'];heat(axs[i,j],cm,lab,lab,f'({"abcd"[i*2+j]}) {stream.upper()}: {task}')
save(fig,'figure5_confusion_matrices')
cm=pd.read_csv(D/'severity_pcc_confusion_counts.csv',index_col=0).to_numpy();dec=np.column_stack([cm[:,0],cm[:,1:].sum(1)]);binary=np.array([[cm[0,0],cm[0,1:].sum()],[cm[1:,0].sum(),cm[1:,1:].sum()]])
fig=plt.figure(figsize=(7.16,4.6));g=fig.add_gridspec(2,2);axs=[fig.add_subplot(g[:,0]),fig.add_subplot(g[0,1]),fig.add_subplot(g[1,1])]
heat(axs[0],cm,labels,labels,'(a) Exact severity');heat(axs[1],dec,labels,['Normal','Any attack'],'(b) Decision by true severity');heat(axs[2],binary,['Normal','Attack'],['Normal','Attack'],'(c) Collapsed binary decision');save(fig,'pcc_severity_and_detection_confusions')
from tdms_to_numpy_continues_lfhf_per_channel import LOW_FEATURE_NAMES,HF_FEATURE_NAMES,TIME_FEATURE_NAMES
names=list(LOW_FEATURE_NAMES)+list(HF_FEATURE_NAMES)+list(TIME_FEATURE_NAMES)
fig,axs=plt.subplots(2,1,figsize=(7.16,4.6))
for ax,stream in zip(axs,['motor','pcc']):
 r=pd.concat([pd.read_csv(D/f'importance_{stream}_{seed}.csv') for seed in [1234,2234,3234]]);r=r.groupby('feature_index').importance_drop_bal_acc.agg(['mean','std']).sort_values('mean').tail(10)
 lab=[f'Ch {int(i)//37+1}: {names[int(i)%37]}' for i in r.index];ax.barh(lab,100*r['mean'],xerr=100*r['std'],color=blue);ax.set(title=stream.upper(),xlabel='Validation BA decrease (percentage points)')
save(fig,'figure7_validation_feature_importance')
main=pd.read_csv(D/'main_runs.csv')
for motor in ['acim','pmsm']:
 _,_,m,folder=raws[motor];fig,axs=plt.subplots(3,1,figsize=(7.16,3.7),sharex=True)
 axs[0].step(m.window_start_second,m.target_binary,where='post',color=red);axs[0].set_ylabel('Attack label');axs[0].set_yticks([0,1]);axs[0].set_title(f'Held-out {motor.upper()} recording; seed 1234')
 for j,stream in enumerate(['motor','pcc']):
  n=main[(main.task=='binary')&(main.stream==stream)&(main.seed==1234)].iloc[0];a=pd.read_csv((Path(n.model_path) if Path(n.model_path).is_absolute() else W/str(n.model_path))/'predictions.csv');a=a[a.folder_name==folder].sort_values('window_end_second');prob=a.p_class1 if 'p_class1' in a else a.p_attack
  axs[j+1].plot(a.window_end_second,prob,color=blue,lw=.65,label='Attack probability');axs[j+1].step(a.window_end_second,a.predicted,where='post',color='#ca8026',alpha=.7,lw=.65,label='Decision');axs[j+1].set_ylabel(stream.upper());axs[j+1].set_yticks([0,.5,1]);axs[j+1].legend(loc='upper right',ncol=2)
 axs[-1].set_xlabel('Recording time (s); predictions at window end');save(fig,f'figure6_heldout_{motor}')
print('Re-exported saved result figures at compact dimensions without reducing font sizes.')

# Restore original artwork after regeneration, keeping original traces untouched.
import subprocess
subprocess.run([sys.executable,str(P/'revision_materials/scripts/preserve_original_figures.py')],check=True)

# Apply author-requested presentation after the base figure build.
subprocess.run([sys.executable,str(P/'revision_materials/scripts/make_author_review_figures.py')],check=True)
