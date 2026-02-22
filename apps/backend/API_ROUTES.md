# BrainTrain API Routes & cURL Examples

Base URL: `http://localhost:3000` (assuming default port)
Most endpoints require a JWT token returned from login/register. Replace `<YOUR_JWT_TOKEN>` with your actual token.

---

## 1. Identity & Auth (Public)

### Register a new user
```bash
curl -X POST http://localhost:3000/identity/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Password123"
  }'
```

### Login
```bash
curl -X POST http://localhost:3000/identity/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Password123"
  }'
```

### Request OTP
```bash
curl -X POST http://localhost:3000/identity/request-otp \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "test@example.com"
  }'
```

### Verify OTP
```bash
curl -X POST http://localhost:3000/identity/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "test@example.com",
    "code": "123456"
  }'
```

### Google OAuth Login
```bash
curl -X POST http://localhost:3000/identity/google \
  -H "Content-Type: application/json" \
  -d '{
    "token": "google_id_token_here"
  }'
```

---

## 2. Profile & Skills (Protected)

### Get My Profile
```bash
curl -X GET http://localhost:3000/identity/me \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

### Update Profile
```bash
curl -X PUT http://localhost:3000/identity/me \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "displayName": "John Doe",
    "bio": "Software Engineer",
    "avatarUrl": "https://example.com/avatar.jpg"
  }'
```

### List Global Skill Tags
```bash
curl -X GET http://localhost:3000/identity/skill-tags \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

### Add/Update Skill Preference
```bash
curl -X POST http://localhost:3000/identity/me/skills \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "skillTagId": "<SKILL_TAG_ID>",
    "level": "INTERMEDIATE"
  }'
```

### Remove Skill Preference
```bash
curl -X DELETE http://localhost:3000/identity/me/skills/<SKILL_TAG_ID> \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

---

## 3. Topics (Protected)

### Create a Topic
```bash
curl -X POST http://localhost:3000/topics \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "React Hooks",
    "parentTopicId": null
  }'
```

### List Topics (Global + Your Own)
```bash
curl -X GET http://localhost:3000/topics \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

### Get Topic by ID
```bash
curl -X GET http://localhost:3000/topics/<TOPIC_ID> \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

### Delete a Topic
```bash
curl -X DELETE http://localhost:3000/topics/<TOPIC_ID> \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

---

## 4. Question Bank (Protected)

### Create a Question in the Bank
```bash
curl -X POST http://localhost:3000/question-bank \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Tell me about a time you had to deal with a severe production outage.",
    "topicId": "<TOPIC_ID>",
    "difficulty": "ADVANCED",
    "questionType": "behavioral",
    "isGlobal": false
  }'
```

### List Bank Questions
```bash
curl -X GET "http://localhost:3000/question-bank?topicId=<TOPIC_ID>&difficulty=ADVANCED" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

### Get Bank Question by ID
```bash
curl -X GET http://localhost:3000/question-bank/<QUESTION_BANK_ID> \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

---

## 5. Interview Sessions (Protected)

### Create a Session
```bash
curl -X POST http://localhost:3000/sessions \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "topicId": "<TOPIC_ID>",
    "mode": "ONE_ON_ONE_AI",
    "interviewLevel": "SCREENING",
    "difficulty": "INTERMEDIATE",
    "adaptive": true,
    "durationMinutes": 30
  }'
```

### List Your Sessions
```bash
curl -X GET "http://localhost:3000/sessions?page=1&limit=10&status=COMPLETED" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

### Get Session by ID
```bash
curl -X GET http://localhost:3000/sessions/<SESSION_ID> \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

### Start Session
```bash
curl -X PUT http://localhost:3000/sessions/<SESSION_ID>/start \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

### Complete Session
```bash
curl -X PUT http://localhost:3000/sessions/<SESSION_ID>/complete \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

---

## 6. Questions & Responses (Protected)

### Generate Next Question
```bash
curl -X POST http://localhost:3000/sessions/<SESSION_ID>/questions/next \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

### Submit a Response
```bash
curl -X POST http://localhost:3000/questions/<QUESTION_ID>/responses \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "answerText": "I approached this by first checking the logs, identifying the memory leak, and rolling back the deployment.",
    "responseTimeMs": 35000,
    "thinkingTimeMs": 5000
  }'
```

---

## 7. Evaluation (Protected)

### Analyze Completed Session
```bash
curl -X POST http://localhost:3000/sessions/<SESSION_ID>/evaluation/analyze \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

### Get Session Evaluation Report
```bash
curl -X GET http://localhost:3000/sessions/<SESSION_ID>/evaluation \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

---

## 8. Analytics (Protected)

### Get Cross-Session Analytics
```bash
curl -X GET http://localhost:3000/analytics/me \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```
