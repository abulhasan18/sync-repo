import os
import sys
import boto3
import requests

# --- Hardcoded Configuration ---
GITHUB_REPO_OWNER = "abulhasan18"
GITHUB_REPO_NAME = "github-sync-s3"
GITHUB_BRANCH = "main"
S3_BUCKET = "github-sync-s3"
GITHUB_TOKEN = "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"

# Construct GitHub API URL to get the repository tree recursively
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/git/trees/{GITHUB_BRANCH}?recursive=1"
headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
response = requests.get(GITHUB_API_URL, headers=headers)




if response.status_code != 200:
    print(f"❌ Failed to fetch GitHub file list: {response.text}")
    sys.exit(1)

data = response.json()
# Extract the set of file paths (only blobs) from GitHub repository
github_files = {item["path"] for item in data.get("tree", []) if item["type"] == "blob"}

# Initialize the S3 client using the AWS environment credentials
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
