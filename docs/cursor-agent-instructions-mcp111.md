# Cursor Agent 指示書: MCP-111 `/v1/search` のスキーマ＆堅牢性

**タスクID**: MCP-111  
**目的**: Cursor IDE / Kamui OS 上で動く BFF やエージェントが `/v1/search` を使ううえで、入力・出力のスキーマと通信仕様（httpx + 再試行）・異常系テストを明文化する

---

## 0. 背景

- Python 側の `jgrants_mcp_server/search.py` に `SearchQuery`/`SearchResponse` 型と `SearchService` が定義されており、Cursor からは「この `/v1/search` に自然文のパラメータを投げれば補助金一覧が返ってくる」という契約を利用する。
- このエンドポイントは `SearchService` が `settings.api_base_url`（デフォルト `https://api.jgrants-portal.go.jp/exp/v1/public`）の `/search` を `httpx.AsyncClient` 経由で叩き、受け取った JSON を `SearchResult` へ正規化したものを返す。
- Cursor 系または Kamui OS 上位は、`/v1/search` を不変の API と考えて指定のパラメータと戻り値を使い、異常系の振る舞いは今後も変化しないようテストとドキュメントで保証する。

---

## 1. 期待する成果（Cursor 側のゴール）

1. `/v1/search` に与えるクエリは `keyword` を必須とし、`area`/`acceptance`/`sort` を任意で送る。固定のスキーマを守ることで BFF への自然文変換コードとの整合性を担保する。
2. レスポンスは `items: SearchResult[]` であり、Cursor は `id/title/issuer/deadline/url` を参照することを共通理解とする。
3. BFF や Cursor agent 側でも検索の異常系（タイムアウト・サーバエラー・通信断）を同じ HTTP ステータスでハンドリングできるよう、httpx + retry の仕様を一貫して理解する。
4. 自動テスト（`tests/test_search.py`）を常に green に保ち、timeout/5xx/transport のケースが漏れていないことを確認する。

---

## 2. `/v1/search` の入力スキーマ（Cursor 側が呼び出す際に守るべき契約）

### 2-1. HTTP メソッドとパス

- **メソッド**: `GET`
- **パス**: `/v1/search`
- **Content-Type**: 不要（クエリパラメータで送信）

### 2-2. クエリパラメータ

| パラメータ | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `keyword` | `string` | ✅ | 検索キーワード。最低2文字以上。 |
| `area` | `string \| null` | ❌ | 地域コードなど。省略可能。 |
| `acceptance` | `string \| null` | ❌ | 受付ステータスフィルタ。省略可能。 |
| `sort` | `string \| null` | ❌ | ソート指示（`deadline` / `issuer` など）。省略可能。 |

**例**:
```
GET /v1/search?keyword=IT&area=JP-13&acceptance=accepting&sort=deadline
```

---

## 3. `/v1/search` の出力スキーマ（MCP サーバが返す契約）

### 3-1. 正常レスポンス（HTTP 200）

```json
{
  "items": [
    {
      "id": "a0WJ200000CDNiaMAH",
      "title": "令和7年度 ES...",
      "issuer": "jGrants補助金 (catch phrase)",
      "deadline": "2025-11-14T15:00:00.000Z",
      "url": "https://www.jgrants-portal.go.jp/subsidy/a0WJ200000CDNiaMAH"
    }
  ]
}
```

**フィールド説明**:
- `items`: `SearchResult[]` - 検索結果配列（最大10件程度を想定）
- `id`: Jグランツ API の `id` フィールド
- `title`: 補助金のタイトル
- `issuer`: 発行元（省庁・団体名）
- `deadline`: ISO8601形式の締切日時
- `url`: 補助金詳細ページのURL

### 3-2. エラーレスポンス

#### HTTP 400 Bad Request
- `keyword` が2文字未満の場合
- 必須パラメータが欠落している場合

#### HTTP 502 Bad Gateway
- 上流API（Jグランツ公開API）が5xxエラーを返した場合
- リトライ後も5xxエラーが続いた場合

