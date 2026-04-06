# 🌱 XiaoLu - Your AI Companion

> "Not just listening, but remembering. Not just comforting, but witnessing. Not just being there, but pushing you forward."

An AI companion that remembers you, accompanies your growth, and witnesses your changes.

## ✨ Core Features

### 🧠 Memory & Companionship
- Long-term memory of important events
- Automatic extraction of key information from conversations
- Proactive care and regular check-ins

### 👁️ Growth Witness
- **Lookback System**: "I remember you mentioned this three weeks ago..."
- **Witness Report**: Clearly points out your changes and progress
- **Stuck Point Analysis**: Identifies recurring concerns

### 💬 Speech Coach (嘴替)
- Don't know how to talk to your boss? XiaoLu teaches you
- Interpersonal skills, leadership communication, social ice-breaking
- Negotiation and persuasion techniques

### 🤖 AI Learning Guide
- Learn AI by applying it to YOUR industry
- Not learning AI for the sake of it
- AI as a tool to reduce your workload, not add to it

### 🎯 Growth Mentor (Hidden Teacher)
- Break long-term goals into 30-day micro-tasks
- One small step per day, no anxiety
- Build confidence through daily progress

### 🖼️ Image Recognition
- Send images, XiaoLu analyzes them
- Screenshots, photos, chat records

### 🛠️ Skill Center
- Natural language installation/uninstallation of skills
- Weather, news, code assistant, writing assistant, etc.

### 📊 Web Visualization
- Memory timeline
- Topic statistics
- Emotion change charts
- Weekly/monthly reviews

## 🚀 Quick Start

### 1. Clone the Project

```bash
git clone https://github.com/huangmumu-3/xiaolu.git
cd xiaolu
```

### 2. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env and add your DeepSeek API Key
```

### 4. Run

```bash
# Web service (recommended)
python3 web_server.py

# Or terminal mode
python3 main.py
```

### 5. Access

- **Local**: http://localhost:8080/chat
- **WeChat**: Scan QR code to access

## 📁 Project Structure

```
xiaolu/
├── core/                    # Core modules
│   ├── engine.py            # Conversation engine
│   ├── memory.py            # Memory extraction
│   ├── witness.py           # Witness system
│   ├── lookback.py          # Lookback system
│   ├── growth.py            # Growth mentor
│   ├── guidance.py          # Guidance system
│   ├── coach.py             # Speech coach
│   ├── graph.py             # Neo4j graph database
│   └── database.py          # SQLite database
├── templates/               # Web templates
├── data/                   # Data storage
├── web_server.py           # Flask web service
├── main.py                 # Terminal entry
└── requirements.txt       # Dependencies
```

## 🔧 Configuration

Configure in `.env`:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
PROACTIVE_ENABLED=true
PORT=8080
```

## 🛠️ Available Skills

| Skill | Description |
|-------|-------------|
| 🖼️ Image Analysis | Analyze image content |
| 💬 Speech Coach | Learn how to communicate |
| 🤖 AI Coach | Learn to use AI |
| 🌤️ Weather Query | Weather forecast |
| 📰 News Summary | Daily news briefing |
| 💻 Code Assistant | Write code, debug |
| ✍️ Writing Assistant | Write articles, emails |

## 💡 Usage Tips

### Speech Coach
Just describe your difficulty:
- "I don't know how to ask my boss for a raise"
- "My colleague keeps taking credit for my work"
- "How to politely decline someone's request"

### Goal Setting
Say your goal naturally:
- "I want to learn English"
- "I want to start exercising"
- "I want to read more books"

XiaoLu will break it into 30-day micro-tasks!

### AI Application
Tell your industry:
- "I'm a teacher, how can I use AI?"
- "I'm in marketing, what AI tools should I use?"

XiaoLu will recommend tools for YOUR specific situation.

### Witness Function
- `/witness` - View growth witness report
- `/stuck` - View stuck point analysis
- `/lookback` - Review past topics

## 📝 Feedback & Suggestions

Submit feedback through the 💌 Feedback Box in the web interface to help improve XiaoLu!

## 📄 License

MIT License

---

*Built with ❤️ using DeepSeek API*
