from __future__ import annotations

from fastapi import FastAPI
from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings


class MCPConfig(BaseSettings):
    """Compute and expose environment-driven settings used by the MCP server."""

    api_base_url: HttpUrl = Field(
        default="https://api.jgrants-portal.go.jp/exp/v1/public",
        description="Digital庁 Jグランツの公開 API ベース URL",
    )
    jgrants_files_dir: str = Field(
        default="./jgrants_files",
        description="ローカルに保存するファイル群のディレクトリ",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = MCPConfig()

app = FastAPI(
    title="jgrants MCP Server",
    version="0.1.0",
    description="FastMCP 構想に基づく簡易サーバ。将来的にはチャット UI と連携した MCP ロジックをホストします。",
)


@app.get("/health")
async def health() -> dict[str, str]:
    """クラスタの状態を見るための簡易ヘルスチェックを提供します。"""
    return {
        "status": "ok",
        "api_base_url": str(settings.api_base_url),
    }


@app.get("/v1/jgrants-info")
async def jgrants_info() -> dict[str, str]:
    """現在の設定値を返すだけのハンドラ。実装の拡張ポイント。"""
    return {
        "api_base_url": str(settings.api_base_url),
        "jgrants_files_dir": settings.jgrants_files_dir,
    }
