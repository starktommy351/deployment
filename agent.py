"""
GitHub + Vercel Deploy Agent
============================
এই agent স্বয়ংক্রিয়ভাবে:
1. Project files তৈরি করে
2. package-lock.json generate করে
3. GitHub-এ push করে
4. Vercel-এ deploy করে
"""

import subprocess
import sys
import os
import json
import urllib.request
import urllib.error
from pathlib import Path

# ═══════════════════════════════════════════
# কনফিগারেশন — এখানে তোমার তথ্য দাও
# ═══════════════════════════════════════════
CONFIG = {
    "github_token": "তোমার_github_token",      # GitHub → Settings → Developer Settings → Personal Access Token
    "github_username": "starktommy351",          # তোমার GitHub username
    "repo_name": "newsmain",                     # যে repo-তে push করবে
    "vercel_token": "তোমার_vercel_token",        # Vercel → Settings → Tokens
    "project_folder": "./autoposter-final",      # তোমার project folder
}

# ═══════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════
def log(msg, emoji="→"):
    print(f"\n{emoji} {msg}")

def success(msg):
    print(f"  ✅ {msg}")

def error(msg):
    print(f"  ❌ {msg}")
    sys.exit(1)

def run(cmd, cwd=None, check=True):
    """Command চালাও"""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True
    )
    if check and result.returncode != 0:
        error(f"Command failed: {cmd}\n{result.stderr}")
    return result

