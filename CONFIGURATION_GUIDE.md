# Configuration Guide
## How to Update Settings for Your Chatbot
**File Location:** `D:\IT_Support_Chatbot\backend\.env`

---

## 🔑 CRITICAL Settings (Must Update)

### 1. Groq API Key (REQUIRED)

**What it is:** API credentials to use Groq's LLM service for generating answers

**Where to get it:**
1. Go to: https://console.groq.com/keys
2. Sign up or log in with your account
3. Click "Create API Key"
4. Copy the API key

**How to update:**

```
# BEFORE:
GROQ_API_KEY=your_groq_api_key

# AFTER (replace with your actual key):
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Example:**
```
GROQ_API_KEY=gsk_2y9R8mK3pL7nQ2vX5bJ8wZ1cF4tY6dE9
```

---

### 2. Database Connection (REQUIRED if using PostgreSQL)

**What it is:** Connection string to your PostgreSQL database

**Current value:**
```
DATABASE_URL=postgresql://chatbot_user:YourStrongPassword123!@localhost:5432/chatbot
```

**If you're NOT using PostgreSQL:**
- Comment it out or set a dummy value for now
- We'll add support for other databases later

**If you ARE using PostgreSQL, update:**
```
DATABASE_URL=postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME
```

**Example:**
```
DATABASE_URL=postgresql://admin:MyPassword123!@localhost:5432/chatbot_db
```

**Breaking it down:**
- `postgresql://` - Database type
- `admin` - Your PostgreSQL username
- `MyPassword123!` - Your PostgreSQL password
- `localhost` - Server address
- `5432` - Port number
- `chatbot_db` - Database name

---

### 3. JWT Secret (REQUIRED for Production)

**What it is:** Secret key for generating secure authentication tokens

**How to generate a new secret:**

Open PowerShell and run:
```powershell
python -c "import secrets; print('JWT_SECRET=' + secrets.token_hex(32))"
```

**Output will look like:**
```
JWT_SECRET=a7f8c2e9b3d1f4g6h9k2m5p8q1r4s7t0v3w6x9z2c5f8i1l4o7r0t3w6z9c2f5
```

**Update in .env:**
```
JWT_SECRET=a7f8c2e9b3d1f4g6h9k2m5p8q1r4s7t0v3w6x9z2c5f8i1l4o7r0t3w6z9c2f5
```

---

## ⚙️ Important Settings (Should Update)

### 4. CORS Allowed Origins (Restrict Access)

**What it is:** List of websites that can access your chatbot

**Current value:**
```
CORS_ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

**For development (local testing):**
Keep as is - allows localhost:3000 and localhost:5173

**For production (your company):**
```
CORS_ALLOWED_ORIGINS=["https://yourcompany.com","https://intranet.yourcompany.com"]
```

**Example:**
```
CORS_ALLOWED_ORIGINS=["https://company.com","https://support.company.com","https://chat.company.com"]
```

---

### 5. LLM Provider (Can Change)

**What it is:** Which AI service to use for generating answers

**Current:**
```
LLM_PROVIDER=groq
GROQ_MODEL=llama-3.3-70b-versatile
```

**Alternative: Google Gemini**
```
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash
```

**How to get Gemini API key:**
1. Go to: https://makersuite.google.com/app/apikey
2. Create a new API key
3. Copy and paste into `.env`

---

## 📊 Optional Settings (Can Leave as Default)

### 6. Rate Limiting

```
RATE_LIMIT_PER_MINUTE=100      # Max requests per user per minute
RATE_LIMIT_PER_HOUR=1000       # Max requests per user per hour
```

**Change if needed:**
```
RATE_LIMIT_PER_MINUTE=50       # More restrictive
RATE_LIMIT_PER_HOUR=500        # More restrictive
```

---

### 7. Logging Level

```
LOG_LEVEL=INFO      # Normal logging
```

**Options:**
- `DEBUG` - Very detailed (development)
- `INFO` - Normal (default)
- `WARNING` - Only warnings
- `ERROR` - Only errors

**Change to:**
```
LOG_LEVEL=DEBUG     # For debugging issues
LOG_LEVEL=ERROR     # For production to reduce logs
```

---

### 8. Storage Paths

```
CHROMA_DIR=./storage/chromadb   # Where vector database is stored
DOCS_DIR=./storage/docs          # Where uploaded documents are stored
```

**Don't change unless you have a specific reason.**

---

### 9. JWT Token Expiry

```
JWT_EXPIRY_HOURS=24    # Tokens expire after 24 hours
```

**Change if needed:**
```
JWT_EXPIRY_HOURS=1     # Expire after 1 hour (more secure)
JWT_EXPIRY_HOURS=720   # Expire after 30 days (less secure)
```

---

### 10. Embedding Model

```
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

**This creates semantic search vectors. Don't change unless you know what you're doing.**

---

## 🚀 How to Edit the .env File

### Option 1: Using Notepad (Easiest)

1. **Open File Explorer**
2. **Navigate to:** `D:\IT_Support_Chatbot\backend`
3. **Find:** `.env` file
4. **Right-click** → **Open with** → **Notepad**
5. **Edit the values** you need to change
6. **Save** (Ctrl + S)
7. **Restart the app**

