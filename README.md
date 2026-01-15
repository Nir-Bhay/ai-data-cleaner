# AI Data Cleaner 🧹✨

A modern, AI-powered data cleaning application with a beautiful glassmorphism UI. Clean messy CSV files using natural language commands!

![AI Data Cleaner](https://img.shields.io/badge/AI-Powered-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-green?style=for-the-badge)
![Flask](https://img.shields.io/badge/Flask-3.0-black?style=for-the-badge)
![Vercel](https://img.shields.io/badge/Deploy-Vercel-black?style=for-the-badge)

## ✨ Features

- 🤖 **AI-Powered Cleaning** - Use natural language to describe what you want to clean
- 🎨 **Modern UI** - Beautiful glassmorphism dark theme with gradient accents
- 💾 **Browser Storage** - Your data stays private in your browser (IndexedDB)
- 📊 **Data Preview** - See stats and preview before cleaning
- 📥 **Multi-Format Export** - Download as CSV or Excel
- 📜 **Cleaning History** - Track all your cleaning operations locally
- ⚡ **Serverless Ready** - Deploys to Vercel with zero configuration

## 🚀 Live Demo

[Try it live on Vercel](https://your-deployment-url.vercel.app) _(coming soon)_

## 🖼️ Screenshots

### Upload Page
![Upload](docs/upload.png)

### Data Preview
![Preview](docs/preview.png)

### Results & Export
![Results](docs/results.png)

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **AI**: Google Gemini API
- **Storage**: IndexedDB (browser-side)
- **Data Processing**: Pandas
- **Deployment**: Vercel

## 📦 Quick Start

### Prerequisites

- Python 3.11+
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-data-cleaner.git
   cd ai-data-cleaner
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   ```
   http://localhost:5000
   ```

## 🌐 Deploy to Vercel

The easiest way to deploy this app:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/ai-data-cleaner)

### Manual Deployment

1. **Fork this repository**

2. **Connect to Vercel**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your forked repository

3. **Add Environment Variable**
   - Go to Project Settings → Environment Variables
   - Add `GEMINI_API_KEY` with your API key

4. **Deploy**
   - Vercel will automatically deploy from your main branch

## 📖 Usage

1. **Upload CSV** - Drag and drop or click to browse
2. **Review Data** - Check stats and preview
3. **Describe Cleaning** - Use natural language like:
   - "Remove duplicate rows"
   - "Fill missing values in Age column with median"
   - "Remove rows where Salary is null"
4. **Clean** - AI processes your request
5. **Export** - Download as CSV or Excel

## 🧠 AI Cleaning Examples

| Command | What it does |
|---------|--------------|
| `Remove duplicate rows` | Deletes exact duplicate entries |
| `Fill missing Age with median` | Imputes missing values |
| `Remove rows with null Salary` | Filters out incomplete data |
| `Standardize date formats` | Normalizes date columns |
| `Convert text to lowercase` | Case normalization |

## 🏗️ Architecture

```
┌─────────────┐
│   Browser   │ ← Stores history & data (IndexedDB)
│  (Frontend) │
└─────┬───────┘
      │
      ├─ Upload CSV
      ├─ Send cleaning prompt
      │
┌─────▼───────┐
│    Flask    │ ← Stateless API
│   Backend   │
└─────┬───────┘
      │
      ├─ Parse with Gemini AI
      ├─ Clean with Pandas
      │
┌─────▼───────┐
│   Return    │ ← Cleaned data as JSON
│  JSON Data  │
└─────────────┘
```

## 📁 Project Structure

```
ai-data-cleaner/
├── app.py                 # Flask application
├── modules/
│   ├── csv_loader.py      # CSV handling
│   ├── rule_parser.py     # AI prompt parsing
│   └── data_cleaner.py    # Data cleaning logic
├── static/
│   ├── css/style.css      # Glassmorphism UI
│   └── js/
│       ├── app.js         # Frontend logic
│       └── storage.js     # IndexedDB manager
├── templates/
│   └── index.html         # Single page app
├── requirements.txt       # Python dependencies
├── vercel.json           # Vercel config
└── README.md
```

## 🔐 Privacy

- **No server storage** - Your data never leaves your browser
- **Temporary processing** - Files deleted after cleaning
- **API calls** - Only prompts sent to Gemini (not your data)

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - feel free to use this project however you'd like!

## 🙏 Acknowledgments

- Google Gemini for AI capabilities
- Pandas for data processing
- Vercel for easy deployment

---

Made with ❤️ using AI and modern web technologies
