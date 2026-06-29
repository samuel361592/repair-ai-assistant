# LangChain 維修問題分析助手 v0.1 設計文件

## 1. 系統概要

本系統是一個命令列工具。

使用者從終端機輸入故障描述後，系統會透過 LangChain Chain 呼叫 LLM，並輸出固定格式的維修分析結果。

---

## 2. 系統流程

```text
使用者啟動程式
→ 載入 .env
→ 檢查環境變數
→ 建立 ChatOpenAI Model
→ 建立 ChatPromptTemplate
→ 建立 StrOutputParser
→ 組合 LangChain Chain
→ 使用者輸入故障描述
→ 檢查輸入不可為空
→ 執行 chain.invoke()
→ 輸出維修分析結果
```

---

## 3. 專案結構設計

目標結構如下：

```text
LANGCHAIN/
├── docs/
│   └── sdd/
│       ├── 01_requirements.md
│       ├── 02_design.md
│       ├── 03_tasks.md
│       └── 04_acceptance_criteria.md
├── src/
│   └── repair_assistant/
│       ├── __init__.py
│       ├── config.py
│       ├── chains.py
│       └── main.py
├── agents/
├── .env
├── .gitignore
├── .python-version
├── main.py
├── pyproject.toml
├── README.md
└── uv.lock
```

---

## 4. 模組設計

### 4.1 config.py

檔案位置：

```text
src/repair_assistant/config.py
```

責任：

- 載入 `.env`
- 讀取必要環境變數
- 檢查環境變數是否存在
- 回傳設定物件或 dictionary

必要環境變數：

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
```

建議提供函式：

```python
def get_settings() -> dict:
    ...
```

回傳格式：

```python
{
    "api_key": "...",
    "base_url": "...",
    "model": "..."
}
```

若缺少環境變數，需 raise `ValueError`，並指出缺少哪個設定。

---

### 4.2 chains.py

檔案位置：

```text
src/repair_assistant/chains.py
```

責任：

- 建立 ChatOpenAI model
- 建立維修問題分析 prompt
- 建立 StrOutputParser
- 組合 LangChain Chain
- 提供分析函式

建議提供函式：

```python
def build_repair_analysis_chain():
    ...
```

```python
def analyze_repair_problem(problem: str) -> str:
    ...
```

---

### 4.3 main.py

檔案位置：

```text
src/repair_assistant/main.py
```

責任：

- 作為實際程式流程入口
- 顯示系統提示
- 讀取使用者輸入
- 檢查輸入不可為空
- 呼叫 `analyze_repair_problem`
- 印出結果

建議提供函式：

```python
def main():
    ...
```

---

### 4.4 根目錄 main.py

檔案位置：

```text
main.py
```

責任：

- 只作為專案啟動入口
- 不放主要業務邏輯

內容應為：

```python
from src.repair_assistant.main import main

if __name__ == "__main__":
    main()
```

---

## 5. Chain 設計

使用 LangChain LCEL 組合：

```python
chain = prompt | model | parser
```

其中：

| 元件 | 說明 |
|---|---|
| prompt | ChatPromptTemplate |
| model | ChatOpenAI |
| parser | StrOutputParser |

---

## 6. Prompt 設計

Prompt 角色：

```text
你是一位印表機與設備維修助理。
```

Prompt 任務：

根據使用者提供的故障描述，輸出固定格式的維修分析。

Prompt 需限制：

- 不要編造已確認事實
- 若資訊不足，要明確指出
- 可能原因需使用「可能」語氣
- 檢查方向需可執行
- 補問資訊需具體

輸出格式：

```md
## 問題摘要

## 可能原因

1.
2.
3.

## 初步檢查方向

1.
2.
3.

## 需要補問的資訊

1.
2.
3.

## 建議處理優先順序

1.
2.
3.
```

---

## 7. 錯誤處理設計

### 7.1 缺少環境變數

若缺少 `OPENAI_API_KEY`，錯誤訊息：

```text
缺少必要環境變數：OPENAI_API_KEY
```

若缺少 `OPENAI_BASE_URL`，錯誤訊息：

```text
缺少必要環境變數：OPENAI_BASE_URL
```

若缺少 `OPENAI_MODEL`，錯誤訊息：

```text
缺少必要環境變數：OPENAI_MODEL
```

---

### 7.2 使用者輸入空白

若使用者輸入空字串或只有空白，顯示：

```text
請輸入故障描述，不可為空。
```

---

### 7.3 模型呼叫失敗

若模型呼叫失敗，顯示：

```text
模型呼叫失敗，請檢查 API Key、Base URL 或模型名稱設定。
```

---

## 8. 後續擴充設計

### v0.2：Structured Output

將輸出從 Markdown 改成 JSON，例如：

```json
{
  "summary": "...",
  "possible_causes": [],
  "check_steps": [],
  "questions": [],
  "priority_steps": []
}
```

---

### v0.3：RAG

加入維修手冊知識庫：

```text
PDF
→ Text Splitter
→ Embedding
→ Vector Store
→ Retriever
→ RAG Chain
```

---

### v0.4：Tool Calling

加入工具：

```text
search_repair_history
search_manual_knowledge
classify_problem
generate_repair_steps
```

---

### v0.5：LangGraph

改成可控制流程的 Workflow：

```text
輸入問題
→ 問題分類
→ 查手冊
→ 查歷史紀錄
→ 產生建議
→ 人工確認
→ 輸出結果
```