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
fig,ax=canvas(2.75)
box(ax,.05,2.05,1.05,.8,'AC supply\nShared PCC');box(ax,1.55,2.05,1.1,.8,'Rectifier');arrow(ax,(1.1,2.45),(1.55,2.45));ax.plot([3,3],[1.05,3.85],color=blue);arrow(ax,(2.65,2.45),(3,2.45));ax.text(2.97,4.25,'DC bus',ha='center')
for y,m in [(3.5,'PMSM'),(.75,'ACIM')]:
 box(ax,3.55,y,1.15,.7,'Inverter');box(ax,5.2,y,1.05,.7,m);box(ax,6.8,y,1.05,.7,'Load')
 arrow(ax,(3,y+.35),(3.55,y+.35));arrow(ax,(4.7,y+.35),(5.2,y+.35));arrow(ax,(6.25,y+.35),(6.8,y+.35))
 cy=y-.85 if y>2 else y+.95
 box(ax,4.3,cy,1.65,.6,'Drive controller',green)
 arrow(ax,(4.5,cy+(.6 if y>2 else 0)),(4.1,y+(0 if y>2 else .7)),green)
 ax.text(6.7,cy+.3,'Biased current\nfeedback',ha='center',va='center',color=red)
 arrow(ax,(5.8,y+(0 if y>2 else .7)),(5.8,cy+(.6 if y>2 else 0)),red,'--')
box(ax,8.3,1.15,1.6,2.45,'Trusted\nmonitoring\n\nPCC: V + I\nMotor: 6 I\n10 kHz',green)
# Trusted taps are distinct from compromised feedback paths.
ax.plot([1.3,1.3,8.1,8.1],[2.45,.05,.05,2.2],color=green,lw=.8,ls='--');arrow(ax,(8.1,2.2),(8.3,2.2),green,'--')
ax.plot([4.95,4.95,9.1],[3.85,4.8,4.8],color=green,lw=.8,ls='--');arrow(ax,(9.1,4.8),(9.1,3.6),green,'--')
ax.plot([4.95,4.95,9.1],[1.1,.15,.15],color=green,lw=.8,ls='--');arrow(ax,(9.1,.15),(9.1,1.15),green,'--')
ax.text(1.35,.45,'Two motor families × three speeds × three load settings',ha='left')
save(fig,'figure1_platform')
fig,ax=canvas(2.45)
box(ax,.05,1.7,1.55,1.15,'Input sequence\n61 × 222 (motor)\n61 × 74 (PCC)')
box(ax,2.0,1.8,1.2,.95,'1 × 1\nbottleneck')
arrow(ax,(1.6,2.27),(2,2.27))
for y,k in [(3.5,39),(2.5,19),(1.5,9)]:
 box(ax,3.8,y,1.3,.65,f'Conv1D\nk = {k}');arrow(ax,(3.2,2.27),(3.8,y+.325));arrow(ax,(5.1,y+.325),(5.7,2.6))
