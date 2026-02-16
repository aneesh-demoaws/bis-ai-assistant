#!/bin/bash
cd /root/bis-assistant
export AWS_REGION=eu-west-1
export STRANDS_KNOWLEDGE_BASE_ID=MNAX9DFME0
python3 -m uvicorn app:app --host 0.0.0.0 --port 80
