# NoMoreClutter 🗂️✨

An intelligent AI-powered desktop application that automatically organizes your files using local Large Language Models (LLMs). Say goodbye to cluttered folders and let AI analyze, categorize, and rename your files with smart descriptive names!

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-orange.svg)
![OpenAI Compatible](https://img.shields.io/badge/LLM-OpenAI%20API-green.svg)

## 🎯 Features

### Intelligent AI Organization
- **Smart Image Analysis**: Uses computer vision to understand what's in your images (landscapes, people, memes, documents, etc.)
- **AI Validation**: Double-checks folder and filename suggestions to ensure accuracy
- **Descriptive Renaming**: AI generates meaningful filenames based on actual image content (e.g., `sunset_beach.jpg`, `cat_portrait.jpg`)
- **Flexible Categories**: AI creates appropriate folder categories based on content (Nature, People, Memes, Artwork, Screenshots, etc.)

### Powerful File Management
- **Batch Processing**: Process thousands of files efficiently in batches
- **Multiple File Types**: Organize Images, Documents, Videos, Audio, Archives, and Code files
- **Numbered Renaming**: Option to rename files sequentially (1.jpg, 2.jpg, etc.)
- **Non-Destructive**: Files are moved, not copied - saves disk space

### User-Friendly Interface
- **Modern Dark UI**: Built with CustomTkinter for a sleek, modern look
- **Real-Time Progress**: See exactly what's happening as files are processed
- **Detailed Logging**: Every file move is logged to the output area
- **Settings Persistence**: Your preferences are saved automatically

### Privacy & Flexibility
- **Flexible AI Integration**: Works with local servers (Ollama, LM Studio), embedded models, or direct cloud APIs (Groq, Gemini, OpenAI)
- **RLM-Compatible**: Designed for Recursive Language Model decomposition
- **Strict Guidelines**: Governed by automated AI principles ([GUIDELINES.md](GUIDELINES.md))

## 📜 Project Principles & Guidelines
This project adheres to strict architectural and workflow principles:
- **[PRINCIPLE-001: RLM Compatibility](GUIDELINES.md#principle-001-rlm-compatibility-recursive-language-model)**: Hierarchical recursive decomposition for complex directory structures.
- **[PRINCIPLE-002: Automatic Git Workflow](GUIDELINES.md#principle-002-automatic-git-workflow-commit--push)**: AI assistants automatically stage, commit, and push updates.
- **[PRINCIPLE-003: Modularity & Pluggable Architecture](GUIDELINES.md#principle-003-modularity--pluggable-architecture)**: Decoupled AI providers, engines, and UI layers.
- **[PRINCIPLE-004: Living Principles System & Auto-Sync](GUIDELINES.md#principle-004-living-principles-system-extensible-governance--auto-sync)**: Extensible guidelines with automated cross-AI synchronization.
- **[PRINCIPLE-005: AI Cold-Start Readiness & Living README Sync](GUIDELINES.md#principle-005-ai-cold-start-readiness--living-documentation-readme-sync)**: 100% self-describing repository for cold-starting AI agents; mandatory README synchronization after every change.
- **[PRINCIPLE-006: Pre-flight Impact & Quality Checklist](GUIDELINES.md#principle-006-pre-flight-impact--quality-checklist-cold-start-gate)**: Pre-flight checklist assessing motivation, benefits, risks/harm, and quality preservation.

> **Universal AI Support**: These guidelines are automatically synchronized across all AI coding assistants (`AGENTS.md`, `GUIDELINES.md`, `GEMINI.md`, `CLAUDE.md`, `.cursorrules`, `.agents/rules/principles.md`, and `.github/copilot-instructions.md`) via `scripts/sync_principles.py`. Full specification in [GUIDELINES.md](GUIDELINES.md) and [AGENTS.md](AGENTS.md).

## 🚀 Getting Started

### Prerequisites

1. **Python 3.12 or higher**
2. **A local LLM server** (one of):
   - [LM Studio](https://lmstudio.ai/) - Recommended for beginners
   - [Ollama](https://ollama.ai/)
   - Any OpenAI-compatible local server

### Installation

```bash
# Clone or download the project
cd NoMoreClutter

# Install dependencies
pip install -r requirements.txt
```

### Running the App

```bash
python main.py
```

## ⚙️ Configuration

### LLM Setup

1. **Start your local LLM server**:
   - **LM Studio**: Open the app, load a model (recommended: `llama3` or `qwen2.5-vl-7b` for vision), and start the server on port `1234`
   - **Ollama**: Run `ollama serve` (defaults to port `11434`)

2. **Configure in app**:
   - Click the ⚙️ **Settings** button
   - Set the API URL (default: `http://localhost:1234/v1`)
   - Enter your model name (e.g., `llama3`, `qwen2.5-vl-7b-instruct`)
   - Click **Test AI Connection** to verify

### Settings Options

| Setting | Description |
|---------|-------------|
| **Create new folders** | AI creates new categories based on content |
| **Analyze images with AI** | Uses vision AI to understand image content |
| **Numbered renaming** | Rename files as 1.jpg, 2.jpg, etc. |
| **AI rename** | Let AI suggest better filenames |
| **Auto execute** | Move files immediately after analysis |
| **Batch size** | Files processed per AI request (default: 10) |
| **Max files** | Limit total files to process |

## 📁 Project Structure

```
NoMoreClutter/
├── main.py                 # Main application UI and orchestration
├── models/
│   └── __init__.py        # Data models and file type definitions
├── services/
│   ├── __init__.py        # Service factory functions
│   ├── file_scanner.py    # File discovery and filtering
│   ├── llm_service.py     # AI integration and image analysis
│   └── file_executor.py   # File move operations
├── settings.json          # Saved user preferences
└── requirements.txt       # Python dependencies
```

## 🔧 How It Works

### Image Analysis Flow

1. **Initial Scan**: Files are discovered from the source folder
2. **AI Batch Processing**: Images are sent to the local LLM in batches
3. **Content Analysis**: AI looks at each image and determines:
   - What category/folder fits best
   - What descriptive name matches the content
4. **Validation**: AI validates its own suggestions by re-examining the image
5. **Re-analysis** (if needed): If validation fails, AI re-analyzes with different prompts
6. **Execution**: Files are moved to appropriate folders with new names

### Example Results

```
Before                          After
─────────────────────────────   ───────────────────────────
IMG_001.jpg              →      Memes/funny_meme.jpg
screenshot_2024.png     →      Screenshots/desktopCapture.png
DSCN1234.jpg            →      Nature/sunset_beach.jpg
random_file.png         →      Artwork/digital_art.png
```

## 🐛 Troubleshooting

### "Failed to connect to AI"
- Ensure your LLM server (LM Studio/Ollama) is running
- Check the API URL in Settings matches your server
- Verify the model name is correct

### "No files found"
- Select a source folder containing files
- Check that file type categories are selected

### Files not being renamed
- Ensure "Analyze images with AI" is enabled in Settings
- For numbered renaming, enable "Numbered renaming" option

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## 📝 License

MIT License - Feel free to use and modify as needed!

---

Made with ❤️ for cleaner directories everywhere
