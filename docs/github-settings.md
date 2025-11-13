# GitHub Actions & Security Requirements

このリポジトリでは **Jグランツ公開APIをMCPサーバ化** した Paid 会員向けチャットUI + MCP の安定運用を目的に、CI・セキュリティ・GHCR Release && Approval まで GitHub Actions で一気通貫に管理します。以下の要件を Settings と workflow に反映してください。

## 0. 背景と目的（グランドデザイン）
- デジタル庁 `digital-go-jp/jgrants-mcp-server` を参考に Python 3.11+ / FastMCP 前提で MCP 部分を構築。
- Paid 会員へチャットUI + MCP を提供するため、PR/Push で自動ビルド・テスト、依存/脆弱性チェック、タグ発行で GHCR へ署名付きコンテナを公開、`prod` は 2 名承認の手動デプロイ保護を実現。
- テストは `pytest tests/test_core.py`、ENV は README 想定（`API_BASE_URL`・`JGRANTS_FILES_DIR` など）。
- セキュリティ方針として、最小権限の `GITHUB_TOKEN`、Zero Trust なアクション実行（Verified + Allowlist + SHA Pinning）、フォーク PR は承認制、Secret Scanning Push Protection を必須化。

## 1. 適用スコープ
- Repository Settings で以下を構成（UI/`gh api` 両対応）
  1. **Settings → Actions → General**（Policies / Workflow permissions / Fork PR / Artifact retention / Reusable workflows）
  2. **Settings → Environments**：`dev` / `stg` / `prod`
  3. **Settings → Code security and analysis**（CodeQL・Dependabot・Dependency Review・Secret Scanning）
  4. **Settings → Branches**：`main` の保護ルール

## 2. 想定ディレクトリ構成（参考）
```
/jgrants_mcp_server   # MCPサーバ本体（digital-go-jp相当）
/tests                # pytest 移行先
/.github/workflows    # CI / Security / Release / Backup
```

## 3. Actions → General 要件
1. **Allow select actions and reusable workflows** を選び、以下を明示的に許可（全て SHA でピン留め）
   - `actions/checkout@08eba0b27e820071cde6df949e0beb9ba4906955`
   - `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065`（`cache: pip` を活用）
   - `actions/cache@6f8efc29b200d32929f49075959781ed54ec270c`
   - `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02`
   - `actions/download-artifact@9bc31d5ccc31df68ecc42ccf4149144866c47d8a`
   - `docker/login-action@465a07811f14bebb1938fbed4728c6a1ff8901fc`
   - `docker/setup-buildx-action@885d1462b80bc1c1c7f0b00334ad271f09369c55`
   - `docker/build-push-action@ca052bb54ab0790a636c9b5f226502c73d547a25`
   - `sigstore/cosign-installer@c85d0e205a72a294fe064f618a87dbac13084086`
   - `github/codeql-action/init@8dca8a82e2fa1a2c8908956f711300f9c4a4f4f6`
   - `github/codeql-action/analyze@8dca8a82e2fa1a2c8908956f711300f9c4a4f4f6`
   - `actions/dependency-review-action@93809e13f07c0db8c2db3c320885d98f2d235acc`
2. **Workflow permissions**：`Read repository contents`（既定）にし、`packages: write`/`id-token: write` 等はウォークフロー単位で必要なジョブにのみ付与。
3. **Fork pull request workflows**：`Require approval for first-time contributors` をON、外部ソースからの初回実行は手動承認。
4. **Artifact and log retention**：30 日（必要ならジョブ上で `retention-days` を指定）。
5. **Reusable workflows access**：組織内再利用なら `Accessible from repositories in the organization`。
6. **Concurrency**：全 workflow に `concurrency.group` を設定し、同一ブランチの旧実行を自動キャンセル（CI や Release に `cancel-in-progress: true`）。

## 4. Environments
| 環境 | 用途 | ルール |
| --- | --- | --- |
| `dev` | 開発用（任意デプロイ） | 制限なし |
| `stg` | ステージング | Required reviewers: 1、Wait timer: 10 分 |
| `prod` | 本番 | Required reviewers: 2（自己承認禁止）、Allow admin bypass OFF、Deploy branches: `main` のみ |

`Release` workflow の `environment: prod` ジョブは手動承認を待ち、自己承認禁止 & 2 名以上の承認を満たす必要があります。必要なら「Prevent self-approval」オプションも有効化。

## 5. Code security and analysis
- **CodeQL**：Enable（Default Setup も OK）
- **Dependency Review**：Enable（PR での差分依存に対する警告）
- **Dependabot**：Security updates + version updates を有効化し、`/.github/dependabot.yml` で weekly に依存・Actions を更新
- **Secret scanning → Push protection**：Enable（Push 時にシークレットが検出されるとブロック）

## 6. Branch protection（`main`）
- Require a pull request before merging（1 承認以上）
- Require status checks to pass before merging：`CI (unit)`、`Security / CodeQL`、`Dependency Review`
- Require branches to be up to date before merging（厳格モード）

