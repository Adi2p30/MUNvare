# 🎉 MUNvare - New Features Guide

## What's New?

Your MUNvare platform now has 4 major enhancements:

### 1. ⚙️ Setup Tab - Configuration System
**What it does:** Store your MUN session details so AI knows your context

**How to use:**
1. Click "⚙️ Setup" in sidebar
2. Fill in:
   - Your country, committee, and agenda
   - Add other delegates in your committee
   - Committee information (study guide, deadlines)
3. Click "Save"

**Why it matters:**
- AI automatically knows your country when chatting
- Speech generation is tailored to your specific committee
- Notes are analyzed with your agenda in mind
- Everything is saved across sessions

### 2. 💬 Chat with History & Markdown
**What it does:** Persistent conversations that save automatically

**New features:**
- **Chat History**: All conversations saved and accessible
- **Markdown Support**: AI responses render with formatting
- **Context-Aware**: AI knows your config + notes automatically

**How to use:**
1. Click "AI Chat"
2. See your past conversations in the sidebar
3. Click "+ New" for a new conversation
4. Click any past chat to continue it
5. Chat knows your country, committee, and research notes!

**Markdown features:**
- **Bold** text with `**text**`
- *Italic* with `*text*`
- `Code` with backticks
- Lists (bullet and numbered)
- Code blocks with syntax highlighting

### 3. 📁 Enhanced Notes System
**What it does:** Organize notes in folders with professional templates

**New features:**
- **Folders**: Research, Speeches, POI, Lobbying, Documentation
- **Templates**: 6 pre-made note templates for common MUN tasks
- **Auto-Context**: Your notes automatically used by AI

**How to use:**
1. Click "My Notes"
2. Click "📋 From Template" to see templates:
   - **Country Research**: Structured research template
   - **Speech Draft**: Format for writing speeches
   - **POI Preparation**: Organize POI questions and defenses
   - **Lobbying Strategy**: Plan your lobbying approach
   - **Resolution Draft**: Draft resolutions properly
   - **Committee Session Notes**: Take session notes
3. Or click "+ New Note" for blank note
4. Notes appear in folders automatically
5. AI uses ALL your notes when you chat or generate speeches

### 4. 🧠 Context-Aware AI
**What it does:** AI uses everything you've configured

**AI now automatically knows:**
1. **Your Configuration**
   - Country, committee, agenda
   - Other delegates in committee
2. **All Your Notes**
   - Research, speeches, strategies
   - Automatically included as context
3. **Chat History**
   - Remembers previous conversation
4. **MUN Guidebook**
   - Full knowledge base

**This means:**
- **Smarter Speech Generation**: Uses your research automatically
- **Better Chat**: Knows your specific situation
- **Personalized Advice**: Tailored to your country and committee

## How Everything Works Together

### Example Workflow:

1. **Setup Phase**:
   ```
   Setup Tab → Enter country (India), committee (UNEP), agenda (Climate Change)
   ```

2. **Research Phase**:
   ```
   Notes → From Template → Choose "Country Research"
   Fill in India's climate policy, positions, allies
   ```

3. **Chat Phase**:
   ```
   AI Chat → "What should India's main arguments be on climate finance?"
   AI Response: Uses your notes + config + guidebook to answer
   ```

4. **Speech Writing**:
   ```
   Speech Generator → Enter basic info
   AI automatically uses your research notes to generate speech
   Speech references facts from your notes!
   ```

## Important: Everything is Saved

- ✅ **Configuration**: Saved in `data/config/mun_config.json`
- ✅ **Chats**: Each conversation in `data/chats/`
- ✅ **Notes**: All notes in `data/notes_v2/`
- ✅ **Speeches**: Generated speeches in `data/speeches/`

**Your work persists across sessions!**

## Quick Start Checklist

- [ ] 1. Go to Setup tab
- [ ] 2. Enter your delegate info (country, committee, agenda)
- [ ] 3. Add other delegates if desired
- [ ] 4. Create notes from templates for your research
- [ ] 5. Try chatting - notice AI knows your context
- [ ] 6. Generate a speech - notice it uses your notes

## Tips for Best Results

### Setup:
- Fill in complete delegate info first
- Add major countries as "other delegates" to track them

### Notes:
- Use templates - they're optimized for MUN
- Write comprehensive notes - AI uses them everywhere
- Update notes as you learn more in committee

### Chat:
- Start new chats for different topics
- Reference your notes by mentioning them
- Chat history helps AI remember context

### Speeches:
- Do research in notes FIRST
- Then generate speech - it'll use your research
- Edit the generated speech to add your voice

## Troubleshooting

**Q: AI doesn't seem to know my country**
A: Make sure you saved your info in Setup tab

**Q: Chat history not showing**
A: Check backend is running (`python start.py`)

**Q: Templates not appearing**
A: Refresh page, check backend console for errors

**Q: AI not using my notes**
A: Notes are automatically used - make sure they're saved

## What's Different from Before?

### Before:
- Chat was temporary, no history
- No configuration - had to specify country every time
- Notes were just notes - AI didn't use them
- Speech generation didn't know your research

### Now:
- Chat history saves everything
- Setup tab configures everything once
- Notes automatically used by AI everywhere
- Speech generation includes your research
- Much smarter, personalized experience

## Future Enhancements (Coming Soon)

- Export notes to PDF
- Share configurations between devices
- Collaborative notes
- More templates
- Voice input
- Mobile app

---

**Enjoy your enhanced MUN preparation platform!** 🎯

For issues or questions, check the console (F12) for errors and ensure the backend is running.
