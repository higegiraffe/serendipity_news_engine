# 自分用セレンディピティ記事推薦エンジン

RSS から記事を収集し、タイトルと概要をベクトル化して、自分の関心プロファイルとの近さ・新しさ・鮮度・情報源の信頼度から記事を推薦するローカル優先の Python アプリです。

単なる RSS リーダーではなく、検索語にしにくい関心をフィードバックから少しずつ推定し、「既知の関心」「隣接する関心」「意外性のある記事」を理由付きで表示することを目指しています。

## 現在の実装状況

MVP の主要な流れは実装済みです。

- `config/feeds.yaml` の RSS から記事を取得し、SQLite に保存
- 記事タイトル・概要の embedding を作成
- `config/interests.yaml` の初期関心プロファイルを登録
- 関心類似度、新規性、鮮度、情報源スコアから推薦スコアを計算
- Streamlit 画面で推薦記事、全記事、関心プロファイル、検索語候補を表示
- 記事ごとの評価、コメント、あとで読む、深掘りフラグを保存
- 評価済み記事を使って関心プロファイルを再計算
- OpenAI API キーがない場合もローカル embedding またはハッシュ代替で動作

記事本文の全文取得、Web 検索 API 連携、RSS 情報源の自動提案、日次レポート、関心の可視化は今後の拡張予定です。

## セットアップ

Windows PowerShell で実行します。

```powershell
cd C:\Users\USER\Documents\python\serendipity_news_engine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

OpenAI API は任意です。利用する場合は `.env` に設定します。

```text
OPENAI_API_KEY=sk-...
```

API キーがない場合、`embedding.provider` が `local` の設定でローカルモデルを使います。`sentence-transformers` がまだ使えない環境では、CLI とテストが動くように決定的なハッシュ embedding に切り替えます。

## コマンド

```powershell
python -m src.main init
python -m src.main fetch
python -m src.main embed
python -m src.main score
python -m src.main run
streamlit run src/ui_streamlit.py
```

各コマンドの意味は次の通りです。

- `init`: DB を作成し、初期関心プロファイルを登録
- `fetch`: RSS から記事を取得して DB に保存
- `embed`: embedding 未作成の記事をベクトル化
- `score`: フィードバックを反映し、記事スコアを再計算
- `run`: `fetch`、`embed`、`score` をまとめて実行
- `streamlit run src/ui_streamlit.py`: UI を起動

## 設定

- RSS は `config/feeds.yaml` で追加・無効化・信頼度調整をします。
- 初期関心プロファイルは `config/interests.yaml` で編集します。
- embedding provider やスコア重みは `config/settings.yaml` で変更します。
- OpenAI embeddings を使う場合は `embedding.provider` を `openai` にし、`.env` に `OPENAI_API_KEY` を設定します。

## スコアリング

```text
final_score =
  similarity_weight * interest_score
+ novelty_weight    * novelty_score
+ freshness_weight  * freshness_score
+ source_weight     * source_score
```

推薦タイプは次の4種類です。

- `known_interest`: 既知の関心に近い記事
- `adjacent_interest`: 既知の関心から少しずれた隣接領域の記事
- `surprise`: 普段の中心からは離れるが、情報源と新規性に期待できる記事
- `general`: 総合スコアで残した記事

DB は `data/app.db` に作成されます。検索語候補は現時点では画面に表示するだけで、外部検索 API には接続していません。

## テスト

```powershell
python -m pytest
```

## 今後の拡張候補

- AI が生成した検索語を使う Web 検索 API 連携
- 記事本文の取得と要約精度の改善
- 評価の高い記事から RSS 情報源を提案
- 重複ニュースの統合
- 深掘りモード
- Markdown または HTML の日次レポート出力
- 関心プロファイルの可視化
