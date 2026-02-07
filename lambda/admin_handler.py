import json
import os
import hashlib
import base64
import hmac
import time
import boto3

S3_BUCKET = os.environ["S3_BUCKET"]
KB_ID = os.environ["KB_ID"]
DS_ID = os.environ["DS_ID"]
ADMIN_USER = os.environ["ADMIN_USER"]
ADMIN_PASS_HASH = os.environ["ADMIN_PASS_HASH"]
TOKEN_SECRET = os.environ["TOKEN_SECRET"]
REGION = os.environ.get("AWS_REGION", "eu-west-1")

s3 = boto3.client("s3", region_name=REGION)
bedrock = boto3.client("bedrock-agent", region_name=REGION)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": os.environ.get("ALLOWED_ORIGIN", "https://bisai.demoaws.com"),
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
}


def response(status, body):
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body)}


def make_token(username):
    exp = int(time.time()) + 3600
    payload = f"{username}:{exp}"
    sig = hmac.new(TOKEN_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.b64encode(f"{payload}:{sig}".encode()).decode()


def verify_token(token):
    try:
        decoded = base64.b64decode(token).decode()
        username, exp, sig = decoded.rsplit(":", 2)
        if int(exp) < time.time():
            return None
        expected = hmac.new(TOKEN_SECRET.encode(), f"{username}:{exp}".encode(), hashlib.sha256).hexdigest()
        return username if hmac.compare_digest(sig, expected) else None
    except Exception:
        return None


def handler(event, context):
    rc = event.get("requestContext", {})
    method = event.get("httpMethod") or rc.get("http", {}).get("method", "")
    path = event.get("rawPath") or event.get("path", "")

    if method == "OPTIONS":
        return response(200, {"ok": True})

    if path.endswith("/login") and method == "POST":
        return handle_login(event)

    headers = event.get("headers", {})
    auth = headers.get("authorization", headers.get("Authorization", ""))
    token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""
    if not verify_token(token):
        return response(401, {"error": "Unauthorized"})

    if path.endswith("/upload") and method == "POST":
        return handle_upload(event)
    elif path.endswith("/documents") and method == "GET":
        return handle_list()
    elif path.endswith("/documents") and method == "DELETE":
        return handle_delete(event)
    elif path.endswith("/sync") and method == "POST":
        return handle_sync()
    elif path.endswith("/sync") and method == "GET":
        return handle_sync_status()
    return response(404, {"error": "Not found"})


def handle_login(event):
    body = json.loads(event.get("body", "{}"))
    username = body.get("username", "")
    password = body.get("password", "")
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    if username == ADMIN_USER and hmac.compare_digest(pw_hash, ADMIN_PASS_HASH):
        return response(200, {"token": make_token(username)})
    return response(401, {"error": "Invalid credentials"})


def handle_upload(event):
    try:
        body = json.loads(event.get("body", "{}"))
        filename = body["filename"]
        content_b64 = body["content"]
        content = base64.b64decode(content_b64)
        s3.put_object(Bucket=S3_BUCKET, Key=filename, Body=content)
        sync = bedrock.start_ingestion_job(knowledgeBaseId=KB_ID, dataSourceId=DS_ID)
        job_id = sync["ingestionJob"]["ingestionJobId"]
        return response(200, {"message": f"Uploaded {filename}", "ingestionJobId": job_id})
    except Exception as e:
        return response(500, {"error": str(e)})


def handle_list():
    try:
        objs = s3.list_objects_v2(Bucket=S3_BUCKET)
        files = []
        for obj in objs.get("Contents", []):
            files.append({"key": obj["Key"], "size": obj["Size"], "lastModified": obj["LastModified"].isoformat()})
        return response(200, {"files": files})
    except Exception as e:
        return response(500, {"error": str(e)})


def handle_delete(event):
    try:
        body = json.loads(event.get("body", "{}"))
        key = body["key"]
        s3.delete_object(Bucket=S3_BUCKET, Key=key)
        sync = bedrock.start_ingestion_job(knowledgeBaseId=KB_ID, dataSourceId=DS_ID)
        job_id = sync["ingestionJob"]["ingestionJobId"]
        return response(200, {"message": f"Deleted {key}", "ingestionJobId": job_id})
    except Exception as e:
        return response(500, {"error": str(e)})


def handle_sync():
    try:
        sync = bedrock.start_ingestion_job(knowledgeBaseId=KB_ID, dataSourceId=DS_ID)
        job_id = sync["ingestionJob"]["ingestionJobId"]
        return response(200, {"ingestionJobId": job_id})
    except Exception as e:
        return response(500, {"error": str(e)})


def handle_sync_status():
    try:
        jobs = bedrock.list_ingestion_jobs(knowledgeBaseId=KB_ID, dataSourceId=DS_ID, maxResults=5)
        result = []
        for job in jobs.get("ingestionJobSummaries", []):
            result.append({
                "ingestionJobId": job["ingestionJobId"],
                "status": job["status"],
                "startedAt": job.get("startedAt", "").isoformat() if job.get("startedAt") else "",
                "updatedAt": job.get("updatedAt", "").isoformat() if job.get("updatedAt") else "",
            })
        return response(200, {"jobs": result})
    except Exception as e:
        return response(500, {"error": str(e)})
