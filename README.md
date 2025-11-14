# jgrants-mcp

Paid会員向けの「補助金MCPチャット」バックエンドのベースリポジトリです。

デジタル庁の **Jグランツ公開API** を **MCP(Server)** としてラップし、

チャットUI（Discord/LINE/Web）から自然文で「補助金の検索→詳細→添付要約→ウォッチ」を行うための土台を提供します。

* MCPサーバ本体：Python 3.11 + FastAPI 相当の構成

* 運用：GitHub Actions による CI / Security / Release / Backup パイプラインを前提

* 上位レイヤー：Kamui OS / Cursor IDE から利用されることを想定（必須ではない）

---

## 1. ディレクトリ構成（想定）

```bash
/jgrants_mcp_server   # MCP サーバ本体（FastAPI / Uvicorn）＋ MCP エンドポイント
/tests                # pytest で実行するテストコード
/.github/workflows    # CI・Security・Release・Backup ワークフロー
/docs                 # GitHub 設定・運用ノート
/scripts              # GitHub 設定検証用スクリプトなど
```

---

## 2. 必要な環境変数（MCPサーバ）

| 変数名                 | 説明                      | 既定値                                              |
| ------------------- | ----------------------- | ------------------------------------------------ |
| `API_BASE_URL`      | Jグランツ公開API のベースURL      | `https://api.jgrants-portal.go.jp/exp/v1/public` |
| `JGRANTS_FILES_DIR` | MCP が永続化するファイルを置くディレクトリ | `./jgrants_files`                                |

> CI では上記の想定値と整合するように環境を構成しています。

---

## 3. ローカル開発（最短ルート）

### 3-1. 前提

* Python 3.11 以上

* `uvicorn` などは `requirements.txt` からインストール

### 3-2. セットアップ

```bash
# 仮想環境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存インストール
python3 -m pip install -r requirements.txt
```

### 3-3. MCP サーバを起動する

```bash
# デフォルト: http://0.0.0.0:8000
uvicorn jgrants_mcp_server.server:app --host 0.0.0.0 --port 8000
```

### 3-4. 動作確認

```bash
# ステータス
curl http://localhost:8000/health

# 設定値
curl http://localhost:8000/v1/jgrants-info

# OpenAPI UI（ブラウザ）
open http://localhost:8000/docs
```

MCPクライアントや LLM からは、この `http://localhost:8000` を
「MCP サーバ」として登録して利用します。

---

## 4. テスト

### 4-1. ユニットテスト

```bash
python3 -m pip install -r requirements.txt
pytest tests/test_core.py
```

（将来的には `tests/` 以下にケースを追加し、`pytest` 単体で全件実行できる構成を想定）

### 4-2. 開発の最低ルール（推奨）

* 1 PR につき 1 つの論点（例：MCPツール追加、バグ修正など）

* 新規エンドポイント・ツール追加時は `tests/` に 1 ケース以上を追加

* README や docs に反映が必要な変更は同じ PR に含める

---

## 5. GitHub Actions（CI / Security / Release / Backup）

このリポジトリには、以下のワークフローを配置することを想定しています。

### 5-1. CI

* トリガー：`push` / `pull_request`

* Python 3.11

* `pip` キャッシュを利用

* `pytest` によるテスト実行（失敗時はマージ不可）

### 5-2. Security

* CodeQL + Dependency Review を `main` ブランチに対して実行

* トリガー：`push` / `pull_request` / 週次スケジュール

* 依存差分の脆弱性は `fail-on-severity=high` で PR をブロック

* GitHub Advanced Security が無い場合でも、警告付きで成功するように調整可能

### 5-3. Release

* トリガー：`v*.*.*` タグ

* `docker/build-push-action` で GHCR へイメージを公開

* `sigstore/cosign-installer` による keyless 署名（OIDC）

* cosign 署名にはリトライロジック（最大 3 回、5 秒間隔）あり

