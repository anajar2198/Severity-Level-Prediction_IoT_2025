"""Compute selected LF/HF/TD statistics and their dependencies only.

Definitions and numerical operation order match the archived 37-feature extractor.
No model fitting, feature reranking, or label changes. Plans are compiled once,
outside per-window timing. Input column ordering (including duplicates) is retained.
"""
from dataclasses import dataclass
import numpy as np

FEATURE_EPS = 1e-8
FEATURE_NAMES = (
    'a1', 'f1', 'phi1', 'thd', 'h2_h1', 'h3_h1', 'h5_h1', 'h7_h1',
    'phi3_minus_phi1', 'phi5_minus_phi1', 'sideband_energy', 'sideband_ratio',
    'e_0_120', 'e_120_300', 'e_300_500', 'df1_dt', 'da1_dt', 'dthd_dt',
    'rms_2_5k', 'hf_energy_ratio', 'hf_centroid', 'hf_bandwidth', 'hf_flatness',
    'hf_spec_kurtosis', 'hf_peak_freq', 'hf_peak_to_band_ratio',
    'env_rms_2_5k', 'env_kurtosis_2_5k', 'env_crest_2_5k',
    'rms', 'std', 'crest_factor', 'kurtosis', 'skewness', 'peak_to_peak',
    'line_length', 'teager_mean_abs',
)
DERIVATIVES = {'df1_dt': 'f1', 'da1_dt': 'a1', 'dthd_dt': 'thd'}
BANDS = {'e_0_120': (0., 120.), 'e_120_300': (120., 300.), 'e_300_500': (300., 500.)}
HF_SPECTRAL = frozenset(FEATURE_NAMES[20:26])
HF_ENVELOPE = frozenset(FEATURE_NAMES[26:29])


def stable_skewness(x):
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return 0.0
    c = x - np.mean(x)
    s = np.std(c)
    return 0.0 if s < FEATURE_EPS else float(np.mean((c / s) ** 3))


def stable_kurtosis(x):
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return 0.0
    c = x - np.mean(x)
    s = np.std(c)
    return 0.0 if s < FEATURE_EPS else float(np.mean((c / s) ** 4))


