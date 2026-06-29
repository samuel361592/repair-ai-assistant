# LangChain 維修問題分析助手 v0.1 需求規格

## 1. 專案名稱

LangChain 維修問題分析助手 v0.1

## 2. 專案目標

建立一個基於 LangChain 的維修問題分析助手。

使用者輸入一段設備或印表機故障描述後，系統需要透過 LangChain Chain 呼叫 LLM，並輸出結構化的維修分析結果。

本版本不接資料庫、不做 RAG、不呼叫外部 CRM API、不做 Agent Tool Calling，只專注完成以下能力：

- 讀取 `.env` 環境設定
- 建立 LangChain ChatOpenAI 模型
- 使用 ChatPromptTemplate 建立提示詞
- 使用 StrOutputParser 解析輸出
- 使用 LCEL 組合 Chain
- 從終端機輸入故障描述
- 輸出固定格式的維修分析結果

## 3. 使用者情境

維修人員、客服或系統操作人員收到客戶的故障描述，例如：

```text
客戶說印表機一直卡紙，重新開機後還是一樣，紙張大概卡在出紙口附近。
```

系統需要協助整理成可讀性較高的維修分析內容，包含：

1. 問題摘要
2. 可能原因
3. 初步檢查方向
4. 需要補問的資訊
5. 建議處理優先順序

## 4. 功能需求

### FR-001：讀取環境變數

系統需要從 `.env` 讀取以下設定：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`

若任一必要設定不存在，系統需要顯示明確錯誤訊息。

---

### FR-002：建立 LangChain 模型

系統需要使用 `langchain_openai.ChatOpenAI` 建立模型實例。

模型設定來源如下：

| 設定項目 | 來源 |
|---|---|
| model | OPENAI_MODEL |
| base_url | OPENAI_BASE_URL |
| api_key | OPENAI_API_KEY |
| temperature | 固定為 0 |

---

### FR-003：建立維修問題分析 Chain

系統需要使用以下 LangChain 元件建立 Chain：

- `ChatPromptTemplate`
- `ChatOpenAI`
- `StrOutputParser`

Chain 組合方式需使用 LCEL：

```python
chain = prompt | model | parser
```

---

### FR-004：支援使用者輸入故障描述

系統需要允許使用者從終端機輸入一段故障描述。

若使用者輸入空字串，系統需要提示：

```text
請輸入故障描述，不可為空。
```

---

### FR-005：輸出固定格式分析結果

系統輸出需包含以下區塊：

```md
## 問題摘要

## 可能原因

## 初步檢查方向

## 需要補問的資訊

## 建議處理優先順序
```

每個區塊的要求如下：

| 區塊 | 說明 |
|---|---|
| 問題摘要 | 用一句話整理使用者描述的故障問題 |
| 可能原因 | 列出 3 個可能原因 |
| 初步檢查方向 | 列出 3 個維修人員可先檢查的方向 |
| 需要補問的資訊 | 列出還需要向客戶或維修人員確認的資訊 |
| 建議處理優先順序 | 用步驟方式列出建議處理順序 |

---

## 5. 非功能需求

### NFR-001：程式結構清楚

程式不得全部寫在根目錄 `main.py`。

需要拆分成以下模組：

```text
src/repair_assistant/
├── __init__.py
├── config.py
├── chains.py
└── main.py
```

---

### NFR-002：方便後續擴充

本版本需保留後續擴充空間，未來可以升級成：

- v0.2：Structured Output JSON
- v0.3：RAG 查詢維修手冊
- v0.4：Tool Calling 查詢歷史維修紀錄
- v0.5：LangGraph Workflow
- v0.6：FastAPI API Server
- v0.7：Web UI

---

### NFR-003：模型輸出穩定

Prompt 需要明確限制輸出格式，避免模型每次輸出結構差異過大。

---

### NFR-004：錯誤訊息清楚

當系統發生以下情況時，需要提供清楚錯誤訊息：

- `.env` 未設定
- 缺少必要環境變數
- 使用者輸入空白內容
- 模型呼叫失敗

---

## 6. 本版本不處理的範圍

v0.1 不處理以下功能：

- PDF 讀取
- 文件切片
- Embedding
- Vector Store
- RAG
- Agent
- Tool Calling
- CRM API 串接
- Web UI
- 資料庫儲存
- 使用者登入