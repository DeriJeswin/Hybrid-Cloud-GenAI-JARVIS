# 🤖 Hybrid Cloud & GenAI JARVIS Desktop Assistant

A voice-activated Windows desktop assistant built on a **Hybrid Edge + Cloud Serverless Architecture**. It routes instant OS automation, hardware telemetry, and network diagnostics locally on Windows while offloading Generative AI reasoning, neural speech synthesis, and persistent memory to **AWS Serverless** services.

---

## 🏗️ System Architecture

```text
[Windows Desktop Agent (Python + Tkinter HUD)]
       │
       ├──► Local Edge Execution (45+ OS Shortcuts, System Telemetry, Calculators, Timers)
       │
       └──► HTTPS POST ──► [Amazon API Gateway]
                                  │
                                  ▼
                         [AWS Lambda (Python 3.12)]
                           ├──► Groq LLM API (Dynamic Model Discovery)
                           ├──► Amazon DynamoDB (Persistent Cloud Notes)
                           └──► Amazon Polly (Neural British Voice TTS)
```

---

## ✨ Key Features

- **Live Floating Telemetry HUD**: Custom frameless `Tkinter` overlay featuring a 32-bar animated audio waveform, real-time CPU/RAM/Battery metrics, and a clickable microphone mute toggle (`LIVE` / `MUTED`).
- **Hybrid Intent Routing**: Executes 45+ local Windows commands (app launching, media control, Brave YouTube routing, Chrome search, voice math, screenshots) in milliseconds while routing open-ended technical and general queries to the Cloud LLM.
- **Dynamic LLM Model Discovery**: Automatically queries Groq's `/openai/v1/models` endpoint inside AWS Lambda to select active chat models with zero hardcoded deprecations.
- **Persistent Cloud Memory & Neural TTS**: Saves and retrieves voice-dictated notes in **Amazon DynamoDB** and synthesizes natural British responses (`Arthur` Neural) via **Amazon Polly**.
- **Production Secret Management**: Zero hardcoded credentials—API keys are stored encrypted in **AWS Lambda Environment Variables** with least-privilege **IAM execution roles**.

---

## 🛠️ Tech Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Cloud & Serverless** | AWS Lambda, Amazon API Gateway, Amazon DynamoDB, Amazon Polly, AWS IAM, Amazon CloudWatch |
| **AI & Speech** | Groq LLM API, Amazon Polly Neural TTS, Google SpeechRecognition |
| **Local Edge Client** | Python 3, Tkinter, `psutil`, `pyautogui`, `requests`, `playsound` |

---

## 📁 Repository Structure

```text
Hybrid-Cloud-GenAI-JARVIS/
├── jarvis_cloud.py       # Local Windows voice client, command router & Tkinter HUD
├── lambda_function.py    # AWS Lambda serverless backend (Groq AI, DynamoDB & Polly)
├── requirements.txt      # Python dependencies for the local desktop agent
└── README.md             # Project documentation & architecture overview
```

---

## 🚀 Setup & Deployment Guide

### 1. Deploy the AWS Serverless Backend
1. **Amazon DynamoDB**: Create a table named `JarvisMemory` with Partition key `NoteID` (`String`).
2. **AWS IAM**: Create an execution role (`JarvisLambdaRole`) with permissions for `AmazonDynamoDBFullAccess` (or table-scoped read/write), `AmazonPollyFullAccess`, and `AWSLambdaBasicExecutionRole`.
3. **AWS Lambda**: Create a Python 3.12 function named `JarvisCloudBrain`, paste the code from `lambda_function.py`, set timeout to `15 seconds`, and deploy.
4. **Environment Variables**: Under **Configuration → Environment variables**, add:
   - `GROQ_API_KEY` = `your_groq_api_key`
5. **Amazon API Gateway**: Create an HTTP or REST API `POST` endpoint wired to `JarvisCloudBrain`.

### 2. Run the Local Windows Desktop Agent
1. Install the required Python libraries:
   ```bash
   pip install -r requirements.txt
   ```
2. Set your API Gateway endpoint URL as an environment variable:
   ```cmd
   set AWS_JARVIS_URL=https://amazonaws.com
   ```
3. Launch JARVIS:
   ```cmd
   python jarvis_cloud.py
   ```

---

## 🎙️ Example Voice Commands

- **Cloud GenAI Brain**: *"Jarvis, what is the difference between a router and a switch?"*
- **DynamoDB Cloud Notes**: *"Jarvis, save note revise BGP path attributes"* / *"Jarvis, read my notes"*
- **System & Hardware Telemetry**: *"Jarvis, check battery"* / *"Jarvis, system status"*
- **Smart Calculations**: *"Jarvis, calculate 24 times 11"*
- **App & Browser Automation**: *"Jarvis, open WhatsApp"* / *"Jarvis, search Google about AWS VPC"* / *"Jarvis, play [song] on YouTube"*

---

## 👨‍💻 Author

**Deri Jeswin**  
B.E. Computer Science & Engineering (2026) | Cloud & Network Engineering Enthusiast  
- GitHub: https://github.com/DeriJeswin
