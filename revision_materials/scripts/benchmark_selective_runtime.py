"""Validate selective extraction, then time the existing paper models without fitting.

Run with the original experiment workspace available:
  python revision_materials/scripts/benchmark_selective_runtime.py --workspace PATH --output PATH
All variants, including full and family ablations, use the same selective extractor.
"""
import argparse
from pathlib import Path
import sys, os, json, hashlib, time, platform, subprocess
from datetime import datetime, timezone
from unittest.mock import patch
import numpy as np
import pandas as pd
import selective_feature_extraction as fe

REPO = Path(__file__).resolve().parents[2]
PRUNED = ['top75', 'top50', 'top25', 'per_channel15', 'per_channel10']
ABLATIONS = ['lf_only', 'hf_only', 'time_only', 'lf_hf', 'lf_time', 'hf_time']
SEEDS = [1234, 2234, 3234]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, default=str) + '\n')


def load_raw(workspace, folder, seconds):
    from nptdms import TdmsFile
    sources = sorted((workspace / '540case_for_shushan_paper_final_20260220' / folder).glob('*.tdms'))
    start, stop = int(round(seconds * 10000)), int(round(seconds * 10000)) + 2000
    specs = [(f'cDAQ9185-1EF7B78Mod2/ai{i}',) for i in range(6)] + [('cDAQ9185-1EF7B78Mod3/ai2', 'cDAQ9185-1EF7B78Mod3/neutral'), ('cDAQ9185-1EF7B78Mod4/ai0',)]
    parts, offsets, used = [[] for _ in specs], [0] * len(specs), []
    # Mirror read_tdms_folder: concatenate each signal independently; voltage
    # differences are formed within each file, using its shorter channel length.
    for source in sources:
        with TdmsFile.open(source) as t:
            g = t['Log']
            touched = False
            for i, names in enumerate(specs):
                n = min(len(g[name]) for name in names)
                lo, hi = max(0, start - offsets[i]), min(n, stop - offsets[i])
                if lo < hi:
                    a = np.asarray(g[names[0]][lo:hi], dtype=np.float64)
                    if len(names) == 2:
                        a = a - np.asarray(g[names[1]][lo:hi], dtype=np.float64)
                    parts[i].append(a)
                    touched = True
                offsets[i] += n
            if touched:
                used.append(str(source.relative_to(workspace)))
        if min(offsets) >= stop:
            break
    assert all(p and sum(len(a) for a in p) == 2000 for p in parts), (folder, seconds)
    a = np.column_stack([np.concatenate(p) for p in parts])
    return {'motor': a[:, :6], 'pcc': a[:, 6:]}, ';'.join(used)


def models(workspace, stream, seed, include_ablations=True):
    runs = pd.read_csv(REPO / 'revision_materials/data/main_runs.csv')
    path = Path(runs.query('task == "binary" and stream == @stream and seed == @seed').iloc[0].model_path)
    if not path.is_absolute():
        path = workspace / path
    root = workspace / 'reviewer_revision/full_paper_rerun'
    out = {'full': path}
    out.update({v: root / 'pruning' / stream / str(seed) / v for v in PRUNED})
    if include_ablations:
        out.update({v: root / 'ablations/binary' / stream / str(seed) / v for v in ABLATIONS})
    return out


def old_extract(old, raw):
    return old.extract_window_features_per_channel(raw, 10000., 2000, 500, 250, 25, 29, fixed_time_steps=61)[0]


