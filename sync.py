import os
import sys
import boto3
import requests

# --- Load Configuration ---
GITHUB_REPO_OWNER = "abulhasan18"
GITHUB_REPO_NAME = "s3-sync"  # Fixed repository name
GITHUB_BRANCH = "main"
S3_BUCKET = "github-sync-s3"

# Retrieve GitHub Token from environment variable
github_token = os.getenv("GITHUB_TOKEN")

if not github_token:
    print("❌ Error: GitHub token is missing. Make sure you have set TOKEN_SECRET in GitHub secrets or environment variables.")
    sys.exit(1)
else:
    print("✅ GitHub token is available in sync.py")

# --- Fetch the correct SHA of the main branch ---
BRANCH_API_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/branches/{GITHUB_BRANCH}"
headers = {"Authorization": f"Bearer {github_token}", "Accept": "application/vnd.github.v3+json"}

branch_response = requests.get(BRANCH_API_URL, headers=headers)
if branch_response.status_code != 200:
    print(f"❌ Failed to fetch branch details: {branch_response.text}")
    sys.exit(1)

branch_data = branch_response.json()
tree_sha = branch_data["commit"]["commit"]["tree"]["sha"]

# --- Fetch Repository Tree ---
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/git/trees/{tree_sha}?recursive=1"
response = requests.get(GITHUB_API_URL, headers=headers)

if response.status_code != 200:
    print(f"❌ Failed to fetch GitHub file list: {response.text}")
    sys.exit(1)

data = response.json()
github_files = {item["path"] for item in data.get("tree", []) if item["type"] == "blob"}

# --- Initialize S3 Client ---
s3_client = boto3.client("s3")

# Retrieve current files in S3
s3_files = set()
paginator = s3_client.get_paginator("list_objects_v2")
for page in paginator.paginate(Bucket=S3_BUCKET):
    for obj in page.get("Contents", []):
        s3_files.add(obj["Key"])

# --- Sync Process ---
# Upload files that are in GitHub but not in S3
for file_path in github_files - s3_files:
    print(f"📂 Uploading {file_path} to S3...")
    raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}/{file_path}"
    file_response = requests.get(raw_url)
    if file_response.status_code == 200:
        s3_client.put_object(Bucket=S3_BUCKET, Key=file_path, Body=file_response.content)
    else:
        print(f"❌ Failed to fetch {file_path} from GitHub.")

# Delete files that exist in S3 but not in GitHub
for file_path in s3_files - github_files:
    print(f"🗑️ Deleting {file_path} from S3...")
    s3_client.delete_object(Bucket=S3_BUCKET, Key=file_path)

print("✅ Sync Complete!")





# github token
# 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
