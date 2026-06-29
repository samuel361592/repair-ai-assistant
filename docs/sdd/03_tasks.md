# LangChain 維修問題分析助手 v0.1 任務拆解

## Task 1：建立 SDD 文件資料夾

建立以下資料夾：

```text
docs/sdd
```

並建立以下文件：

```text
docs/sdd/01_requirements.md
docs/sdd/02_design.md
docs/sdd/03_tasks.md
docs/sdd/04_acceptance_criteria.md
```

---

## Task 2：建立程式資料夾

建立以下資料夾：

```text
src/repair_assistant
```

建立以下檔案：

```text
src/repair_assistant/__init__.py
src/repair_assistant/config.py
src/repair_assistant/chains.py
src/repair_assistant/main.py
```

---

## Task 3：實作 config.py

檔案位置：

```text
src/repair_assistant/config.py
```

需求：

1. 使用 `dotenv.load_dotenv()` 載入 `.env`
2. 使用 `os.getenv()` 讀取環境變數
3. 需要讀取：

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
```

4. 若缺少任一設定，需 raise `ValueError`
5. 錯誤訊息需明確指出缺少哪個環境變數
6. 提供 `get_settings()` 函式

建議介面：

```python
def get_settings() -> dict:
    ...
```

---

## Task 4：實作 chains.py

檔案位置：

```text
src/repair_assistant/chains.py
```

需求：

1. 從 `config.py` 取得設定
2. 使用 `ChatOpenAI` 建立模型
3. 使用 `ChatPromptTemplate` 建立 Prompt
4. 使用 `StrOutputParser` 建立 Parser
5. 使用 LCEL 組合 Chain
6. 提供 `build_repair_analysis_chain()` 函式
7. 提供 `analyze_repair_problem(problem: str) -> str` 函式

必要套件：

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
```

Chain 組合方式：

```python
chain = prompt | model | parser
```

---

## Task 5：設計維修分析 Prompt

Prompt 需要符合以下要求：

1. 角色設定為印表機與設備維修助理
2. 使用初學維修人員也能理解的方式輸出
3. 不可直接宣稱某個原因一定正確
4. 需要使用「可能」語氣
5. 若資訊不足，需要明確指出
6. 輸出固定格式

固定格式：

```md
## 問題摘要

## 可能原因

## 初步檢查方向

## 需要補問的資訊

## 建議處理優先順序
```

---

## Task 6：實作 src/repair_assistant/main.py

檔案位置：

```text
src/repair_assistant/main.py
```

需求：

1. 顯示系統名稱
2. 提示使用者輸入故障描述
3. 檢查輸入不可為空
4. 呼叫 `analyze_repair_problem(problem)`
5. 印出分析結果
6. 若發生錯誤，顯示清楚錯誤訊息

建議流程：

```text
顯示系統名稱
→ input() 讀取故障描述
→ strip() 清除空白
→ 若空白則提示錯誤
→ 呼叫 analyze_repair_problem()
→ print 結果
```

---

## Task 7：更新根目錄 main.py

檔案位置：

```text
main.py
```

需求：

根目錄 `main.py` 只作為 entry point，不放主要邏輯。

內容：

```python
from src.repair_assistant.main import main

if __name__ == "__main__":
    main()
```

---

## Task 8：確認 .env 設定

`.env` 至少需要包含：

```env
OPENAI_API_KEY=你的_api_key
OPENAI_BASE_URL=你的_base_url
OPENAI_MODEL=你的_model_name
```

範例：

```env
OPENAI_API_KEY=sk-xxxxx
OPENAI_BASE_URL=https://api.banana2556.com/v1
OPENAI_MODEL=gpt-5.4-mini-as
```

注意：

`.env` 不可提交到 GitHub。

---

## Task 9：確認 .gitignore

`.gitignore` 至少需要包含：

```gitignore
.env
.venv/
__pycache__/
*.pyc
```

---

## Task 10：執行測試

執行指令：

```bash
uv run python main.py
```

測試輸入：

```text
客戶說印表機一直卡紙，重新開機後還是一樣，紙張大概卡在出紙口附近。
```

預期輸出需包含：

```text
問題摘要
可能原因
初步檢查方向
需要補問的資訊
建議處理優先順序
```

---

## Task 11：更新 README.md

README 需要包含：

1. 專案簡介
2. 安裝方式
3. `.env` 設定方式
4. 執行方式
5. 範例輸入
6. 範例輸出
7. 後續版本規劃

---

## Task 12：完成 v0.1 驗收

確認以下項目：

- [ ] 可正常讀取 `.env`
- [ ] 可正常建立 ChatOpenAI model
- [ ] 可正常建立 LangChain Chain
- [ ] 可從終端機輸入故障描述
- [ ] 輸入空白時會提示錯誤
- [ ] 可輸出固定格式分析結果
- [ ] 程式已拆分為 config.py、chains.py、main.py
- [ ] 根目錄 main.py 只作為 entry point