#### HTTP 503 Service Unavailable
- 上流APIへの接続が確立できない場合（TransportError）
- リトライ後も接続できない場合

#### HTTP 504 Gateway Timeout
- 上流APIへのリクエストがタイムアウトした場合（ReadTimeout）
- リトライ後もタイムアウトが続いた場合

---

## 4. httpx の retry と timeout 仕様

### 4-1. タイムアウト設定

- **timeout**: `3.0秒`（デフォルト）
- `httpx.AsyncClient(timeout=3.0)` で設定

### 4-2. リトライ設定

- **max_retries**: `3回`（初回含む）
- **backoff_factor**: `0.2`（指数バックオフの係数）
- **リトライ間隔**: `0.2秒 × (2 ^ attempt)` で指数バックオフ
  - 1回目: 0.2秒
  - 2回目: 0.4秒
  - 3回目: 0.8秒

### 4-3. リトライ対象エラー

以下のエラーが発生した場合、リトライを実行：

1. **httpx.ReadTimeout**: タイムアウトエラー → リトライ後も失敗なら HTTP 504
2. **httpx.TransportError**: 接続エラー → リトライ後も失敗なら HTTP 503
3. **httpx.HTTPStatusError (5xx)**: サーバエラー → リトライ後も失敗なら HTTP 502

**4xxエラーはリトライしない**（クライアントエラーのため）

---

## 5. pytest 要件（`tests/test_search.py`）

### 5-1. 正常系テスト

- **test_search_service_returns_normalized_payload**: 正常なレスポンスが正規化されることを確認

### 5-2. 異常系テスト（必須）

以下の3つのケースを `pytest.mark.parametrize` で網羅：

1. **timeout ケース**:
   - `httpx.ReadTimeout` を3回発生させる
   - 最終的に `SearchBackendError` が `HTTP_504_GATEWAY_TIMEOUT` で発生することを確認

2. **5xx ケース**:
   - HTTP 500 レスポンスを3回返す
   - 最終的に `SearchBackendError` が `HTTP_502_BAD_GATEWAY` で発生することを確認

3. **transport ケース**:
   - `httpx.TransportError` を3回発生させる
   - 最終的に `SearchBackendError` が `HTTP_503_SERVICE_UNAVAILABLE` で発生することを確認

### 5-3. テスト実行コマンド

```bash
PYTHONPATH=. pytest tests/test_search.py -v
```

**期待される結果**: すべてのテストが通過（green）

---

## 6. 実装ファイル

### 6-1. 主要ファイル

- **`jgrants_mcp_server/search.py`**: `SearchService` と `/v1/search` エンドポイントの実装
- **`tests/test_search.py`**: 正常系＋異常系（timeout/5xx/transport）のテスト

### 6-2. 型定義

- **`SearchQuery`**: 入力パラメータの型
- **`SearchResult`**: 検索結果1件の型
- **`SearchResponse`**: レスポンス全体の型
- **`SearchBackendError`**: バックエンドエラーをラップする例外

---

## 7. 完了条件（受け入れ基準）

- [x] `/v1/search` エンドポイントが実装されている
- [x] `keyword` が必須で、最低2文字のバリデーションがある
- [x] `httpx` で3秒タイムアウト + 3回リトライ + 指数バックオフが実装されている
- [x] 異常時に適切なHTTPステータス（504/503/502）を返す
- [x] `tests/test_search.py` で timeout/5xx/transport のケースがカバーされている
- [x] `PYTHONPATH=. pytest tests/test_search.py` で全テストが通過している

---

## 8. 参考情報

- **実装ファイル**: `jgrants_mcp_server/search.py`
- **テストファイル**: `tests/test_search.py`
- **設定ファイル**: `jgrants_mcp_server/config.py`（`settings.api_base_url`）

---

**作成日**: 2024年11月14日  
**対象**: Cursor Agent / Kamui OS  
**ステータス**: ✅ 完了

