# MUNvare - Complete MUN Assistant

## 🚀 Get Started in 3 Steps

A comprehensive AI-powered platform for MUN delegates with speech generation, research tools, note-taking with AI analysis, and study guides - all powered by Google Gemini.

### Step 1: Install Dependencies (2-3 minutes)

**Option A: Using install script (Recommended)**
```bash
bash install.sh
```

**Option B: Manual installation**
```bash
# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Add API Key (1 minute)
1. Get a Google Gemini API key:
   - Visit: https://makersuite.google.com/app/apikey
   - Click "Create API Key"
   - Copy your key

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Edit `.env` and paste your API key:
```
GEMINI_API_KEY=your-key-here
```

### Step 3: Launch (1 minute)
```bash
python start.py
```

Browser opens automatically at http://localhost:5000

## ✨ Try These First

1. **Chat**: Click "AI Chat" → Ask "What is MUN?"
2. **Speech**: Click "Speech Generator" → Enter:
   - Country: India
   - Topic: Climate Change
   - Committee: UNEP
   - Click "Generate Speech"
3. **Notes**: Click "My Notes" → Create a new note → Write something → Click "Analyze with AI"

## 📚 Generate Study Guides (Optional but Recommended)

After first launch:
```bash
python backend/generate_premade_notes.py
```

Wait 5-10 minutes. Creates comprehensive study guides from the MUN book.

## 🎯 Features at a Glance

| Feature | What It Does |
|---------|-------------|
| **AI Chat** | Ask anything about MUN - rules, procedures, strategy |
| **Speech Generator** | Create professional MUN speeches for any country/topic |
| **My Notes** | Write research notes, get AI analysis and insights |
| **Study Guides** | Pre-made comprehensive notes on all MUN topics |
| **Research Tools** | Generate POI questions, research foreign policy, suggest modcaucus topics |
| **Speech Rating** | Record and analyze your speeches (coming soon) |
| **Book Search** | Search the entire MUN guidebook instantly |

## 🎨 Dark Minimalistic UI

- **Black background** with subtle accents
- **Clean, thin buttons** for modern look
- **Organized sidebar** navigation
- **Distraction-free** writing experience

## 💡 Pro Tips

- **Save Money**: Use premade notes and search instead of chat when possible
- **Better Speeches**: Research foreign policy first, then generate speech
- **Efficient Research**: Create one master note per committee, analyze it regularly
- **POI Prep**: Generate questions for all major countries beforehand

## ❓ Common Issues

### "Module not found"
```bash
pip install -r requirements.txt
```

### "AI features not working"
- Check `.env` file has valid API key
- Verify you have credit/quota with API provider

### "Port already in use"
```bash
lsof -ti:5000 | xargs kill -9  # Mac/Linux
```

## 🛠️ Troubleshooting

**"API key not found"**
- Check `.env` file exists
- Verify `GEMINI_API_KEY=your-key-here` (no spaces)

**"Module not found"**
```bash
pip install -r requirements.txt
```

**"Port 5000 in use"**
```bash
lsof -ti:5000 | xargs kill -9
```

**Gemini errors**
- Verify API key is valid at https://makersuite.google.com/app/apikey
- Check you haven't exceeded free tier limits (wait 24 hours)

## 💰 Cost Estimate

Google Gemini is **FREE** for moderate usage!

- **Gemini 2.5 Flash Lite**: Free tier with generous limits
- More than enough for daily MUN preparation
- No credit card required!

## 🎯 Core Features

- **AI Chat**: Ask anything about MUN procedures, strategy, rules
- **Speech Generator**: Create professional speeches for any country/topic
- **Smart Notes**: Write research notes and get AI-powered analysis
- **Study Guides**: Pre-made comprehensive notes from the MUN book
- **Research Tools**: Generate POI questions, research foreign policy, suggest modcaucus topics
- **Book Search**: Search the entire MUN guidebook with semantic search
- **Dark Theme**: Beautiful minimalistic black interface

## 📁 Project Structure

```
MUNvare/
├── backend/          # Flask API + AI service
├── frontend/         # HTML/CSS/JS interface
├── data/            # Your notes, speeches (auto-created)
├── MUN Book .txt    # Knowledge base
└── start.py         # Launch script
```

## 🔧 Advanced Usage

### Generate Study Guides
After first launch, create comprehensive study guides:
```bash
python backend/generate_premade_notes.py
```
Takes 5-10 minutes, creates notes on all MUN topics.

### Change UI Theme
Edit `frontend/styles.css`:
```css
:root {
    --accent: #2196F3;  /* Change this color */
}
```

---

**That's it! You're ready to excel at MUN with AI assistance.** 🏆