box(ax,3.8,.25,1.3,.85,'MaxPool\n+ 1 × 1');arrow(ax,(1.55,1.7),(3.8,.67));arrow(ax,(5.1,.67),(5.7,2.2))
box(ax,5.7,1.75,1.25,1.15,'Concat\nBN + ReLU')
box(ax,7.45,1.75,2.4,1.15,'Repeat modules\nGlobal average pooling\nDropout → dense')
arrow(ax,(6.95,2.3),(7.45,2.3));ax.text(5,4.65,'Projected residual shortcut after every three modules',ha='center',color=red)
ax.text(8.6,.65,'Softmax: 2 or 4 classes',ha='center');arrow(ax,(8.6,1.75),(8.6,.95))
save(fig,'figure3_architecture')
fig,ax=canvas(2.3)
steps=[(.05,1.65,'Trusted sensors\nMotor: 6 currents\nPCC: voltage/current'),(2.6,1.7,'Window acquisition\n2,000 samples\n0.2 s at 10 kHz'),(5.15,1.75,'LF / HF / TD\n61 temporal steps\nNormalize inputs'),(7.7,2.2,'Selected model\nBinary or severity\nAlarm + logging')]
for x,w,t in steps:box(ax,x,2.7,w,1.4,t)
for a,b in [(1.7,2.6),(4.3,5.15),(6.9,7.7)]:arrow(ax,(a,3.4),(b,3.4))
box(ax,.1,.25,2.85,1.35,'Training recordings\nFit normalization + models',green)
box(ax,3.6,.25,2.85,1.35,'Validation recordings\nSelect model + rank features',green)
box(ax,7.1,.25,2.8,1.35,'Test recordings\nEvaluate once per condition',green)
ax.text(5,2.05,'Whole recordings and all their episodes remain in one partition',ha='center')
save(fig,'figure4_pipeline')
# Load only the two pre-specified held-out recordings. Correct PCC current is channel 2.
from tdms_to_numpy import read_tdms_folder,DEFAULT_ACIM_MOTOR_CHANNELS,DEFAULT_PMSM_MOTOR_CHANNELS,DEFAULT_PCC_CHANNELS
from tdms_to_numpy_continues_lfhf_per_channel import compute_low_features,compute_hf_features,compute_time_features
manifest=pd.read_csv(C/'splits/1234/manifest.csv');raws={};sources=[]
for motor in ['acim','pmsm']:
 m=manifest[(manifest.motor_type==motor)&(manifest.split=='test')];folder=sorted(m.folder_name.unique())[0];m=m[m.folder_name==folder].sort_values('window_start_second')
 channel=(DEFAULT_ACIM_MOTOR_CHANNELS if motor=='acim' else DEFAULT_PMSM_MOTOR_CHANNELS)[0]
 raw,fs=read_tdms_folder(W/'540case_for_shushan_paper_final_20260220'/folder,(channel,DEFAULT_PCC_CHANNELS[1]));raws[motor]=(raw,fs,m,folder)
 sources.append({'motor':motor,'recording':folder,'motor_channel':channel,'pcc_channel':DEFAULT_PCC_CHANNELS[1],'split':'test','seed':1234})
raw,fs,m,folder=raws['acim'];onset=10.;start=int((onset-.2)*fs);stop=int((onset+.2)*fs);t=(np.arange(start,stop)/fs-onset)*1000
fig,axs=plt.subplots(4,2,figsize=(7.16,4.6),sharex=True)
for j,name in enumerate(['Motor current','PCC current']):
 x=raw[start:stop,j];axs[0,j].plot(t,x,color='#333333',lw=.6);axs[0,j].set_title(name)
 lf=np.arange(0,len(x)-500+1,25);hf=np.arange(0,len(x)-250+1,29)
 y1=[compute_time_features(x[i:i+500])['rms'] for i in lf];y2=[compute_low_features(x[i:i+500],fs)['thd'] for i in lf];y3=[compute_hf_features(x[i:i+250],fs)['hf_energy_ratio'] for i in hf]
 for row,ts,ys,color in [(1,(lf+250)/fs*1000-200,y1,blue),(2,(lf+250)/fs*1000-200,y2,green),(3,(hf+125)/fs*1000-200,y3,red)]:axs[row,j].plot(ts,ys,color=color)
 for i,label in enumerate(['Amplitude','TD RMS','LF THD','HF energy\nratio']):
  axs[i,j].set_ylabel(label);axs[i,j].axvline(0,color='gray',ls='--',lw=.7);axs[i,j].ticklabel_format(axis='y',style='sci',scilimits=(-2,3));axs[i,j].grid(alpha=.15)
 axs[-1,j].set_xlabel('Time relative to scheduled onset (ms)')
save(fig,'figure2_feature_example')
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
(F/'revision_figure_provenance.json').write_text(json.dumps({'style':style,'source_recordings':sources,'note':'All new data plots use saved results or existing recordings. No new fitting. PCC current uses DEFAULT_PCC_CHANNELS[1]; channel 0 is voltage. Figures 1/3/4 are conceptual diagrams of the existing apparatus/implemented pipeline.'},indent=2))
print('Generated vector figures 1–4, 8 and sensitivity, with Times-family typography.')
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
