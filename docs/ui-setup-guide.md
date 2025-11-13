# GitHub UI 設定ガイド

このドキュメントは、GitHub リポジトリの Settings を UI で設定する手順を説明します。`docs/github-settings.md` の要件に沿って、順番に設定を完了してください。

## 設定手順の概要

1. **Settings → Actions → General**
2. **Settings → Environments**
3. **Settings → Code security and analysis**
4. **Settings → Branches**

各設定項目の詳細は `docs/github-settings.md` を参照してください。

## 1. Actions → General の設定

### 1.1 Actions の利用可否と使用可能Actionsの範囲

1. リポジトリの **Settings** → **Actions** → **General** に移動
2. **Actions permissions** セクションで **Allow select actions and reusable workflows** を選択
3. 以下をチェック：
   - ✅ **Allow actions created by GitHub**
   - ✅ **Allow Marketplace actions by verified creators**
4. **Allow specified actions and reusable workflows** セクションで、以下のアクションを SHA で追加：

```
actions/checkout@08eba0b27e820071cde6df949e0beb9ba4906955
actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
actions/cache@6f8efc29b200d32929f49075959781ed54ec270c
actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
actions/download-artifact@9bc31d5ccc31df68ecc42ccf4149144866c47d8a
docker/login-action@465a07811f14bebb1938fbed4728c6a1ff8901fc
docker/setup-buildx-action@885d1462b80bc1c1c7f0b00334ad271f09369c55
docker/build-push-action@ca052bb54ab0790a636c9b5f226502c73d547a25
sigstore/cosign-installer@c85d0e205a72a294fe064f618a87dbac13084086
github/codeql-action/init@v3
github/codeql-action/analyze@v3
actions/dependency-review-action@93809e13f07c0db8c2db3c320885d98f2d235acc
```

### 1.2 Workflow permissions

- **Workflow permissions** セクションで **Read repository contents and packages permissions** を選択
- **Allow GitHub Actions to create and approve pull requests** は OFF のまま

### 1.3 Fork pull request workflows

- **Fork pull request workflows** セクションで **Require approval for first-time contributors** を ON

### 1.4 Artifact and log retention

- **Artifact and log retention** を **30 days** に設定

## 2. Environments の設定

### 2.1 環境の作成

1. **Settings** → **Environments** に移動
2. **New environment** をクリックして、以下を作成：
   - `dev`
   - `stg`
   - `prod`

### 2.2 stg 環境の設定

1. `stg` 環境を選択
2. **Deployment protection rules** セクションで：
   - **Required reviewers**: 1 名を追加
   - **Wait timer**: 10 分に設定

### 2.3 prod 環境の設定

1. `prod` 環境を選択
2. **Deployment protection rules** セクションで：
   - **Required reviewers**: 2 名を追加
   - **Prevent self-reviews** を ON
   - **Allow admins to bypass** を OFF
   - **Deployment branches**: **Selected branches** を選択し、`main` のみを指定

> **注意**: 環境保護ルールは GitHub Pro プラン以上が必要です。無料プランの場合は、この機能は利用できません。

## 3. Code security and analysis の設定

### 3.1 CodeQL

1. **Settings** → **Code security and analysis** に移動
2. **Code scanning** セクションで **Set up** をクリック
3. **Set up this workflow** を選択（または既存のワークフローを使用）
4. 言語は自動検出されます（Python）

### 3.2 Dependabot

1. **Dependabot alerts** を **Enable** に設定
2. **Dependabot security updates** を **Enable** に設定
3. **Dependabot version updates** は `.github/dependabot.yml` で設定済み

### 3.3 Secret scanning

1. **Secret scanning** セクションで **Enable** をクリック
2. **Push protection** を **Enable** に設定

## 4. Branch protection の設定

> **注意**: Branch protection は GitHub Pro プラン以上が必要です。

1. **Settings** → **Branches** に移動
2. **Add branch protection rule** をクリック
3. **Branch name pattern** に `main` を入力
4. 以下を設定：
   - ✅ **Require a pull request before merging**
     - **Required number of approvals**: 1
   - ✅ **Require status checks to pass before merging**
     - 必須チェックを追加：
       - `CI (unit)`
       - `Security / CodeQL`
       - `Dependency Review`
   - ✅ **Require branches to be up to date before merging**

## 設定の検証

設定完了後、以下のコマンドで検証してください：

```bash
export GITHUB_TOKEN=$(gh auth token)
python3 scripts/check_github_settings.py --repo cursorvers/jgrants-mcp
```

## ワークフローの再実行と確認

設定完了後、ワークフローを再実行して動作を確認します：

```bash
# ワークフロー実行状況の確認
gh run list --repo cursorvers/jgrants-mcp --limit 10

# 特定のワークフローの詳細確認
gh run view <run-id> --repo cursorvers/jgrants-mcp

# 失敗したワークフローのログ確認
gh run view <run-id> --repo cursorvers/jgrants-mcp --log-failed
```

### Release ワークフローのテスト

Release ワークフローをテストするには、タグを作成して push します：

```bash
git tag v0.1.0
git push origin v0.1.0
```

`prod` 環境の承認が必要な場合、GitHub UI で承認を行ってください。

