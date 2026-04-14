# 🤖 GitHub + Vercel Deploy Agent

এই agent স্বয়ংক্রিয়ভাবে তোমার project GitHub-এ push করে Vercel-এ deploy করে।

## ব্যবহার করার আগে

### ১. GitHub Token পাবে কোথায়?
1. github.com → Settings → Developer Settings
2. Personal Access Tokens → Tokens (classic)
3. Generate new token → সব repo permission দাও
4. Token copy করো (ghp_xxx...)

### ২. Vercel Token পাবে কোথায়?
1. vercel.com → Settings → Tokens
2. Create Token → copy করো

### ৩. agent.py খোলো → CONFIG সেট করো
```python
CONFIG = {
    "github_token": "ghp_তোমার_token",
    "github_username": "starktommy351",
    "repo_name": "newsmain",
    "vercel_token": "তোমার_vercel_token",
    "project_folder": "./autoposter-final",
}
```

## চালাও

```bash
python agent.py
```

## Agent কী কী করে?

1. ✅ Node.js, npm, Git চেক করে
2. ✅ npm install করে package-lock.json তৈরি করে
3. ✅ GitHub repo তৈরি করে (না থাকলে)
4. ✅ সব files push করে
5. ✅ Vercel-এ deploy করে
