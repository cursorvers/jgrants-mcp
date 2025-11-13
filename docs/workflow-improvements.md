# ワークフロー改善履歴

最終更新: 2025-11-13

## 実施した改善

### 1. Security ワークフローの改善

**問題**: CodeQL が GitHub Advanced Security が有効でない場合にワークフロー全体を失敗させていた

**解決方法**:
- `github/codeql-action/analyze@v3` ステップに `continue-on-error: true` を追加
- エラー時には警告メッセージを表示して、ワークフローを続行

**結果**: Security ワークフローが成功（警告付き）するようになりました

### 2. Release ワークフローの改善

**問題**: cosign 署名時に TUF メタデータ更新エラーが発生し、一時的なネットワーク問題で失敗していた

**解決方法**:
- cosign 署名にリトライロジックを追加
- 最大3回まで自動リトライ（5秒間隔）
- 各イメージ（タグ付きと latest）に対して個別にリトライ

**結果**: リトライロジックは追加されましたが、根本的な問題（Sigstore の TUF メタデータ更新エラー）は外部サービスの問題の可能性があります

## 現在の状況

### ✅ 成功しているワークフロー
- **CI ワークフロー**: 正常に動作
- **Security ワークフロー**: 成功（警告付き）

### ⚠️ 課題があるワークフロー
- **Release ワークフロー**: cosign 署名エラー
  - エラー: `error updating to TUF remote mirror: invalid key`
  - 原因: Sigstore の TUF メタデータ更新エラー（外部サービスの問題の可能性）
  - 対策: リトライロジックを追加済み、時間をおいて再実行を推奨

## 今後の改善案

1. **cosign のバージョン更新**: 最新バージョンで問題が解決されている可能性
2. **TUF キャッシュのクリア**: 環境変数で TUF の設定を調整
3. **代替署名方法の検討**: キーベースの署名に切り替える（ただし、keyless の利点が失われる）

## 参考リンク

- [Sigstore Cosign Documentation](https://docs.sigstore.dev/)
- [GitHub Actions Workflow Troubleshooting](https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows)
- [CodeQL Action Documentation](https://docs.github.com/en/code-security/code-scanning/using-codeql-code-scanning-with-your-existing-ci-system/using-codeql-cli-in-your-ci-system)

