import os

import matplotlib.pyplot as plt
import numpy as np
import pyvisa

# 1. パスの基準設定
# current_dir: src/ フォルダの絶対パス
current_dir = os.path.dirname(os.path.abspath(__file__))
# project_root: プロジェクトのルートフォルダ（研修13_Pythonライブラリ_pyvisaについて）
project_root = os.path.dirname(current_dir)

# 各種ファイルのパス設定
yaml_path = os.path.join(project_root, "devices.yaml")
output_dir = os.path.join(project_root, "outputs")

# outputs フォルダが存在しない場合は自動作成する
os.makedirs(output_dir, exist_ok=True)

try:
    # PyVISA-sim バックエンドを初期化
    rm = pyvisa.ResourceManager(f"{yaml_path}@sim")

    scope_address = "TCPIP0::127.0.0.1::inst0::INSTR"
    print(f"仮想デバイス ({scope_address}) に接続します...")

    instrument = rm.open_resource(
        scope_address, read_termination="\n", write_termination="\n"
    )

    # 接続確認
    idn = instrument.query("*IDN?")
    print(f"接続成功: {idn.strip()}")

    # 波形データの取得
    print("波形データ (CURVE?) を取得中...")
    response_str = instrument.query("CURVE?")
    print(f"受信した生文字列: [{response_str.strip()}]")

    if not response_str.strip():
        raise ValueError("計測器からデータが返されませんでした。")

    # カンマ区切りの文字列を NumPy 配列に変換
    waveform_data = np.array([float(val) for val in response_str.strip().split(",")])

    # 物理単位（電圧値）へのスケーリング変換
    ymult = 0.04
    yoff = 0.0
    voltage_array = waveform_data * ymult - yoff
    print(f"変換後の電圧配列 (V): {voltage_array}")

    instrument.close()

    # グラフ描画と outputs フォルダへの保存
    plt.figure(figsize=(8, 4))
    plt.plot(voltage_array, marker="o", linestyle="-", color="b", label="Ch1 Waveform")
    plt.title("Simulated Oscilloscope Waveform (CURVE?)")
    plt.xlabel("Sample Index")
    plt.ylabel("Voltage (V)")
    plt.grid(True)
    plt.legend()

    # outputs フォルダの配下に画像として保存
    output_image_path = os.path.join(output_dir, "waveform_result.png")
    plt.savefig(output_image_path)
    print(f"波形グラフを保存しました: {output_image_path}")

    # 画面にグラフを表示
    plt.show()
    print("波形取得テストが正常に完了しました。")

except Exception as e:  # noqa: BLE001
    print(f"エラーが発生しました: {e}")