def api_call(url, method="GET", data=None, token=None, token_type="Bearer"):
    """API call করো"""
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    if token:
        req.add_header("Authorization", f"{token_type} {token}")
    
    body = json.dumps(data).encode() if data else None
    
    try:
        with urllib.request.urlopen(req, body) as res:
            return json.loads(res.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            err_data = json.loads(body)
            return {"error": err_data}
        except:
            return {"error": body}

# ═══════════════════════════════════════════
# ধাপ ১: Node.js ও npm চেক করো
# ═══════════════════════════════════════════
def check_requirements():
    log("Node.js ও npm চেক করা হচ্ছে...", "🔍")
    
    node = run("node --version", check=False)
    npm = run("npm --version", check=False)
    git = run("git --version", check=False)
    
    if node.returncode != 0:
        error("Node.js নেই! https://nodejs.org থেকে install করো")
    if npm.returncode != 0:
        error("npm নেই! Node.js আবার install করো")
    if git.returncode != 0:
        error("Git নেই! https://git-scm.com থেকে install করো")
    
    success(f"Node.js: {node.stdout.strip()}")
    success(f"npm: {npm.stdout.strip()}")
    success(f"Git: {git.stdout.strip().split()[2]}")

# ═══════════════════════════════════════════
# ধাপ ২: package-lock.json তৈরি করো
# ═══════════════════════════════════════════
def generate_lock_file():
    log("package-lock.json তৈরি হচ্ছে...", "📦")
    
    folder = CONFIG["project_folder"]
    
    if not Path(f"{folder}/package.json").exists():
        error(f"package.json নেই! {folder} folder চেক করো")
    
    # node_modules থাকলে মুছো
    run(f"rm -rf node_modules", cwd=folder, check=False)
    
    # npm install চালাও
    result = run("npm install --legacy-peer-deps", cwd=folder, check=False)
    
    if result.returncode != 0:
        # আবার চেষ্টা করো force দিয়ে
        result = run("npm install --force", cwd=folder, check=False)
        if result.returncode != 0:
            error(f"npm install failed:\n{result.stderr}")
    
    if Path(f"{folder}/package-lock.json").exists():
        success("package-lock.json তৈরি হয়েছে!")
    else:
        error("package-lock.json তৈরি হয়নি")

# ═══════════════════════════════════════════
# ধাপ ৩: GitHub-এ push করো
# ═══════════════════════════════════════════
def push_to_github():
    log("GitHub-এ push করা হচ্ছে...", "🐙")
    
    folder = CONFIG["project_folder"]
    username = CONFIG["github_username"]
    token = CONFIG["github_token"]
    repo = CONFIG["repo_name"]
    
    # Git config
    run(f'git config user.email "agent@auto.com"', cwd=folder, check=False)
    run(f'git config user.name "Deploy Agent"', cwd=folder, check=False)
    
    # .gitignore চেক
    gitignore = Path(f"{folder}/.gitignore")
    if gitignore.exists():
        content = gitignore.read_text()
        if "node_modules" not in content:
            gitignore.write_text(content + "\nnode_modules\n.next\n")
    else:
        gitignore.write_text("node_modules\n.next\n.env\n.env.local\n")
    
    # GitHub repo আছে কিনা চেক করো
    repo_check = api_call(
        f"https://api.github.com/repos/{username}/{repo}",
        token=token,
        token_type="token"
    )
    
    if "error" in repo_check or repo_check.get("message") == "Not Found":
        # Repo তৈরি করো
        log(f"GitHub repo '{repo}' তৈরি হচ্ছে...", "🆕")
        create_result = api_call(
            "https://api.github.com/user/repos",
            method="POST",
            data={"name": repo, "private": True, "auto_init": False},
            token=token,
            token_type="token"
        )
        if "error" in create_result:
            error(f"Repo তৈরি ব্যর্থ: {create_result}")
        success(f"Repo তৈরি হয়েছে: {repo}")
    else:
        success(f"Repo পাওয়া গেছে: {repo}")
    
    # Remote URL সেট করো
    remote_url = f"https://{token}@github.com/{username}/{repo}.git"
    
    # Git init ও push
    cmds = [
        "git init",
        "git checkout -B main",
        "git add .",
        'git commit -m "auto deploy by agent" --allow-empty',
        f"git remote remove origin",
        f"git remote add origin {remote_url}",
        "git push -u origin main --force",
    ]
    
    for cmd in cmds:
        result = run(cmd, cwd=folder, check=False)
        if result.returncode != 0 and "remote remove" not in cmd:
            if "nothing to commit" not in result.stdout:
                log(f"Warning: {cmd}", "⚠️")
    
    success(f"GitHub push সম্পন্ন! https://github.com/{username}/{repo}")

# ═══════════════════════════════════════════
# ধাপ ৪: Vercel-এ deploy করো
# ═══════════════════════════════════════════
def deploy_to_vercel():
    log("Vercel-এ deploy হচ্ছে...", "🚀")
    
    token = CONFIG["vercel_token"]
    username = CONFIG["github_username"]
    repo = CONFIG["repo_name"]
    
    # Vercel user info নাও
    user_info = api_call("https://api.vercel.com/v2/user", token=token)
    if "error" in user_info:
        error(f"Vercel token সমস্যা: {user_info}")
    
    team_id = user_info.get("user", {}).get("defaultTeamId", None)
    
    # GitHub integration চেক
    deploy_url = "https://api.vercel.com/v13/deployments"
    if team_id:
        deploy_url += f"?teamId={team_id}"
    
    deploy_data = {
        "name": repo,
        "gitSource": {
            "type": "github",
            "repoId": None,  # Vercel নিজে খুঁজে নেবে
            "ref": "main",
            "repo": f"{username}/{repo}",
        },
        "projectSettings": {
            "framework": "nextjs",
            "buildCommand": None,
            "outputDirectory": None,
            "installCommand": "npm install --legacy-peer-deps",
        },
    }
    
    result = api_call(deploy_url, method="POST", data=deploy_data, token=token)
    
    if "error" in result or result.get("error"):
        # Vercel CLI দিয়ে চেষ্টা করো
        log("Vercel CLI দিয়ে deploy করা হচ্ছে...", "🔄")
        vercel_cli_deploy()
    else:
        deploy_id = result.get("id", "")
        success(f"Deploy শুরু হয়েছে! ID: {deploy_id}")
        if result.get("url"):
            success(f"URL: https://{result['url']}")

def vercel_cli_deploy():
    """Vercel CLI দিয়ে deploy"""
    folder = CONFIG["project_folder"]
    token = CONFIG["vercel_token"]
    
    # Vercel CLI আছে কিনা চেক
    check = run("vercel --version", check=False)
    
    if check.returncode != 0:
        log("Vercel CLI install হচ্ছে...", "📥")
        run("npm install -g vercel", check=False)
    
    # Deploy করো
    result = run(
        f'vercel --token {token} --yes --prod',
        cwd=folder,
        check=False
    )
    
    if result.returncode == 0:
        success("Vercel deploy সম্পন্ন!")
        print(result.stdout)
    else:
        error(f"Vercel deploy ব্যর্থ:\n{result.stderr}\n\nম্যানুয়ালি করো:\ncd {folder}\nvercel --prod")

# ═══════════════════════════════════════════
# মূল Agent চালাও
# ═══════════════════════════════════════════
def main():
    print("=" * 50)
    print("  🤖 GitHub + Vercel Deploy Agent")
    print("=" * 50)
    
    # Config চেক
    if "তোমার_github_token" in CONFIG["github_token"]:
        print("\n⚠️  agent.py ফাইলে CONFIG সেকশনে তোমার token দাও!")
        print("\nCONFIG = {")
        print('    "github_token": "ghp_xxxxxxxxxxxx",')
        print('    "github_username": "তোমার_username",')
        print('    "repo_name": "newsmain",')
        print('    "vercel_token": "xxxxxxxxxxxxxxxx",')
        print('    "project_folder": "./autoposter-final",')
        print("}")
        sys.exit(1)
    
    try:
        check_requirements()   # ধাপ ১
        generate_lock_file()   # ধাপ ২
        push_to_github()       # ধাপ ৩
        deploy_to_vercel()     # ধাপ ৪
        
        print("\n" + "=" * 50)
        print("  ✅ সব কাজ সম্পন্ন!")
        print(f"  🌐 https://github.com/{CONFIG['github_username']}/{CONFIG['repo_name']}")
        print("=" * 50)
        
    except SystemExit:
        print("\n❌ Agent বন্ধ হয়ে গেছে। উপরের error ঠিক করো।")
        sys.exit(1)

if __name__ == "__main__":
    main()
