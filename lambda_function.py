import base64
from datetime import datetime
import json
import os
import urllib.error
import urllib.request
import uuid
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("JarvisMemory")
polly = boto3.client("polly")


def ask_cloud_ai(question):
  api_key = os.environ.get("GROQ_API_KEY", "").strip()
  if not api_key:
    return (
        "My cloud AI key is not configured yet, sir. Please add GROQ_API_KEY"
        " in Lambda environment variables."
    )

  base_url = "https://api.groq.com" 
  headers = {
      "Authorization": f"Bearer {api_key}",
      "Content-Type": "application/json",
      "User-Agent": "JarvisCloudBrain/1.0",
  }

  try:
    # Auto-discover an active chat model on your Groq account so 404 never happens
    models_req = urllib.request.Request(
        base_url + "/openai/v1/models", headers=headers
    )
    with urllib.request.urlopen(models_req, timeout=5) as m_resp:
      models_data = json.loads(m_resp.read().decode("utf-8")).get("data", [])
      valid_ids = [
          m["id"]
          for m in models_data
          if "whisper" not in m["id"]
          and "guard" not in m["id"]
          and "tts" not in m["id"]
      ]
      chosen_model = next(
          (
              m
              for m in valid_ids
              if "qwen" in m or "llama" in m or "gemma" in m or "gpt-oss" in m
          ),
          valid_ids if valid_ids else "openai/gpt-oss-120b",
      )

    payload = {
        "model": chosen_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are JARVIS, a crisp British AI assistant. Answer in 2"
                    " short, clear spoken sentences without markdown, bullet"
                    " points, or special symbols."
                ),
            },
            {"role": "user", "content": question},
        ],
        "max_tokens": 300,
        "temperature": 0.5,
    }

    req = urllib.request.Request(
        base_url + "/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
      result = json.loads(resp.read().decode("utf-8"))
      msg = result["choices"].pop(0)["message"]

      return (msg.get("content") or msg.get("reasoning_content") or "").strip()
  except urllib.error.HTTPError as e:
    err_body = e.read().decode("utf-8", errors="ignore")
    print(f"Groq HTTP {e.code}: {err_body}")
    return f"Groq error {e.code}: {err_body[:90]}"
  except Exception as e:
    print("AI Error:", str(e))
    return f"AI connection error: {str(e)}"


def lambda_handler(event, context):
  try:
    raw_body = event.get("body") or "{}"
    body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
    action = body.get("action", "speak")
    content = body.get("content", "")

    if action == "save_note":
      table.put_item(
          Item={
              "NoteID": str(uuid.uuid4())[:8],
              "Content": content,
              "Timestamp": datetime.utcnow().isoformat(),
          }
      )
      reply_text = f"Note saved to DynamoDB, sir: {content}"

    elif action == "read_notes":
      response = table.scan(Limit=5)
      items = response.get("Items", [])
      if not items:
        reply_text = "You have no saved notes in DynamoDB, sir."
      else:
        notes_list = ". ".join([item["Content"] for item in items])
        reply_text = f"Here are your recent notes, sir: {notes_list}"

    elif action == "ask_ai":
      reply_text = ask_cloud_ai(content)
      if not reply_text:
        reply_text = "I could not generate an answer for that right now, sir."

    else:
      reply_text = content

    polly_response = polly.synthesize_speech(
        Text=reply_text, OutputFormat="mp3", VoiceId="Arthur", Engine="neural"
    )
    audio_base64 = base64.b64encode(
        polly_response["AudioStream"].read()
    ).decode("utf-8")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"reply": reply_text, "audio_base64": audio_base64}),
    }

  except Exception as e:
    print("Lambda Error:", str(e))
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"reply": f"AWS Lambda Error: {str(e)}"}),
    }
