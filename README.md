# LangChain 維修問題分析助手 v0.2

這是一個以 LangChain LCEL 實作的命令列助手。v0.2 使用 LangChain Structured Output，讓模型先回傳經 Pydantic 驗證的 `RepairAnalysis` 物件，再由 CLI 格式化成 Markdown。

```text
使用者輸入
→ ChatPromptTemplate
→ ChatOpenAI.with_structured_output(method="json_mode")
→ RepairAnalysis
→ Markdown CLI 輸出
```

目前版本不包含 RAG、Agent、一般 Tool Calling、LangGraph、FastAPI 或 Web UI。

## Structured Output Schema

`RepairAnalysis` 包含以下欄位：

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| `summary` | `str` | 一句話整理故障問題 |
| `possible_causes` | `list[str]` | 可能原因，至少 3 筆 |
| `check_steps` | `list[str]` | 初步檢查方向，至少 3 筆 |
| `questions` | `list[str]` | 需要補問的資訊，至少 3 筆 |
| `priority_steps` | `list[str]` | 建議處理優先順序，至少 3 筆 |

## 安裝

請先安裝 [uv](https://docs.astral.sh/uv/)，再於專案根目錄執行：

```powershell
uv sync
```

## 設定 `.env`

在專案根目錄建立 `.env`，填入以下三個必要環境變數：

```dotenv
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://your-api-base-url/v1
OPENAI_MODEL=your-model-name
```

三個值都不可省略或留空。`.env` 已列入 `.gitignore`，不應提交至版本控制。

## 執行

從根目錄入口啟動：

```powershell
uv run python main.py
```

也可以使用套件命令：

```powershell
uv run repair-assistant
```

看到提示後輸入非空白的維修問題，例如：

```text
客戶說印表機一直卡紙，重新開機後還是一樣，紙張大概卡在出紙口附近。
```

輸出範例：

```md
## 問題摘要

印表機在出紙口附近反覆卡紙。

## 可能原因

1. 出紙口可能有殘紙或異物阻塞
2. 出紙滾輪可能髒污或磨損
3. 紙張規格可能與紙匣設定不一致

## 初步檢查方向

1. 檢查出紙口是否有殘紙或異物
2. 檢查出紙滾輪狀態
3. 確認紙張與紙匣設定

## 需要補問的資訊

1. 卡紙是否都發生在相同位置？
2. 使用的紙張尺寸與種類是什麼？
3. 最近是否更換過紙張或耗材？

## 建議處理優先順序

1. 先檢查明顯異物
2. 再確認紙張設定
3. 最後檢查滾輪與出紙機構
```

## 測試

測試使用 Python 內建的 `unittest`，不會連線或呼叫實際模型 API：

```powershell
uv run python -m unittest discover -s tests -v
```

端到端模型測試會使用 `.env` 並呼叫實際 API：

```powershell
uv run python main.py
```

## 後續版本規劃

RAG、API、Web UI、CRM 串接與多輪對話等能力需另行撰寫 SDD；它們不在 v0.2 的實作範圍內。