### Option 2: Using PowerShell

```powershell
# Open .env in default editor
notepad D:\IT_Support_Chatbot\backend\.env
```

### Option 3: Using VS Code

```powershell
# Open in VS Code
code D:\IT_Support_Chatbot\backend\.env
```

---

## ✅ Complete Setup Checklist

### Minimal Setup (Local Testing)
- [ ] `GROQ_API_KEY` - Required
- [ ] Leave everything else as default
- [ ] Restart app

### Development Setup
- [ ] `GROQ_API_KEY` - Required
- [ ] `JWT_SECRET` - Generate new one
- [ ] `DATABASE_URL` - If using PostgreSQL
- [ ] Restart app

### Production Setup
- [ ] `GROQ_API_KEY` - Set securely
- [ ] `JWT_SECRET` - Generate strong key
- [ ] `DATABASE_URL` - Production database
- [ ] `CORS_ALLOWED_ORIGINS` - Your domains only
- [ ] `APP_ENV=production`
- [ ] `DEBUG=false`
- [ ] `LOG_LEVEL=WARNING`
- [ ] Restart app

---

## 🔄 How to Apply Changes

### After editing .env:

1. **Stop the chatbot** - Press `Ctrl + C` in the terminal

2. **Restart it:**
```powershell
cd D:\IT_Support_Chatbot\backend
.\venv\Scripts\Activate.ps1
python run.py
```

3. **Verify changes were loaded:**
```powershell
# In a new PowerShell window:
curl http://localhost:8001/health
# Should return: {"status":"ok",...}
```

---

## 📋 Example: Complete Configuration

### For Local Development:

```env
# Application Settings
APP_ENV=development
DEBUG=true

# LLM Provider
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_2y9R8mK3pL7nQ2vX5bJ8wZ1cF4tY6dE9
GROQ_MODEL=llama-3.3-70b-versatile

# Storage
CHROMA_DIR=./storage/chromadb
DOCS_DIR=./storage/docs

# Authentication
JWT_SECRET=a7f8c2e9b3d1f4g6h9k2m5p8q1r4s7t0v3w6x9z2c5f8i1l4o7r0t3w6z9c2f5
JWT_EXPIRY_HOURS=24
API_KEY_ROTATION_DAYS=90

# Database
DATABASE_URL=postgresql://chatbot_user:password@localhost:5432/chatbot

# CORS
CORS_ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000

# Logging
LOG_LEVEL=DEBUG
AUDIT_LOG_FILE=./logs/audit.log

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### For Production:

```env
# Application Settings
APP_ENV=production
DEBUG=false

# LLM Provider
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_xxxxxxxxxxxxx  (your actual key)
GROQ_MODEL=llama-3.3-70b-versatile

# Storage
CHROMA_DIR=/data/chromadb  (external storage)
DOCS_DIR=/data/docs

# Authentication
JWT_SECRET=xxxxxxxxxxxxx  (generate with: python -c "import secrets; print(secrets.token_hex(32))")
JWT_EXPIRY_HOURS=1  (shorter expiry)
API_KEY_ROTATION_DAYS=30  (rotate more frequently)

# Database
DATABASE_URL=postgresql://prod_user:strong_password@prod-db.company.com:5432/chatbot_prod

# CORS
CORS_ALLOWED_ORIGINS=["https://company.com","https://support.company.com"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=50  (stricter)
RATE_LIMIT_PER_HOUR=500

# Logging
LOG_LEVEL=WARNING  (less verbose)
AUDIT_LOG_FILE=/var/log/chatbot/audit.log

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

---

## 🆘 Troubleshooting

### "Invalid Groq API Key" error
- Check: Did you copy the full key?
- Check: No extra spaces before/after the key?
- Check: Did you restart the app after changing?

### "Database connection refused"
- Check: PostgreSQL is running
- Check: Username and password are correct
- Check: Database exists
- Check: Port 5432 is open

### "CORS error from browser"
- Check: Your domain is in `CORS_ALLOWED_ORIGINS`
- Check: You're using correct protocol (https vs http)
- Check: You restarted the app

### "JWT Secret too short"
- Generate new one: `python -c "import secrets; print(secrets.token_hex(32))"`
- Must be at least 32 characters

---

## ⏱️ When Changes Take Effect

| Setting | Takes Effect |
|---------|--------------|
| `GROQ_API_KEY` | After restart ✓ |
| `JWT_SECRET` | After restart ✓ |
| `CORS_ALLOWED_ORIGINS` | After restart ✓ |
| `RATE_LIMIT_*` | After restart ✓ |
| `LOG_LEVEL` | After restart ✓ |
| `DATABASE_URL` | After restart ✓ |

**Always restart the app after changing .env values!**

---

## 🔐 Security Tips

1. **Never commit .env to git** (already in .gitignore)
2. **Use strong JWT_SECRET** (32+ characters)
3. **Rotate JWT_SECRET regularly** (every 3-6 months)
4. **Restrict CORS_ALLOWED_ORIGINS** in production
5. **Use HTTPS URLs** in production
6. **Don't share API keys** in chat/email
7. **Rotate GROQ_API_KEY** if compromised

---

**Ready to configure?** Open the `.env` file and update the required settings! 🚀

