# ワークフロートラブルシューティングガイド

このドキュメントは、GitHub Actions ワークフローの問題を診断・解決するためのガイドです。

## よくある問題と解決方法

### 1. CI ワークフローの失敗

#### 問題: `ModuleNotFoundError: No module named 'httpx'`
**解決方法**: `requirements.txt` に `httpx>=0.24` を追加

#### 問題: テストが失敗する
**確認項目**:
- `pytest tests/test_core.py` がローカルで成功するか
- 環境変数が正しく設定されているか

### 2. Security ワークフローの失敗

#### 問題: CodeQL の権限エラー
**エラーメッセージ**: `Resource not accessible by integration`

**解決方法**: Security ワークフローの CodeQL ジョブに `actions: read` 権限を追加

```yaml
jobs:
  codeql:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
      actions: read  # これを追加
```

#### 問題: Dependency Review が実行されない
**原因**: PR イベントでのみ実行されるため、`push` イベントでは実行されません

**確認方法**: PR を作成して確認

### 3. Release ワークフローの失敗

#### 問題: cosign 署名エラー
**エラーメッセージ**: `error updating to TUF remote mirror: invalid key`

**原因**: 一時的なネットワーク問題または TUF メタデータの更新エラー

**解決方法**:
1. ワークフローを再実行
2. cosign のバージョンを確認・更新
3. ネットワーク接続を確認

**再実行コマンド**:
```bash
gh run rerun <run-id> --repo cursorvers/jgrants-mcp
```

#### 問題: 環境保護ルールが機能しない
**原因**: GitHub Pro プランが必要、または環境保護ルールが設定されていない

**解決方法**:
1. Settings → Environments → `prod` で保護ルールを設定
2. Required reviewers: 2名
3. Prevent self-reviews: ON
4. Allow admin bypass: OFF

### 4. ワークフローのログ確認方法

```bash
# ワークフロー実行一覧
gh run list --repo cursorvers/jgrants-mcp --limit 10

# 特定のワークフローの詳細
gh run view <run-id> --repo cursorvers/jgrants-mcp

# 失敗したステップのログ
gh run view <run-id> --repo cursorvers/jgrants-mcp --log-failed

# 特定のジョブのログ
gh run view <run-id> --repo cursorvers/jgrants-mcp --job=<job-id>
```

### 5. GitHub Settings の検証

設定変更後は、検証スクリプトを実行して整合性を確認：

```bash
export GITHUB_TOKEN=$(gh auth token)
python3 scripts/check_github_settings.py --repo cursorvers/jgrants-mcp
```

### 6. 承認フローの確認

Release ワークフローで `environment: prod` を使用している場合：

1. GitHub UI でワークフロー実行を確認
2. 承認待ちの場合は、**Review deployments** をクリック
3. 承認を実行

**API で確認**:
```bash
gh api repos/cursorvers/jgrants-mcp/actions/runs/<run-id>/pending_deployments
```

承認が必要な場合、空の配列ではなく、承認待ちのデプロイメント情報が返されます。

## 修正履歴

- `fix: Add httpx dependency for test client` - CI ワークフローの依存関係を修正
- `fix: Update CodeQL Action to v3` - CodeQL Action を v3 に更新
- `fix: Add actions:read permission for CodeQL workflow` - CodeQL の権限を修正

