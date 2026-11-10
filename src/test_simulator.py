import os

import pyvisa

# スクリプトの場所を基準に devices.yaml の絶対パスを指定
current_dir = os.path.dirname(os.path.abspath(__file__))
yaml_path = os.path.join(os.path.dirname(current_dir), "devices.yaml")

try:
    # YAMLファイルを紐づけた PyVISA-sim バックエンドを初期化
    rm = pyvisa.ResourceManager(f"{yaml_path}@sim")

    scope_address = "TCPIP0::127.0.0.1::inst0::INSTR"
    print(f"仮想デバイス ({scope_address}) に接続します...")

    # メッセージベースリソースとしてオープン
    instrument = rm.open_resource(scope_address)

    # 動作確認
    idn_response = instrument.query("*IDN?")
    print(f"受信した機器情報: {idn_response.strip()}")

    instrument.write("ACQ:STATE RUN")
    print("コマンド送信テスト成功: ACQ:STATE RUN")

    instrument.close()

except Exception as e:  # noqa: BLE001
    print(f"エラーが発生しました: {e}")
