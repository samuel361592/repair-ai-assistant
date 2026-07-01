# LangChain 維修問題分析助手 v0.3

這是一個以 LangChain LCEL 實作的命令列助手。v0.3 保留原有 Structured Output 維修分析，並新增根據本地 Markdown/TXT 維修手冊回答問題的 RAG 功能。

目前提供兩個彼此獨立的流程：

```text
維修問題分析：
使用者輸入
→ ChatPromptTemplate
→ ChatOpenAI.with_structured_output(method="json_mode")
→ RepairAnalysis
→ Markdown CLI 輸出

維修手冊 RAG：
本地手冊
→ 文件切片
→ OpenAIEmbeddings
→ Chroma
→ Retriever
→ 根據檢索內容回答並顯示來源
```

目前版本不包含 PDF、OCR、Agent、Tool Calling、LangGraph、FastAPI 或 Web UI。

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
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
RAG_MANUALS_DIR=data/manuals
RAG_VECTORSTORE_DIR=data/vectorstore/chroma
```

前三個值不可省略或留空。後三個 RAG 設定為可選，未設定時會使用上述預設值。`.env` 已列入 `.gitignore`，不應提交至版本控制。

## 執行維修問題分析

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

## 維修手冊 RAG

### 1. 放置手冊

將 UTF-8 編碼的 `.md` 或 `.txt` 手冊放入：

```text
data/manuals/
```

目前包含測試用的 `data/manuals/sample_manual.md`。v0.3 不支援 PDF、圖片或 Word 文件。

### 2. 建立或重建向量庫

```powershell
uv run repair-rag-ingest
```

這會讀取手冊、以 800 字元和 120 字元重疊切片，使用 `OPENAI_EMBEDDING_MODEL` 建立 embedding，並將 Chroma 資料寫入 `data/vectorstore/chroma`。

`data/vectorstore/` 已加入 `.gitignore`，不會提交至 GitHub。

### 3. 詢問手冊問題

```powershell
uv run repair-rag-qa
```

範例問題：

```text
出紙口卡紙要怎麼處理？
```

輸出會包含回答及由程式根據 retrieved documents metadata 產生的來源：

```md
## 回答

根據手冊內容，請先關閉設備電源，打開出紙口蓋板並小心取出殘紙。

## 來源

1. data/manuals/sample_manual.md，chunk 1
```

若沒有檢索到手冊內容，系統會回答：

```text
目前手冊資料不足，無法確認。
```

## 測試

測試使用 Python 內建的 `unittest`，不會連線或呼叫實際模型 API：

```powershell
uv run python -m unittest discover -s tests -v
```

端到端模型測試會使用 `.env` 並呼叫實際 API：

```powershell
uv run python main.py
uv run repair-rag-ingest
uv run repair-rag-qa
```

RAG 建庫與問答需要 API provider 同時支援設定的 chat model 與 embedding model。

## 後續版本規劃

PDF/OCR、API、Web UI、CRM 串接與多輪對話等能力需另行撰寫 SDD；它們不在 v0.3 的實作範圍內。