## 7. Secrets & Variables
| 名前 | 用途 |
| --- | --- |
| `JGRANTS_API_BASE` | README に書かれた `API_BASE_URL`（デフォルト https://api.jgrants-portal.go.jp/exp/v1/public）
| `JGRANTS_FILES_DIR` | 任意でファイル保存先を変更する場合に設定
| `SUPABASE_SERVICE_ROLE` | supabase によるバックアップやエクスポートで使う（任意）
| `GHCR_IMAGE` | 例：`ghcr.io/cursorvers/jgrants-mcp`（タグ化用）

**署名について**：`cosign keyless`（OIDC）を使うためシークレットキー不要。`Release` workflow には `permissions: id-token: write` を設定し、GH が発行する OIDC トークンを使って署名。

## 8. Workflows（`.github/workflows/*.yml`）
### 8.1 `CI` (`.github/workflows/ci.yml`)
- トリガ：`push`（全ブランチ） & `pull_request`（`main`）
- `permissions: contents: read`
- `concurrency.group: ci-${{ github.workflow }}-${{ github.ref }}` + `cancel-in-progress: true`
- Python 3.11、`actions/setup-python` の `cache: pip`、`pip install -r requirements.txt`、`pytest -q`
- commit-SHA でアクションをピン留め済み

### 8.2 `Security` (`.github/workflows/security.yml`)
- トリガ：`push` / `pull_request`（`main`） + `schedule`（週1 水 05:15 UTC）
- `permissions`：`contents: read`、`security-events: write`
- CodeQL の `init` / `analyze` を SHA で固定
- Pull Request 時に `actions/dependency-review-action` で `high` 以上の脆弱性差分を失敗にする

### 8.3 `Release` (`.github/workflows/release.yml`)
- トリガ：`push` で `tags: 'v*.*.*'`
- `permissions`: `contents: read`, `packages: write`, `id-token: write`
- `environment: prod`（2 名承認 + 自己承認禁止）
- GHCR へ `docker/build-push-action` で `latest` を含むタグを push
- `sigstore/cosign-installer` + `cosign sign --yes`（`COSIGN_EXPERIMENTAL=1` 環境）で keyless 署名

### 8.4 `Nightly backup` (`.github/workflows/nightly-backup.yml`)
- スケジュール：UTC `0 18 * * *`（JST 03:00 相当）
- アーティファクトは `actions/upload-artifact`、`retention-days: 30`
- Supabase などで PHI/機微情報を保存しない設計を徹底

## 9. GitHub 設定の手順（UI / `gh api` 両対応）
1. **Settings → Actions → General**
   - Policies：Allow select actions and reusable workflows
   - Allow GitHub + Verified Marketplace actions：ON
   - Allow specified actions：上記 SHA ピン留めアクションを追加
   - Workflow permissions：Read repository contents
   - Fork PR workflows：Require approval for first-time contributors
   - Artifact & log retention：30 日
   - Reusable workflows access：必要なら組織内に限定
2. **Settings → Environments**：`dev`, `stg`, `prod` を作成し、`stg` で Wait timer 10 分、`prod` で Required reviewers 2（自己承認禁止）、Allow admin bypass OFF。
3. **Settings → Code security and analysis**：CodeQL、Dependency Review、Dependabot、Secret Scanning Push Protection を有効化。
4. **Settings → Branches**：`main` に保護ルール（PR・ステータスチェック・最新化要求）。
5. **Secrets**：必要な Secrets / Variables を追加（`JGRANTS_API_BASE`, `GHCR_IMAGE`, `SUPABASE_SERVICE_ROLE` など）。
6. 実行後は `gh api /repos/cursorvers/jgrants-mcp/actions/permissions` などで現在の設定値を取得し記録。

## 10. 運用KPI
- **MTTD ≤ 5 分**：CI/セキュリティ検知を即時可視化（Notifications + PR Block）
- **P50 MTTR ≤ 15 分**：失敗 run からログ把握 → リトライ → 再現性確認を迅速化
- **Artifact/Logs 保管 30 日**：必要に応じて job 単位で `retention-days` を上書き

## 11. リスクと緩和策
- **サードパーティアクション改竄**：Verified + Allowlist + SHA pinning、Dependabot で更新
- **フォークPRの情報流出**：承認必須＆`GITHUB_TOKEN` の最小権限運用（job 単位で `packages` / `id-token` を書き換え）
- **連続 Push の無駄実行**：全 workflow に `concurrency` で旧実行をキャンセル
- **秘密情報の Push**：Secret Scanning + Push Protection でブロック

## 12. 想定実装前提
- Python 3.11+、`pytest tests/test_core.py`、README 想定 ENV（`API_BASE_URL`, `JGRANTS_FILES_DIR`）に合わせたテストを workflow で実行
- デジタル庁の MCP サーバ README を参照し、CI で使用する ENV / テストコマンドを一致させる

## 付録
### A. Dependabot 設定（`.github/dependabot.yml`）
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```
### B. Workflow での最小権限例
```yaml
permissions:
  contents: read
  packages: write    # GHCR push job のみ
  id-token: write    # cosign keyless job のみ
```
