## 🕸️ Web Application Fingerprinting Tool

A **modular Python-based tool** that performs **web technology fingerprinting** using the **BuiltWith API**, analyzes results using a **local LLM (Ollama)**, and exports structured reports to **Excel** for security assessments.

It’s designed for **bug bounty hunters, red teamers, and security analysts** who want actionable insights into a target’s technology stack.

---

### 🔧 Tools & Technologies

| Tool / Library        | Purpose                                                                                |
| --------------------- | -------------------------------------------------------------------------------------- |
| **BuiltWith API**     | Identifies frameworks, CMS, hosting, analytics, and server technologies.               |
| **Ollama (LLM)**      | Performs local AI analysis of BuiltWith data to identify risks or outdated components. |
| **pandas / openpyxl** | Organizes and exports results into structured Excel reports.                           |
| **python-dotenv**     | Handles environment variables securely.                                                |
| **argparse**          | Adds CLI functionality for user-friendly execution.                                    |
| **Python 3.11+**      | Core runtime for the entire tool.                                                      |

---

### 🧰 Step 1: Environment Setup

**Task:**
Create a Python environment and install dependencies.

**Commands:**

```bash
# Create a virtual environment
python -m venv web_fingerprint_env

# Activate the environment
# On Windows:
web_fingerprint_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Expected Outcome:**
A virtual environment with all dependencies required for API integration, JSON parsing, and Excel export.

---

### 🔑 Step 2: Configure BuiltWith API Key

**Task:**
Generate and securely store your BuiltWith API key.

**Instructions:**

1. Sign up at [BuiltWith.com](https://builtwith.com/) and generate your API key.
2. Create a file named `config.py` in the project root:

   ```python
   BUILTWITH_API_KEY = "your_api_key_here"
   ```
3. *(Optional)* You can also store it in a `.env` file:

   ```bash
   BUILTWITH_API_KEY=your_api_key_here
   ```

**Expected Outcome:**
Your API credentials are securely configured and ready for authentication.

---

### 🌐 Step 3: Perform Fingerprinting via BuiltWith API

**File:** `builtwith_client.py`

**Description:**
This script queries the BuiltWith API to retrieve the target domain’s technology stack.

**Prompt Example:**

```bash
python builtwith_client.py example.com
```

**Expected Outcome:**
A formatted JSON response showing the domain’s detected technologies, categories, and hosting data.

---

### 🧠 Step 4: Analyze Fingerprint Results with Ollama

**File:** `builtwith_ollama.py`

**Description:**
Uses a local LLM (e.g., `llama3`, `tinyllama`) through **Ollama** to analyze the BuiltWith results.

**Example Prompt:**

```bash
Analyze the following BuiltWith result and provide insights:
{builtwith_result}
```

**Expected Outcome:**
AI-generated insights highlighting risks, outdated software, or potential misconfigurations.

---

### 📊 Step 5: Generate Excel Report of Findings

**File:** `builtwith_excel.py`

**Description:**
Converts the fingerprinting and AI analysis into an Excel report using `pandas` and `openpyxl`.

**Report Columns:**

* Category
* Subcategory
* Live Count
* Dead Count
* Latest Timestamp
* Oldest Timestamp
* Latest_Time
* Oldest_Time

**Expected Outcome:**
A structured Excel report for each scanned domain.

---

### 🧩 Step 6: Orchestrate with `main.py`

**File:** `main.py`

**Description:**
The central script that integrates all modules — from BuiltWith query to AI analysis and Excel export.

**Command to Run:**

```bash
python main.py example.com --excel
```

**Workflow:**

1. Calls the BuiltWith API
2. Runs Ollama for analysis
3. Exports results to Excel (if `--excel` flag is included)

**Expected Outcome:**
A single command that performs full-stack fingerprinting and generates both human-readable and report-ready results.

---

### 🧠 Example Output

```
🔍 Target: example.com
----------------------------------------
Detected Technologies: WordPress, Nginx, Google Analytics
AI Analysis (Ollama):
- WordPress version outdated → possible plugin vulnerabilities
- Missing HTTPS redirection detected
✅ Report saved to: reports/example_com_fingerprint.xlsx
```

---

### 📦 Project Structure

```
web_fingerprint-project/
│
├── builtwith_client.py
├── builtwith_excel.py
├── builtwith_ollama.py
├── config.py
├── main.py
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
```

---

### 🛡️ Security Notes

* **Never** commit your `.env` file or API keys to GitHub.
* Use `.gitignore` to keep sensitive files private.
* Make sure your Ollama models run locally and securely.

---

### 🤝 Contributions

Feel free to fork the repository, improve functionality, and submit a pull request.
Bug reports and feature requests are welcome!

---

### 📜 License

This project is open source and available under the **MIT License**.