### 5-4. Nightly backup（任意）

* Supabase などのバックアップや監査ログを UTC 18:00 に取得

* `actions/upload-artifact` で 30 日間保存

* 実運用で不要な場合は無効化可能

---

## 6. Repository Secrets / Variables

**Release ワークフローで必要なシークレット**:
- 基本的に不要（GHCRへのプッシュは`GITHUB_TOKEN`を使用）
- `GHCR_IMAGE`変数（オプション）: デフォルトは`ghcr.io/cursorvers/jgrants-mcp`

**Nightly backup ワークフローで必要なシークレット**（オプション）:
- `SUPABASE_SERVICE_ROLE`: Supabaseを使用する場合のみ

| 名前                      | 用途                                                  | 必須/オプション |
| ----------------------- | --------------------------------------------------- | ----------- |
| `GHCR_IMAGE` (Variable) | GHCRイメージ名（デフォルト `ghcr.io/cursorvers/jgrants-mcp` を上書きしたい場合） | オプション      |
| `SUPABASE_SERVICE_ROLE` (Secret) | Nightly バックアップなどで使用する場合                             | オプション      |

署名は `cosign` の keyless モード（OIDC）を利用するため追加鍵は不要ですが、
`Release` ワークフローには `id-token: write` 権限を付与してください。

---

## 7. アーキテクチャのイメージ（テキスト）

本リポジトリの責務は **「MCPサーバとしてJグランツ公開APIをラップするところまで」** です。

```text
[LLM / Chat UI]  --(MCP)-->  [jgrants-mcp (このリポジトリ)]
                                     │
                                     └─ Jグランツ公開API
```

* このリポジトリはあくまで「MCPの入口」として設計しています。

* 上位のオーケストレーション（Kamui OS）やエディタ（Cursor）は、別リポジトリ/別レイヤーで扱います。

---

## 8. 開発フローの例

1. Issue / タスク（例：`MCP-101`）を立てる

2. ブランチ作成：`feat/mcp-health-endpoint` など

3. コードを書く

   * FastAPI エンドポイントや MCP ツールの追加

   * 必要に応じて `tests/` にテスト追加

4. `pytest` でローカルテスト

5. PR を作成

6. CI / Security チェックが通れば `main` にマージ

7. タグ `vX.Y.Z` を付与 → Release ワークフローで GHCR に反映

---

## 9. GitHub 設定の自動化とチェックリスト

`docs/github-settings.md` に、GitHub Settings 画面での操作と `gh api` を使ったコマンド例を記載しています。
Actions の許可リスト・Workflow 権限・フォーク PR 承認・Environment の承認ルール・Branch Protection・Secret Scanning Push Protection を順に構成してください。

### 9-1. GitHub 設定の検証

`scripts/check_github_settings.py` を使用して、GitHub リポジトリの設定が要件通りになっているかを自動検証できます。

```bash
# GitHub トークンを環境変数に設定
export GITHUB_TOKEN=$(gh auth token)

# または
export GH_TOKEN=$(gh auth token)

# 検証スクリプトを実行
python3 scripts/check_github_settings.py --repo cursorvers/jgrants-mcp
```

このスクリプトは以下を検証します：

* Actions permissions（許可されたアクションのリスト）

* Environments（dev, stg, prod の存在）

* Branch protection（main ブランチの保護ルール）

* Secret scanning push protection

CI や Settings 変更後にこのコマンドを実行することで、
ガードレールが維持されているかを継続的に確認できます。

---

## 10. 参考ドキュメント

* `docs/github-settings.md`：GitHub 設定の詳細な要件定義

* `docs/ui-setup-guide.md`：GitHub UI での設定手順

* `docs/workflow-troubleshooting.md`：ワークフローのトラブルシューティングガイド

* `docs/github-settings-status.md`：現在の設定状況とワークフロー実行結果

* `docs/workflow-improvements.md`：ワークフロー改善履歴
