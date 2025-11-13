# jgrants-mcp

Paid会員向けの「補助金MCPチャット」バックエンドのベースリポジトリです。
Digital庁の Jグランツ公開API を MCP サーバとして提供し、チャットUIと連携するユースケース向けに CI / セキュリティ / デプロイの一気通貫パイプラインを構築します。

## ディレクトリ構成（想定）
```
/jgrants_mcp_server   # MCP サーバ本体（FastMCP/Python 3.11+）
/tests                # Pytest で実行するテストコード
/.github/workflows    # CI・Security・Release・Backup ワークフロー
```

## 必要な環境変数（README の想定値）
| 変数名 | 説明 | 既定値 |
| --- | --- | --- |
| `API_BASE_URL` | Jグランツ公開API のベースURL | `https://api.jgrants-portal.go.jp/exp/v1/public` |
| `JGRANTS_FILES_DIR` | MCP が永続化するファイルを置くディレクトリ | `./jgrants_files` |

（CIは上記の README 想定値と整合するように構成しています。）

## テスト
```
pip install -r requirements.txt
pytest tests/test_core.py
```

## GitHub Actions について
- `CI` ワークフロー：`push`/`pull_request` で Python 3.11、`pip` キャッシュ利用、`pytest` を実行。
- `Security` ワークフロー：CodeQL + Dependency Review を `main` で `push`/`pull_request`/週次スケジュール実行。脆弱性差分は PR で fail-on-severity=high。
- `Release` ワークフロー：`v*.*.*` タグをトリガに GHCR へ `docker/build-push-action` でイメージ公開、`sigstore/cosign-installer` で keyless 署名。
- `Nightly backup` ワークフロー（任意）：Supabase などのバックアップや監査ログを UTC 18:00 に取得し `actions/upload-artifact` で 30 日保存。

## Repository Secrets / Variables
| 名前 | 用途 |
| --- | --- |
| `JGRANTS_API_BASE` | API_BASE_URL は README 想定値以外を使う場合のみ設定 |
| `SUPABASE_SERVICE_ROLE` | Nightly バックアップなどで使用する場合 |
| `GHCR_IMAGE` | デフォルト `ghcr.io/cursorvers/jgrants-mcp` を上書き可能 |

署名は `cosign` の keyless モード（OIDC）なので追加鍵は不要ですが、`Release` ワークフローに `id-token: write` 権限を与えてください。

## ローカルで FastMCP サーバを起動する
```
pip install -r requirements.txt
uvicorn jgrants_mcp_server.server:app --host 0.0.0.0 --port 8000
```
`/health` でステータスを確認でき、`/v1/jgrants-info` では現在の設定値を返します。

## GitHub 設定の自動化とチェックリスト
`docs/github-settings.md` に GitHub Settings 画面での操作と `gh api` を使ったコマンド例を記載しました。Actions の許可リスト・Workflow 権限・フォーク PR 承認・Environment の承認ルール・Branch Protection・Secret Scanning Push Protection を順に構成してください。

## Automation helper
`scripts/check_github_settings.py` を使うと、SHA pinning された Actions、主要な Environments、Branch Protection、Secret Scanning の状態が API から確認できます。GitHub トークン (例: `GITHUB_TOKEN` または `GH_TOKEN`) を用意した上で次を実行してください。

```bash
python scripts/check_github_settings.py --repo cursorvers/jgrants-mcp
```

CI や Settings 変更後にこのコマンドを走らせれば、要求されたガードレールが維持されているかを自動的に検証できます。
