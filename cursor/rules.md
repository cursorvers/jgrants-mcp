# Cursor Rules (補助金MCPチャット) — v1.1

**目的**  

堅牢・軽量・保守容易を最優先。Kamui OS を主導、Cursor IDE は「実装・テスト・レビュー効率化」の**サブ**として使う。

## 0. スタックとバージョン

- Python: 3.11（MCPサーバ） / Node.js: 20（BFF/Discord）

- コンテナ: python:3.11-slim, node:20-alpine（軽量優先）

- OS依存コードは不可。すべてコンテナで再現可能に。

## 1. ディレクトリ

/apps

/bff # PHI/Domain Gate + Mapper API

/discord # Bot

/packages

/mapper # 自然文→MCP引数（唯一の変換点）

/filters # PHI辞書・検知ロジック

/summarizer # 非同期ワーカー

/infra

/compose

/docs

runbook.md

/cursor

rules.md (本ファイル)

## 2. コーディング規約

**Python（MCP）**

- Lint/Format: `ruff`（E/W すべて有効）、型ヒント必須、I/Oは例外化

- テスト: `pytest -q`（I/Oはfixtureでモック）

- 例外は `from e` で原因を連鎖、ログはINFO最小

**Node（BFF/Discord）**

- TypeScript必須、`eslint` + `tsconfig: strict`

- フレームワークは最小（素のFastify/Expressいずれか、重いORM禁止）

- 外向けリンクは**必ず** Verified Domain経由

**共通**

- ネットワーク・I/Oは5秒デフォタイムアウト

- 秘密情報のログ出力・持ち回り禁止（PHI/PIIは破棄）

## 3. セキュリティ/コンプラ

- Secrets: 環境分離（stg/prod）、**長期キー禁止**、OIDC/短期トークンを優先

- PHI/PII: 最上流で検出→**mask/drop/warn**。本文保存は禁止

- Quiet hours: **21:00–08:00**（通知は翌朝9時へ遅延）

- 免責表示を返すコンポーネントでの自動付与（申請可否の助言は対象外）

- 外部遷移は `https://<自社ドメイン>/go?target=...` の案内1Pを経由

## 4. テスト方針

- **ユニット（必須）**：`/packages/mapper`（自然文→MCP引数）、`/packages/filters`、`/packages/summarizer`

- **E2Eライト（毎日）**：`"在宅"`検索→1件詳細→ファイル**存在のみ**確認（本文は取得しない）

- **性能**：検索 p95 ≤ 2.0s、添付要約 平均 ≤ 6s（並列3）

- **フェイルセーフ**：2回連続失敗でDegrade（要約OFF）→Runbookで復旧

## 5. Git 運用

- ブランチ: `feat/*`, `fix/*`, `chore/*`

- Conventional Commits:

  - `feat(mapper): add headcount filter`

  - `fix(filters): mask street address edge-case`

  - `chore(ci): bump actions/checkout sha`

- PR テンプレ（チェック項目）

  - [ ] ユニットテスト追加/更新

  - [ ] PHI/PIIがログに出ない

  - [ ] Verified Domain 経由の遷移

  - [ ] 2文字未満keywordのバリデーション

  - [ ] p95指標に影響しない

## 6. Cursor 推奨プロンプト（即使い）

- **Mapper テスト生成**  

  _"自然文→MCP引数の単体テストを境界値（keyword=1/2文字、受付状態=受付中/終了、締切ソート昇降）で生成して"_

- **PHI フィルタ改善**  

  _"氏名/住所/検査票/保険番号っぽい入力の疑似データを作り、filtersの偽陽性を下げるテストを追加"_

- **要約器の堅牢化**  

  _"PDFテキスト抽出に失敗した場合のBASE64フォールバックを E2Eライトに組み込む差分を提案して"_

- **パフォーマンス監視**  

  _"BFFのsearch経路で p95 を計測する軽量ミドルウェアを追加し、閾値超過時にWARNログを出す"_

## 7. ビルド/実行（例）

```bash
# MCP
pip install -r requirements.txt && python -m jgrants_mcp_server.core --host 0.0.0.0 --port 8080

# BFF
pnpm i && pnpm dev

# Discord
pnpm -C apps/discord dev

# テスト
pytest -q
pnpm test
```

## 8. 禁止事項

- 添付本文の永続保存

- 長期アクセストークンのハードコード

- Quiet hours を無視した通知

- Verified Domain を経由しない外部リンク

## 9. リリース

Phase 1（Discord GA）→ Phase 2（LINE/ICS）→ Phase 3（Web最小）

カナリア 5% → 全量、失敗時 <10分でロールバック（Runbook記載）

免責・権利脚注は自動付与

Trademarks and brand names are the property of their respective owners and are used for identification only. No endorsement implied.

---

必要なら、**`.github/workflows` の最小CI**（`lint`/`unit`/`e2e-light`）もすぐ添えます。配置や命名を変えたい場合は、希望スタイルを教えてください。