def validate(old, workspace, output, torch, load_model):
    checks = []
    def same(name, got, expected):
        np.testing.assert_array_equal(got, expected, err_msg=name)
        checks.append({'check': name, 'values': int(got.size), 'maximum_absolute_difference': float(np.max(np.abs(got - expected))) if got.size else 0.})
    rng = np.random.default_rng(61504)
    # Independent old extractor is the oracle; include degenerate and interpolation cases.
    for label, raw in [('noise', rng.normal(size=(2000, 2))), ('zero', np.zeros((2000, 2))), ('constant', np.ones((2000, 2)))]:
        ref = old_extract(old, raw)
        same(label + '/full', fe.extract_window_features_per_channel(raw)[0], ref)
        for k in range(37):
            same(label + '/' + fe.FEATURE_NAMES[k], fe.extract_window_features_per_channel(raw, selected_feature_indices=[k])[0], ref[:, :, [k]])
        indices = np.array([73, 15, 36, 0, 15])
        same(label + '/reordered_duplicate', fe.extract_window_features_per_channel(raw, selected_feature_indices=indices)[0], ref[:, :, indices])
        same(label + '/empty', fe.extract_window_features_per_channel(raw, selected_feature_indices=[])[0], ref[:, :, []])
    raw = rng.normal(size=(4000, 2))
    ref = old.extract_window_features_per_channel(raw, 10000., 2000, 500, 250, 25, 31, fixed_time_steps=47)[0]
    same('multiwindow/interpolation', fe.extract_window_features_per_channel(raw, hf_stride_samples=31, fixed_time_steps=47)[0], ref)
    assert fe.extract_window_features_per_channel(raw[:1999])[0].shape == (0, 61, 74)
    # Fail if isolated feature paths perform unrelated expensive operations.
    def forbidden(*a, **kw):
        raise AssertionError('Unused calculation was executed')
    with patch.object(fe, 'compute_spectrum', forbidden), patch.object(fe, 'fft_bandpass', forbidden), patch.object(fe, 'analytic_signal', forbidden), patch.object(fe, 'stable_kurtosis', forbidden), patch.object(fe, 'stable_skewness', forbidden):
        fe.extract_window_features_per_channel(raw[:2000], selected_feature_indices=[29])
    with patch.object(fe, 'fft_bandpass', forbidden), patch.object(fe, 'analytic_signal', forbidden), patch.object(fe, 'stable_kurtosis', forbidden):
        fe.extract_window_features_per_channel(raw[:2000], selected_feature_indices=[20])
    with patch.object(fe, 'compute_spectrum', forbidden), patch.object(fe, 'analytic_signal', forbidden):
        fe.extract_window_features_per_channel(raw[:2000], selected_feature_indices=[18])
    with patch.object(fe.np, 'angle', forbidden), patch.object(fe.np, 'argmin', forbidden), patch.object(fe.np, 'gradient', forbidden):
        fe.extract_window_features_per_channel(raw[:2000], selected_feature_indices=[0])
    cache = []
    folders = pd.read_csv(workspace / 'reviewer_revision/full_paper_rerun/splits/1234/recordings.csv')
    representatives = {motor: frame.folder_name.iloc[0] for motor, frame in folders.groupby('motor_type')}
    # All 18 recordings, normal/attack/tail windows; saved input arrays are an additional oracle.
    meta = pd.read_csv(workspace / 'tdms_lfhf_per_channel_w2000_lf500_hf250_s25_s29/metadata.csv')
    saved = {s: np.load(workspace / f'tdms_lfhf_per_channel_w2000_lf500_hf250_s25_s29/X_{s}.npy', mmap_mode='r') for s in ['pcc', 'motor']}
    for row in folders.itertuples():
        for seconds, kind in [(0., 'normal'), (15., 'attack'), (610., 'tail')]:
            raw, source = load_raw(workspace, row.folder_name, seconds)
            ix = meta.index[(meta.folder_name == row.folder_name) & np.isclose(meta.window_start_second, seconds)].item()
            refs = {}
            for stream in ['pcc', 'motor']:
                refs[stream] = old_extract(old, raw[stream])
                value = fe.extract_window_features_per_channel(raw[stream])[0]
                same(f'{row.folder_name}/{kind}/{stream}/archived', value, refs[stream])
                same(f'{row.folder_name}/{kind}/{stream}/saved', value.astype('float32')[0], np.asarray(saved[stream][ix], dtype='float32'))
            if row.folder_name in representatives.values():
                cache.append((row.folder_name, kind, raw, refs))
    print('Full features match archived functions and stored tensors for all 18 recordings.', flush=True)
    model_hashes = []
    feature_plans = []
    for stream in ['pcc', 'motor']:
        for seed in SEEDS:
            for variant, modeldir in models(workspace, stream, seed, include_ablations=seed == 1234).items():
                norm = np.load(modeldir / 'normalization.npz')
                cols = norm['feature_indices']
                plan = fe.compile_global_feature_plan(cols, 2 if stream == 'pcc' else 6)
                model, _ = load_model(modeldir, torch.device('cpu'))
                model.eval()
                for folder, kind, raw, refs in cache:
                    got = fe.extract_window_features_per_channel(raw[stream], feature_plan=plan)[0]
                    expected = refs[stream][:, :, cols]
                    same(f'{stream}/{seed}/{variant}/{folder}/{kind}', got, expected)
                    a, b = got.astype('float32'), expected.astype('float32')
                    for v in [a, b]:
                        v -= norm['mean'].astype('float32')
                        v /= norm['std'].astype('float32')
                    with torch.no_grad():
                        logits_a = model(torch.from_numpy(a)).numpy()
                        logits_b = model(torch.from_numpy(b)).numpy()
                    same(f'{stream}/{seed}/{variant}/{folder}/{kind}/logits', logits_a, logits_b)
                for ch in plan.channels:
                    feature_plans.append(dict(stream=stream, seed=seed, variant=variant, channel=ch.channel + 1, output_count=len(ch.names), outputs=';'.join(ch.names), low_required=';'.join(sorted(ch.low)), hf_required=';'.join(sorted(ch.hf)), time_required=';'.join(sorted(ch.time)), derivative_required=';'.join(ch.derivatives)))
                model_hashes.append({'stream': stream, 'seed': seed, 'variant': variant, 'model': str(modeldir.relative_to(workspace)), 'model_sha256': digest(modeldir / 'model.pt'), 'normalization_sha256': digest(modeldir / 'normalization.npz')})
            print('Verified all saved subsets:', stream, seed, flush=True)
    pd.DataFrame(checks).to_csv(output / 'equivalence_checks.csv', index=False)
    pd.DataFrame(feature_plans).to_csv(output / 'feature_plans.csv', index=False)
    save(output / 'model_hashes.json', model_hashes)
    save(output / 'validation.json', {'passed': True, 'comparison': 'Exact array equality; no numerical tolerance', 'checks': len(checks), 'values_compared': sum(c['values'] for c in checks), 'max_absolute_difference': 0., 'recordings': 18, 'contexts': ['normal', 'attack', 'post-schedule normal'], 'saved_input_tensor_comparison': 'Exact equality at model input precision (float32); extractor-to-extractor equality at float64', 'all_pruning_subsets_and_seeds_verified': True, 'unused_calculation_guards_passed': True, 'model_logits_exact': True, 'retraining': False})


