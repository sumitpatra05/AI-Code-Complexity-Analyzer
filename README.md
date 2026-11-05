
# AI Code Complexity Analyzer

### Analyze. Understand. Optimize.

AI Code Complexity Analyzer is a Python-based code analysis tool designed to evaluate the complexity, maintainability, and quality of Python source code.

It helps developers understand how complex their code is, identify potential performance issues, and discover opportunities for optimization through static analysis and AI-powered code review.

---

## Key Features

- **Cyclomatic Complexity:** Measures the number of independent execution paths in the code.
- **Cognitive Complexity:** Estimates how difficult the code is to understand.
- **Nesting Depth:** Detects deeply nested loops and conditional statements.
- **Big-O Estimation:** Provides heuristic time complexity estimation.
- **Maintainability Index:** Evaluates code maintainability.
- **Refactoring Suggestions:** Provides recommendations to improve code structure.
- **AI-Powered Code Review:** Uses Google Gemini API for additional code analysis and improvement suggestions.
- **Web Interface:** Analyze Python code through a user-friendly web application.
- **CLI Support:** Analyze Python files directly from the terminal.
- **Retry Mechanism:** Handles temporary Gemini API errors with automatic retries.

---

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| AST | Static code analysis |
| Flask | Web application framework |
| HTML & CSS | Frontend interface |
| JavaScript | Frontend interactions |
| Google Gemini API | AI-powered code review |

---

## 📁 Project Structure

```text
AI-Code-Complexity-Analyzer/
│
├── analyzer.py          # Complexity analysis engine
├── ai_review.py         # Gemini AI code review
├── app.py               # Flask web application
├── cli.py               # Command-line interface
├── requirements.txt     # Project dependencies
│
├── templates/
│   └── index.html       # Web interface
│
└── README.md            # Project documentation
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### 2. Navigate to Project Folder

```bash
cd AI-Code-Complexity-Analyzer
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Web Application

Start the Flask application:

```bash
python app.py
```

Open your browser and visit:

http://127.0.0.1:5000

You can now analyze Python code using the web interface.

---

## 💻 Run Using Command Line (CLI)

Analyze a Python file:

```bash
python cli.py yourfile.py
```

Run analysis with AI-powered review:

```bash
python cli.py yourfile.py --ai
```

---

## 🤖 Enable Gemini AI Code Review (Optional)

The project supports Google Gemini API for advanced AI-powered code review.

### Windows PowerShell

```powershell
$env:GEMINI_API_KEY="your_api_key"
$env:GEMINI_MODEL="gemini-3.8-flash"
```

### macOS / Linux

```bash
export GEMINI_API_KEY="your_api_key"
export GEMINI_MODEL="gemini-3.8-flash"
```

**Note:** Replace `your_api_key` with your actual Gemini API key.

The AI review feature is optional. The core static code analysis works independently of the Gemini API.

### API Error Handling

The application includes a retry mechanism for temporary Gemini API errors:

- HTTP 408 – Request Timeout
- HTTP 429 – Too Many Requests
- HTTP 500 – Internal Server Error
- HTTP 502 – Bad Gateway
- HTTP 503 – Service Unavailable
- HTTP 504 – Gateway Timeout

Failed requests are retried up to three times with short backoff delays.

---

## 📊 Analysis Metrics

| Metric | Description |
|---|---|
| Cyclomatic Complexity | Measures independent execution paths |
| Cognitive Complexity | Estimates code understanding difficulty |
| Nesting Depth | Measures nested control structures |
| Time Complexity | Heuristic Big-O estimation |
| Maintainability Index | Estimates maintainability |
| Refactoring Tips | Suggests possible code improvements |

---

## ⚠️ Important Notes

- Big-O estimation is heuristic-based and not a formal mathematical proof.
- Results are generated using AST structure, loop nesting, recursion, and sorting patterns.
- Complex algorithms may require manual time and space complexity verification.
- Gemini AI review is an optional feature and requires a valid API key.
- API availability and usage limits depend on your Gemini account.

---

## 🎯 Project Objectives

1. Understand Python code complexity through static analysis.
2. Identify potentially inefficient code structures.
3. Improve code readability and maintainability.
4. Provide useful refactoring recommendations.
5. Integrate AI-powered code review for deeper insights.

---

## 🔮 Future Enhancements

- Support for Java and C/C++.
- Advanced time and space complexity detection.
- Code visualization and analysis charts.
- Downloadable PDF analysis reports.
- Improved AI-based optimization recommendations.
- GitHub repository integration.

---

## 👨‍💻 Developer

**Sumit Patra**

B.Tech – Computer Science & Engineering

Brainware University

---

## ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.

**Built with Python, Static Analysis, and AI.**
