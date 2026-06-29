# LangChain 維修問題分析助手 v0.1 驗收條件

## AC-001：環境變數驗收

### 條件

`.env` 中存在以下設定：

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
```

### 操作

執行：

```bash
uv run python main.py
```

### 預期結果

系統可以正常啟動，不會因為缺少環境變數而中斷。

---

## AC-002：缺少環境變數驗收

### 條件

`.env` 中缺少任一必要設定，例如：

```text
OPENAI_MODEL
```

### 操作

執行：

```bash
uv run python main.py
```

### 預期結果

系統顯示明確錯誤訊息，例如：

```text
缺少必要環境變數：OPENAI_MODEL
```

---

## AC-003：使用者輸入驗收

### 條件

使用者輸入正常故障描述：

```text
客戶說印表機一直卡紙，重新開機後還是一樣，紙張大概卡在出紙口附近。
```

### 操作

執行程式後，將上述文字輸入終端機。

### 預期結果

系統成功產生維修分析結果。

---

## AC-004：空白輸入驗收

### 條件

使用者沒有輸入任何內容，或只輸入空白。

### 操作

執行程式後，直接按 Enter。

### 預期結果

系統顯示：

```text
請輸入故障描述，不可為空。
```

---

## AC-005：輸出格式驗收

### 條件

使用者輸入任一有效故障描述。

### 操作

執行：

```bash
uv run python main.py
```

輸入：

```text
客戶反應設備開機後有異音，過一段時間後會停止運作。
```

### 預期結果

輸出內容必須包含以下區塊：

```text
問題摘要
可能原因
初步檢查方向
需要補問的資訊
建議處理優先順序
```

---

## AC-006：程式結構驗收

### 條件

專案已完成 v0.1 實作。

### 檢查項目

專案中必須存在以下檔案：

```text
src/repair_assistant/__init__.py
src/repair_assistant/config.py
src/repair_assistant/chains.py
src/repair_assistant/main.py
main.py
```

### 預期結果

主要邏輯不得全部寫在根目錄 `main.py`。

根目錄 `main.py` 只允許作為啟動入口。

---

## AC-007：LangChain Chain 驗收

### 條件

系統已完成 Chain 實作。

### 檢查項目

`chains.py` 中需使用以下元件：

```python
ChatPromptTemplate
ChatOpenAI
StrOutputParser
```

並使用 LCEL 組合：

```python
chain = prompt | model | parser
```

### 預期結果

Chain 可以正常透過 `invoke()` 執行。

---

## AC-008：模型呼叫驗收

### 條件

`.env` 設定正確，API 可正常使用。

### 操作

執行：

```bash
uv run python main.py
```

輸入有效故障描述。

### 預期結果

系統可以成功取得模型回覆並印出結果。

---

## AC-009：錯誤訊息驗收

### 條件

發生以下任一錯誤：

- 缺少環境變數
- 使用者輸入空白
- 模型呼叫失敗

### 預期結果

系統需要顯示清楚錯誤訊息，不應只顯示難懂的 Python Traceback。

---

## AC-010：v0.1 完成定義

當以下條件全部達成，即視為 v0.1 完成：

- [ ] 可從 `.env` 讀取模型設定
- [ ] 可建立 ChatOpenAI model
- [ ] 可建立 ChatPromptTemplate
- [ ] 可建立 StrOutputParser
- [ ] 可組合 LangChain Chain
- [ ] 可從終端機輸入故障描述
- [ ] 可輸出固定格式維修分析
- [ ] 空白輸入會被擋下
- [ ] 缺少環境變數時會顯示清楚錯誤
- [ ] 程式結構已拆成 config.py、chains.py、main.py
- [ ] 根目錄 main.py 只作為 entry point