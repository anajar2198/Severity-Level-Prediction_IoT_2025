def make_dual_plot(
    folder_name,
    motor_bundle,
    pcc_bundle,
    intervals,
    start_second,
    duration_seconds,
    output_prefix: Path,
    rms_window_seconds: float,
    signal_panel_mode: str,
    feature_name: str,
    feature_aggregate: str,
    hide_metrics: bool = False,
):
    fs = motor_bundle["fs"]
    if not np.isclose(fs, pcc_bundle["fs"]):
        raise RuntimeError("Motor and PCC sample rates do not match.")

    start_sample = int(round(start_second * fs))
    end_sample = min(
        motor_bundle["raw_data"].shape[0],
        pcc_bundle["raw_data"].shape[0],
        int(round((start_second + duration_seconds) * fs)),
    )

    fig, axes = plt.subplots(
        5,
        1,
        figsize=(14, 10),
        sharex=True,
        gridspec_kw={"height_ratios": [0.7, 1.2, 1.4, 1.2, 1.4]},
    )
    sched_ax, motor_sig_ax, motor_score_ax, pcc_sig_ax, pcc_score_ax = axes

    for interval in intervals:
        seg_start = interval["start_second"]
        seg_end = interval["end_second"]
        if seg_end <= start_second or seg_start >= start_second + duration_seconds:
            continue
        x0 = max(seg_start, start_second)
        x1 = min(seg_end, start_second + duration_seconds)
        color = "#9ecae1" if interval["segment_type"] == "normal" else "#fb6a4a"
        if interval["segment_type"] == "tail_normal":
            color = "#bdbdbd"
        sched_ax.axvspan(x0, x1, color=color, alpha=0.85)
        if interval["segment_type"] == "attack":
            sched_ax.text(0.5 * (x0 + x1), 0.5, f"{interval['severity_label']:.1f}", ha="center", va="center", fontsize=8)
    sched_ax.set_yticks([])
    sched_ax.set_ylabel("Schedule")
    sched_ax.set_title(f"{folder_name}: motor and PCC cyber-attack detection performance ({start_second:.0f}-{start_second + duration_seconds:.0f} s)")

    def add_attack_spans(ax):
        for interval in intervals:
            seg_start = interval["start_second"]
            seg_end = interval["end_second"]
            if seg_end <= start_second or seg_start >= start_second + duration_seconds:
                continue
            if interval["segment_type"] == "attack":
                ax.axvspan(max(seg_start, start_second), min(seg_end, start_second + duration_seconds), color="#fb6a4a", alpha=0.10)
        ax.grid(True, alpha=0.25)

    def plot_signal(ax, bundle, color, ylabel):
        add_attack_spans(ax)
        if signal_panel_mode == "rms":
            sig = bundle["raw_data"][start_sample:end_sample, bundle["plot_channel_idx"]]
            rms_window_samples = int(round(rms_window_seconds * fs))
            rms = normalize_trace(compute_windowed_rms(sig, rms_window_samples))
            t_rms = start_second + np.arange(len(rms)) * rms_window_seconds
            ax.plot(t_rms, rms, color=color, linewidth=1.2)
            ax.set_ylabel(ylabel)
        elif signal_panel_mode == "feature":
            df = bundle["scores_df"]
            ax.plot(df["window_end_second"], df["feature_value"], color=color, linewidth=1.2)
            prefix = ylabel.split("\n")[0]
            ax.set_ylabel(f"{prefix}\n{feature_label(feature_name, feature_aggregate)}")
        else:
            sig = bundle["raw_data"][start_sample:end_sample, bundle["plot_channel_idx"]]
            t_feat, y_feat = compute_continuous_feature_trace(sig, fs, feature_name, start_second)
            ax.plot(t_feat, y_feat, color=color, linewidth=1.0)
            prefix = ylabel.split("\n")[0]
            ax.set_ylabel(f"{prefix}\n{feature_trace_label(feature_name)}")

    def plot_score(ax, bundle, title):
        df = bundle["scores_df"]
        add_attack_spans(ax)
        ax.plot(df["window_end_second"], df["attack_probability"], color="#006d2c", linewidth=1.4, label="Attack probability")
        ax.step(df["window_end_second"], df["pred_label"], where="post", color="#cb181d", linewidth=1.0, alpha=0.85, label="Predicted label")
        ax.step(df["window_end_second"], df["true_label"], where="post", color="#636363", linewidth=1.0, alpha=0.8, linestyle="--", label="True label")
        ax.axhline(0.5, color="#444444", linestyle=":", linewidth=1.0, label="Threshold")
        ax.set_ylim(-0.05, 1.05)
        ax.set_ylabel("Score / label")
        ax.set_title(title, fontsize=11)
        if not hide_metrics:
            m = bundle["metrics"]
            metric_text = (
                f"Acc={m['accuracy']*100:.1f}%  "
                f"Bal.Acc={m['balanced_accuracy']*100:.1f}%  "
                f"F1={m['f1']*100:.1f}%"
            )
            ax.text(
                0.01, 0.03, metric_text,
                transform=ax.transAxes,
                ha="left", va="bottom", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#888888", alpha=0.9),
            )

    plot_signal(motor_sig_ax, motor_bundle, "#08519c", "Motor\nNorm. RMS")
    plot_score(motor_score_ax, motor_bundle, "Motor-side detection")
    plot_signal(pcc_sig_ax, pcc_bundle, "#6a51a3", "PCC\nNorm. RMS")
    plot_score(pcc_score_ax, pcc_bundle, "PCC-side detection")

    motor_score_ax.legend(loc="upper right", fontsize=8, ncol=2)
    pcc_score_ax.set_xlabel("Time (s)")

    fig.tight_layout()
    fig.savefig(output_prefix.with_suffix(".png"), dpi=250, bbox_inches="tight")
    fig.savefig(output_prefix.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