def analytic_signal(signal):
    signal = np.asarray(signal, dtype=np.float64)
    n = signal.size
    if n == 0:
        return signal.astype(np.complex128)
    x_fft = np.fft.fft(signal)
    h = np.zeros(n, dtype=np.float64)
    if n % 2 == 0:
        h[0] = h[n // 2] = 1.0
        h[1:n // 2] = 2.0
    else:
        h[0] = 1.0
        h[1:(n + 1) // 2] = 2.0
    return np.fft.ifft(x_fft * h)


def fft_bandpass(signal, sample_rate_hz, low_hz, high_hz):
    signal = np.asarray(signal, dtype=np.float64)
    n = signal.size
    if n < 8:
        return np.zeros_like(signal)
    low = max(0., float(low_hz))
    high = min(float(high_hz), sample_rate_hz / 2. - 1e-6)
    if high <= low:
        return np.zeros_like(signal)
    spectrum = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(n, d=1. / sample_rate_hz)
    return np.fft.irfft(np.where((freqs >= low) & (freqs <= high), spectrum, 0.), n=n)


def compute_spectrum(signal, sample_rate_hz):
    signal = np.asarray(signal, dtype=np.float64)
    n = signal.size
    if n < 8:
        return np.zeros(1), np.zeros(1), np.zeros(1, dtype=np.complex128)
    centered = signal - np.mean(signal)
    win = np.hanning(n)
    spec = np.fft.rfft(centered * win)
    freqs = np.fft.rfftfreq(n, d=1. / sample_rate_hz)
    mag = (2. / (np.sum(win) + FEATURE_EPS)) * np.abs(spec)
    return freqs, mag, spec


def low_features(frame, fs, requested):
    """requested includes derivative sources; no unused harmonic/band outputs."""
    freqs, mag, spec = compute_spectrum(frame, fs)
    if freqs.size <= 1:
        return {name: 0. for name in requested}
    out = {}
    for name in requested.intersection(BANDS):
        lo, hi = BANDS[name]
        out[name] = float(np.sum(np.square(mag[(freqs >= lo) & (freqs <= hi)])))
    if not requested.difference(BANDS):
        return out
    search_mask = (freqs >= 40.) & (freqs <= 80.)
    i1 = int(np.argmax(np.where(search_mask, mag, -np.inf))) if np.any(search_mask) else (int(np.argmax(mag[1:]) + 1) if mag.size > 1 else 0)
    # Frequency identifies harmonic/sideband bins; amplitude normalizes ratios.
    f1 = float(freqs[i1])
    if 'f1' in requested:
        out['f1'] = f1
    need_amplitude = bool(requested.intersection(('a1', 'thd', 'h2_h1', 'h3_h1', 'h5_h1', 'h7_h1', 'sideband_ratio')))
    if need_amplitude:
        a1 = float(mag[i1])
        if 'a1' in requested:
            out['a1'] = a1
    if requested.intersection(('phi1', 'phi3_minus_phi1', 'phi5_minus_phi1')):
        phi1 = float(np.angle(spec[i1]))
        if 'phi1' in requested:
            out['phi1'] = phi1
    harm_amp = {}
    for order in (2, 3, 5, 7):
        ratio = f'h{order}_h1'
        phase = f'phi{order}_minus_phi1'
        if 'thd' not in requested and ratio not in requested and phase not in requested:
            continue
        idx = int(np.argmin(np.abs(freqs - order * f1)))
        if 'thd' in requested or ratio in requested:
            harm_amp[order] = float(mag[idx])
        if ratio in requested:
            out[ratio] = float(harm_amp[order] / (a1 + FEATURE_EPS))
        if phase in requested:
            delta = float(np.angle(spec[idx])) - phi1
            out[phase] = float((delta + np.pi) % (2. * np.pi) - np.pi)
    if 'thd' in requested:
        out['thd'] = float(np.sqrt(sum(harm_amp[o] ** 2 for o in (2, 3, 5, 7))) / (a1 + FEATURE_EPS))
    if requested.intersection(('sideband_energy', 'sideband_ratio')):
        low = (freqs >= max(0., f1 - 20.)) & (freqs <= max(0., f1 - 5.))
        high = (freqs >= f1 + 5.) & (freqs <= f1 + 20.)
        energy = float(np.sum(np.square(mag[low])) + np.sum(np.square(mag[high])))
        if 'sideband_energy' in requested:
            out['sideband_energy'] = energy
        if 'sideband_ratio' in requested:
            out['sideband_ratio'] = float(np.sqrt(energy) / (a1 + FEATURE_EPS))
    return out


def hf_features(frame, fs, requested):
    frame = np.asarray(frame, dtype=np.float64)
    out = {}
    band_high = min(5000., fs / 2. - 1e-6)
    spectral = requested & HF_SPECTRAL
    if spectral:
        freqs, mag, _ = compute_spectrum(frame, fs)
        mask = (freqs >= 2000.) & (freqs <= band_high)
        band_power = np.square(mag[mask])
        band_freqs = freqs[mask]
        if not band_power.size:
            out.update({name: 0. for name in spectral})
        else:
            if spectral.intersection(('hf_centroid', 'hf_bandwidth', 'hf_peak_to_band_ratio')):
                energy = float(np.sum(band_power))
            if spectral.intersection(('hf_centroid', 'hf_bandwidth')):
                centroid = float(np.sum(band_freqs * band_power) / (energy + FEATURE_EPS))
                if 'hf_centroid' in spectral:
                    out['hf_centroid'] = centroid
                if 'hf_bandwidth' in spectral:
                    out['hf_bandwidth'] = float(np.sqrt(np.sum(((band_freqs - centroid) ** 2) * band_power) / (energy + FEATURE_EPS)))
            if 'hf_flatness' in spectral:
                out['hf_flatness'] = float(np.exp(np.mean(np.log(band_power + FEATURE_EPS))) / (np.mean(band_power) + FEATURE_EPS))
            if 'hf_spec_kurtosis' in spectral:
                out['hf_spec_kurtosis'] = stable_kurtosis(band_power)
            if spectral.intersection(('hf_peak_freq', 'hf_peak_to_band_ratio')):
                peak = int(np.argmax(band_power))
                if 'hf_peak_freq' in spectral:
                    out['hf_peak_freq'] = float(band_freqs[peak])
                if 'hf_peak_to_band_ratio' in spectral:
                    out['hf_peak_to_band_ratio'] = float(band_power[peak] / (energy + FEATURE_EPS))
    envelope_names = requested & HF_ENVELOPE
    if envelope_names or requested.intersection(('rms_2_5k', 'hf_energy_ratio')):
        bandpassed = fft_bandpass(frame, fs, 2000., band_high)
        if requested.intersection(('rms_2_5k', 'hf_energy_ratio')):
            rms = float(np.sqrt(np.mean(np.square(bandpassed)) + FEATURE_EPS))
            if 'rms_2_5k' in requested:
                out['rms_2_5k'] = rms
            if 'hf_energy_ratio' in requested:
                rms_all = float(np.sqrt(np.mean(np.square(frame)) + FEATURE_EPS))
                out['hf_energy_ratio'] = float((rms**2) / (rms_all**2 + FEATURE_EPS))
        if envelope_names:
            envelope = np.abs(analytic_signal(bandpassed))
            if envelope_names.intersection(('env_rms_2_5k', 'env_crest_2_5k')):
                rms_env = float(np.sqrt(np.mean(np.square(envelope)) + FEATURE_EPS))
                if 'env_rms_2_5k' in requested:
                    out['env_rms_2_5k'] = rms_env
                if 'env_crest_2_5k' in requested:
                    out['env_crest_2_5k'] = float(np.max(np.abs(envelope)) / (rms_env + FEATURE_EPS))
            if 'env_kurtosis_2_5k' in requested:
                out['env_kurtosis_2_5k'] = stable_kurtosis(envelope)
    return out


def time_features(frame, requested):
    frame = np.asarray(frame, dtype=np.float64)
    out = {}
    if requested.intersection(('rms', 'crest_factor')):
        rms = float(np.sqrt(np.mean(np.square(frame)) + FEATURE_EPS))
        if 'rms' in requested:
            out['rms'] = rms
        if 'crest_factor' in requested:
            out['crest_factor'] = float(np.max(np.abs(frame)) / (rms + FEATURE_EPS))
    if 'std' in requested:
        out['std'] = float(np.std(frame))
    if 'kurtosis' in requested:
        out['kurtosis'] = stable_kurtosis(frame)
    if 'skewness' in requested:
        out['skewness'] = stable_skewness(frame)
    if 'peak_to_peak' in requested:
        out['peak_to_peak'] = float(np.max(frame) - np.min(frame))
    if 'line_length' in requested:
        out['line_length'] = float(np.sum(np.abs(np.diff(frame))))
    if 'teager_mean_abs' in requested:
        out['teager_mean_abs'] = float(np.mean(np.abs(frame[1:-1] ** 2 - frame[:-2] * frame[2:]))) if frame.size >= 3 else 0.
    return out


@dataclass(frozen=True)
class ChannelPlan:
    channel: int
    destinations: tuple
    names: tuple
    low: frozenset
    hf: frozenset
    time: frozenset
    derivatives: tuple


@dataclass(frozen=True)
class FeaturePlan:
    channel_count: int
    indices: tuple
    channels: tuple


def compile_global_feature_plan(indices, channel_count):
    if indices is None:
        indices = np.arange(channel_count * 37)
    indices = np.asarray(indices)
    if indices.ndim != 1 or (indices.size and (not np.issubdtype(indices.dtype, np.integer) or np.any(indices < 0) or np.any(indices >= channel_count * 37))):
        raise ValueError('Feature indices must be an in-range, one-dimensional integer array')
    indices = indices.astype(np.int64)
    plans = []
    for ch in range(channel_count):
        positions = np.flatnonzero(indices // 37 == ch)
        if not len(positions):
            continue
        names = tuple(FEATURE_NAMES[i % 37] for i in indices[positions])
        requested = frozenset(names)
        derivatives = tuple(name for name in DERIVATIVES if name in requested)
        low = (requested & frozenset(FEATURE_NAMES[:15])) | frozenset(DERIVATIVES[name] for name in derivatives)
        plans.append(ChannelPlan(ch, tuple(positions), names, low, requested & frozenset(FEATURE_NAMES[18:29]), requested & frozenset(FEATURE_NAMES[29:]), derivatives))
    return FeaturePlan(channel_count, tuple(indices), tuple(plans))


def resample_time_axis(features, target_steps):
    t, f = features.shape
    if t == target_steps:
        return features
    if t <= 1:
        return np.repeat(features[:1], target_steps, axis=0)
    old, new = np.linspace(0., 1., t), np.linspace(0., 1., target_steps)
    out = np.zeros((target_steps, f), dtype=np.float64)
    for j in range(f):
        out[:, j] = np.interp(new, old, features[:, j])
    return out


def extract_window_features_per_channel(signal_data, sample_rate_hz=10000., window_samples=2000,
        low_frame_samples=500, hf_frame_samples=250, low_stride_samples=25,
        hf_stride_samples=29, fixed_time_steps=61, selected_feature_indices=None, feature_plan=None):
    raw = np.asarray(signal_data)
    if raw.ndim != 2 or not np.isclose(sample_rate_hz, 10000.):
        raise ValueError('Expected samples-by-channels at 10 kHz')
    if min(window_samples, low_frame_samples, hf_frame_samples, low_stride_samples, hf_stride_samples) <= 0 or max(low_frame_samples, hf_frame_samples) > window_samples:
        raise ValueError('Invalid frame/window configuration')
    plan = feature_plan or compile_global_feature_plan(selected_feature_indices, raw.shape[1])
    if plan.channel_count != raw.shape[1]:
        raise ValueError('Plan/channel mismatch')
    tl = 1 + (window_samples - low_frame_samples) // low_stride_samples
    th = 1 + (window_samples - hf_frame_samples) // hf_stride_samples
    target = tl if fixed_time_steps is None else fixed_time_steps
    if target < 1:
        raise ValueError('fixed_time_steps must be positive')
    starts = np.arange(0, max(0, raw.shape[0] - window_samples + 1), window_samples, dtype=np.int64)
    out = np.zeros((len(starts), target, len(plan.indices)), dtype=np.float64)
    for wi, start in enumerate(starts):
        for ch in plan.channels:
            window = raw[start:start + window_samples, ch.channel]
            series = {name: np.zeros(tl) for name in ch.low | ch.time}
            if ch.low or ch.time:
                for ti in range(tl):
                    frame = window[ti * low_stride_samples:ti * low_stride_samples + low_frame_samples]
                    if ch.low:
                        for name, value in low_features(frame, sample_rate_hz, ch.low).items():
                            series[name][ti] = value
                    if ch.time:
                        for name, value in time_features(frame, ch.time).items():
                            series[name][ti] = value
            for name in ch.derivatives:
                # Preserve the archived definition exactly; do not alter trained inputs.
                series[name] = np.gradient(series[DERIVATIVES[name]], low_frame_samples / sample_rate_hz)
            if ch.hf:
                names = tuple(name for name in FEATURE_NAMES[18:29] if name in ch.hf)
                hf = np.empty((th, len(names)), dtype=np.float64)
                for ti in range(th):
                    frame = window[ti * hf_stride_samples:ti * hf_stride_samples + hf_frame_samples]
                    values = hf_features(frame, sample_rate_hz, ch.hf)
                    hf[ti] = [values[name] for name in names]
                hf = resample_time_axis(hf, tl)
                series.update({name: hf[:, j] for j, name in enumerate(names)})
            features = np.column_stack([series[name] for name in ch.names])
            out[wi][:, ch.destinations] = resample_time_axis(features, target)
    return out, starts, starts + window_samples, target