def benchmark(workspace, output, torch, load_model):
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA required for the paper GPU-assisted timing; no CPU substitution')
    rng = np.random.default_rng(20261105)
    raw, source = load_raw(workspace, 'case1_30_spd_900_ld1', 0.)
    rows = []
    for stream in ['pcc', 'motor']:
        for device in ['cuda', 'cpu']:
            variants = {}
            for variant, path in models(workspace, stream, 1234).items():
                norm = np.load(path / 'normalization.npz')
                model, _ = load_model(path, torch.device(device))
                model.eval()
                variants[variant] = (model, norm['mean'].astype('float32'), norm['std'].astype('float32'), fe.compile_global_feature_plan(norm['feature_indices'], raw[stream].shape[1]), str(path.relative_to(workspace)))
            def run(variant):
                model, mean, std, plan, path = variants[variant]
                if device == 'cuda':
                    torch.cuda.synchronize()
                t0 = time.perf_counter_ns()
                a = fe.extract_window_features_per_channel(raw[stream], feature_plan=plan)[0].astype('float32')
                t1 = time.perf_counter_ns()
                a -= mean
                a /= std
                model(torch.from_numpy(a).to(device))
                if device == 'cuda':
                    torch.cuda.synchronize()
                t2 = time.perf_counter_ns()
                return ((t1 - t0) / 1e6, (t2 - t1) / 1e6, (t2 - t0) / 1e6)
            with torch.no_grad():
                for repeat in range(10):
                    for variant in rng.permutation(list(variants)):
                        run(variant)
                for repeat in range(50):
                    for order, variant in enumerate(rng.permutation(list(variants))):
                        times = run(variant)
                        plan, path = variants[variant][3:]
                        for stage, ms in zip(['feature_extraction', 'normalization_transfer_inference', 'end_to_end_processing'], times):
                            rows.append(dict(stream=stream, feature_set=variant, features=len(plan.indices), device=device, stage=stage, seed=1234, model_path=path, repeat=repeat, order=order, ms=ms))
            print('Completed timings:', stream, device, flush=True)
            del variants
            torch.cuda.empty_cache()
    samples = pd.DataFrame(rows)
    samples.to_csv(output / 'samples.csv', index=False)
    keys = ['stream', 'feature_set', 'features', 'device', 'stage', 'seed', 'model_path']
    summary = samples.groupby(keys).ms.agg(median_ms='median', p95_ms=lambda x: x.quantile(.95), p25_ms=lambda x: x.quantile(.25), p75_ms=lambda x: x.quantile(.75), repetitions='count').reset_index()
    summary['acquisition_ms'] = 200
    summary.to_csv(output / 'summary.csv', index=False)
    table = []
    for stream in ['pcc', 'motor']:
        part = summary.query('stream == @stream and device == "cuda"')
        base = part.query('feature_set == "full" and stage == "end_to_end_processing"').median_ms.item()
        for variant in ['full'] + PRUNED + ABLATIONS:
            sub = part.query('feature_set == @variant').set_index('stage')
            table.append(dict(stream=stream, variant=variant, features=int(sub.features.iloc[0]), extraction_ms=sub.loc['feature_extraction', 'median_ms'], total_ms=sub.loc['end_to_end_processing', 'median_ms'], total_p95_ms=sub.loc['end_to_end_processing', 'p95_ms'], speedup=base / sub.loc['end_to_end_processing', 'median_ms']))
    pd.DataFrame(table).to_csv(output / 'runtime_table.csv', index=False)
    protocol = {'created_utc': datetime.now(timezone.utc).isoformat(), 'extractor': 'selective_feature_extraction.py', 'extractor_sha256': digest(Path(fe.__file__)), 'benchmark_sha256': digest(__file__), 'reference_extractor_sha256': digest(workspace / 'tdms_to_numpy_continues_lfhf_per_channel.py'), 'raw_source': source, 'raw_start_second': 0., 'raw_window_sha256': {s: hashlib.sha256(a.tobytes()).hexdigest() for s, a in raw.items()}, 'seed': 1234, 'warmup_executions_per_variant_device': 10, 'timed_repetitions_per_variant_device': 50, 'variant_order': 'Random permutation each repetition; deterministic RNG seed 20261105', 'scope': 'In-memory 2000-sample raw window through selected-feature extraction, float32 conversion, normalization, transfer and batch-one inference; acquisition and disk I/O excluded; plan compilation outside loop', 'full_baseline': 'Same selective implementation and benchmark session; all features requested', 'features': {'LF_frame': 500, 'HF_frame': 250, 'LF_stride': 25, 'HF_stride': 29, 'steps': 61, 'sample_rate': 10000}, 'devices': ['cpu', 'cuda'], 'torch_threads': torch.get_num_threads(), 'torch': torch.__version__, 'numpy': np.__version__, 'python': sys.version, 'platform': platform.platform(), 'gpu': torch.cuda.get_device_name(0), 'cpu': subprocess.check_output(['lscpu'], text=True), 'limitation': 'One recorded window on one workstation; external system load not controlled; not embedded worst-case timing', 'performance_metrics': 'Existing three-split BA/F1 retained; exact feature and logits equality checked, no retraining'}
    save(output / 'protocol.json', protocol)
    print(pd.DataFrame(table).query('variant in @PRUNED or variant == "full"').to_string(index=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=REPO.parent)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(workspace))
    os.environ.setdefault('OMP_NUM_THREADS', '4')
    import torch
    import tdms_to_numpy_continues_lfhf_per_channel as old
    from reviewer_revision.full_paper_core import load_model
    torch.set_num_threads(4)
    validate(old, workspace, args.output, torch, load_model)
    benchmark(workspace, args.output, torch, load_model)
    save(args.output / 'complete.json', {'state': 'complete', 'retrained': False})


if __name__ == '__main__':
    main()
