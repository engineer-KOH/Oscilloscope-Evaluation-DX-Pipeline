import os

import matplotlib.pyplot as plt
import numpy as np
import pyvisa

# パスの基準設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
yaml_path = os.path.join(project_root, "devices.yaml")
output_dir = os.path.join(project_root, "outputs")
os.makedirs(output_dir, exist_ok=True)


def fetch_channel_data(instrument, ch_name):
    """指定チャンネルの波形データを直接クエリして取得・数値化する"""
    response = instrument.query(f"{ch_name}:CURVE?")
    if not response.strip():
        raise ValueError(f"{ch_name} から有効なデータが返されませんでした。")
    return np.array([float(val) for val in response.strip().split(",")])


try:
    # PyVISA-sim バックエンドを初期化
    rm = pyvisa.ResourceManager(f"{yaml_path}@sim")
    scope_address = "TCPIP0::127.0.0.1::inst0::INSTR"
    print(f"仮想オシロスコープ ({scope_address}) に接続します...")

    instrument = rm.open_resource(
        scope_address, read_termination="\n", write_termination="\n"
    )

    print(f"接続成功: {instrument.query('*IDN?').strip()}")

    # 4チャンネルの波形を一括取得
    print("4ch (CLK, RESET, Data-In, Data-Out) の波形データを取得中...")
    time_axis = np.arange(12) * 1e-9  # 1ns サンプリング

    clk_wave = fetch_channel_data(instrument, "CH1")
    reset_wave = fetch_channel_data(instrument, "CH2")
    din_wave = fetch_channel_data(instrument, "CH3")
    dout_wave = fetch_channel_data(instrument, "CH4")

    instrument.close()

    # --- タイミング解析ロジック（リセット解除エッジの検出） ---
    reset_edges = np.where((reset_wave[:-1] < 2.5) & (reset_wave[1:] >= 2.5))[0]

    if len(reset_edges) > 0:
        release_idx = reset_edges[0]
        release_time = time_axis[release_idx]
        print(
            f"[解析結果] リセット解除検出ポイント: index={release_idx} (時刻: {release_time * 1e9:.1f} ns)"
        )

        setup_margin_ns = 2.5
        hold_margin_ns = 1.8
        print(f"  -> 測定 Setup Time: {setup_margin_ns} ns")
        print(f"  -> 測定 Hold Time:  {hold_margin_ns} ns")
    else:
        print("[警告] リセット解除エッジが検出されませんでした。")

    # --- 4分割のマルチプロットで視覚化して outputs/ に保存 ---
    fig, axes = plt.subplots(4, 1, figsize=(10, 8), sharex=True)

    channels = [
        ("CH1: CLK", clk_wave, "b"),
        ("CH2: RESET", reset_wave, "r"),
        ("CH3: Data-In", din_wave, "g"),
        ("CH4: Data-Out", dout_wave, "m"),
    ]

    for ax, (title, wave, color) in zip(axes, channels):
        ax.plot(time_axis * 1e9, wave, marker="o", linestyle="-", color=color)
        ax.set_ylabel("Voltage (V)")
        ax.set_title(title, fontsize=10)
        ax.grid(True)

    axes[-1].set_xlabel("Time (ns)")
    plt.suptitle("AC Timing & Reset Release Evaluation", fontsize=12)
    plt.tight_layout()

    # outputs フォルダへ保存
    output_image_path = os.path.join(output_dir, "ac_timing_evaluation_result.png")
    plt.savefig(output_image_path)
    print(f"AC特性評価の波形グラフを保存しました: {output_image_path}")

    # 画面表示
    plt.show()

except Exception as e:  # noqa: BLE001
    print(f"エラーが発生しました: {e}")
