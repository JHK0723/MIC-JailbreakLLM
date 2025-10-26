 Quick Start Guide - OpenAI Integration

## ✅ What's Been Set Up

1. **OpenAI API Key Configured** - Your API key is in `.env`
2. **Backend Set to OpenAI** - `BACKEND_MODEL=openai` in `.env`
3. **Dependencies Installed** - `openai` package installed

## 🚀 Running the Application

### Step 1: Start the Backend
```bash
cd backend
python app.py
```
Or use uvicorn directly:
```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Start the Frontend (in a new terminal)
```bash
cd streamlit
streamlit run ui.py
```

### Step 3: Access the Application
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000

## 🔄 Switching Between Ollama and OpenAI

Edit `.env` and change:
```env
# For OpenAI (currently set)
BACKEND_MODEL=openai

# For Ollama
BACKEND_MODEL=ollama
```

Then restart the backend.

## 📝 Current Configuration

Your `.env` file has:
- ✅ OpenAI API key configured
- ✅ Model: gpt-3.5-turbo
- ✅ Backend set to OpenAI
- ✅ All level passwords set

## 🧪 Testing the Integration

The application should work the same as before, but now it's using OpenAI instead of Ollama. Try:
1. Starting a session
2. Sending a prompt
3. View the streaming response from OpenAI

## ⚠️ Important Notes

- The `.env` file is NOT committed to git (it's in `.gitignore`)
- Never share your API key publicly
- OpenAI charges per request (but gpt-3.5-turbo is very affordable)
- Make sure you have internet connection for OpenAI to work

## 🐛 Troubleshooting

If you see "OPENAI_API_KEY not found":
1. Make sure `.env` file exists in the project root
2. Restart the backend after any `.env` changes
3. The warning may appear during import tests but won't affect runtime

If backend won't start:
1. Check that port 8000 is available
2. Verify all dependencies: `pip install -r requirements.txt`

## 📊 Model Comparison

| Feature | OpenAI | Ollama |
|---------|--------|--------|
| API Key Required | Yes | No |
| Internet Required | Yes | No |
| Cost | Pay per use | Free |
| Model Options | gpt-3.5-turbo, gpt-4, etc | Local models |
| Performance | High | Medium |
