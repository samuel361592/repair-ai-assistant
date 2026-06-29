# LangChain 維修問題分析助手 v0.1

這是一個以 LangChain LCEL 實作的命令列助手。使用者輸入設備或維修異常後，程式會固定從問題摘要、可能原因、初步檢查方向、需要補問的資訊及建議處理優先順序五個部分回覆。

目前版本只提供單次文字分析，不包含 RAG、Agent、Tool Calling 或 LangGraph。

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
冰箱運轉時有異音，而且冷藏室溫度降不下來。
```

## 測試

測試使用 Python 內建的 `unittest`，不會連線或呼叫實際模型 API：

```powershell
uv run python -m unittest discover -s tests -v
```
