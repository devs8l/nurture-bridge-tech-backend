# Intake Module API Documentation

This document describes the intake module endpoints and how to use them.

## Overview

The intake module manages the intake forms for children. It consists of:
- **Sections**: Logical groupings of questions (e.g., "Birth History", "Medical History")
- **Questions**: Individual questions within sections
- **Responses**: A child's intake session (can be in-progress or completed)
- **Answers**: Individual answers to questions within a response

## Database Schema

The intake data is stored in the `intake` schema with the following tables:
- `sections` - Form sections
- `questions` - Questions within sections
- `responses` - Intake sessions for children
- `answers` - Answers to questions

## API Endpoints

Base path: `/api/v1/intake`

### Section Management

#### Create Section (Admin/HOD only)
```http
POST /api/v1/intake/sections
Content-Type: application/json

{
  "title": "Birth History",
  "description": "Questions about the child's birth and early development",
  "order_number": 1,
  "is_active": true
}
```

#### Get All Sections
```http
GET /api/v1/intake/sections?active_only=true
```

#### Get Section with Questions
```http
GET /api/v1/intake/sections/{section_id}
```

#### Update Section (Admin/HOD only)
```http
PATCH /api/v1/intake/sections/{section_id}
Content-Type: application/json

{
  "title": "Updated Birth History",
  "order_number": 2
}
```

#### Delete Section (Admin/HOD only)
```http
DELETE /api/v1/intake/sections/{section_id}
```
Note: This soft deletes by setting `is_active=false`

### Question Management

#### Create Question (Admin/HOD only)
```http
POST /api/v1/intake/questions
Content-Type: application/json

{
  "section_id": "uuid-here",
  "text": "What was the child's birth weight?",
  "question_type": "TEXT",
  "options": null,
  "is_scorable": false,
  "scoring_logic": null,
  "order_number": 1
}
```

Question types can be: TEXT, RADIO, CHECKBOX, SELECT, TEXTAREA, etc.

Example with options (for RADIO/CHECKBOX):
```json
{
  "section_id": "uuid-here",
  "text": "Was the delivery normal?",
  "question_type": "RADIO",
  "options": {
    "choices": ["Yes", "No", "Complicated"]
  },
  "is_scorable": true,
  "scoring_logic": {
    "Yes": 0,
    "No": 1,
    "Complicated": 2
  },
  "order_number": 2
}
```

#### Get Questions by Section
```http
GET /api/v1/intake/sections/{section_id}/questions
```

#### Get Single Question
```http
GET /api/v1/intake/questions/{question_id}
```

#### Update Question (Admin/HOD only)
```http
PATCH /api/v1/intake/questions/{question_id}
Content-Type: application/json

{
  "text": "Updated question text",
  "order_number": 3
}
```

#### Delete Question (Admin/HOD only)
```http
DELETE /api/v1/intake/questions/{question_id}
```
Note: This is a hard delete

### Intake Response (Form Submission)

#### Create Intake Response
```http
POST /api/v1/intake/responses
Content-Type: application/json

{
  "child_id": "uuid-here"
}
```
Creates a new intake session for a child. Only one in-progress response allowed per child.

#### Get Response with Answers
```http
GET /api/v1/intake/responses/{response_id}
```

#### Get All Responses for a Child
```http
GET /api/v1/intake/children/{child_id}/responses
```

#### Update Response Status
```http
PATCH /api/v1/intake/responses/{response_id}
Content-Type: application/json

{
  "status": "COMPLETED",
  "completed_at": "2025-12-22T10:00:00Z"
}
```
Status can be: `IN_PROGRESS` or `COMPLETED`

### Answer Management

#### Save Single Answer
```http
POST /api/v1/intake/responses/{response_id}/answers
Content-Type: application/json

{
  "question_id": "uuid-here",
  "raw_answer": "3.5 kg",
  "answer_bucket": "normal",
  "score": 0
}
```
This endpoint upserts - if an answer already exists for this question, it updates it.

#### Save Multiple Answers (Bulk)
```http
POST /api/v1/intake/responses/{response_id}/answers/bulk
Content-Type: application/json

[
  {
    "question_id": "uuid-1",
    "raw_answer": "3.5 kg",
    "answer_bucket": "normal",
    "score": 0
  },
  {
    "question_id": "uuid-2",
    "raw_answer": "Yes",
    "answer_bucket": "normal_delivery",
    "score": 0
  }
]
```

#### Get All Answers for a Response
```http
GET /api/v1/intake/responses/{response_id}/answers
```

### Utility Endpoints

#### Get Complete Form Structure
```http
GET /api/v1/intake/form-structure
```
Returns all active sections with their questions. Useful for rendering the entire form.

## Typical Workflow

### 1. Admin/HOD Sets Up Form (One-time)

1. Create sections:
```bash
POST /api/v1/intake/sections
{
  "title": "Birth History",
  "description": "Questions about birth",
  "order_number": 1
}
```

2. Create questions for each section:
```bash
POST /api/v1/intake/questions
{
  "section_id": "section-uuid",
  "text": "Birth weight?",
  "question_type": "TEXT",
  "order_number": 1
}
```

### 2. Parent/Doctor Fills Out Intake (Per Child)

1. Get form structure:
```bash
GET /api/v1/intake/form-structure
```

2. Create intake response:
```bash
POST /api/v1/intake/responses
{
  "child_id": "child-uuid"
}
```

3. Save answers as user fills out form:
```bash
POST /api/v1/intake/responses/{response_id}/answers
{
  "question_id": "q1-uuid",
  "raw_answer": "3.5 kg"
}
```

Or save multiple answers at once:
```bash
POST /api/v1/intake/responses/{response_id}/answers/bulk
[...]
```

4. Mark as completed:
```bash
PATCH /api/v1/intake/responses/{response_id}
{
  "status": "COMPLETED"
}
```

### 3. View Completed Intake

```bash
GET /api/v1/intake/responses/{response_id}
```
or
```bash
GET /api/v1/intake/children/{child_id}/responses
```

## Permissions

- **Section/Question CRUD**: ADMIN, HOD only
- **View Structure**: All authenticated users
- **Create/Update Responses**: DOCTOR, PARENT, RECEPTIONIST
- **View Responses**: DOCTOR, PARENT, RECEPTIONIST, HOD

## Features

1. **Resumable Forms**: Intake responses can be saved as IN_PROGRESS and completed later
2. **Mutable Answers**: Unlike assessments, intake answers can be updated
3. **Flexible Question Types**: Support for TEXT, RADIO, CHECKBOX, SELECT, etc.
4. **Scoring Support**: Optional scoring logic for questions
5. **Bulk Operations**: Save multiple answers at once for better performance
6. **Form Structure**: Get complete form structure in one API call
7. **Child History**: View all intake responses for a child

## Example: Complete Form Setup

```python
# 1. Create section
section_response = await client.post("/api/v1/intake/sections", json={
    "title": "Medical History",
    "description": "Child's medical background",
    "order_number": 1
})
section_id = section_response.json()["id"]

# 2. Create questions
questions = [
    {
        "section_id": section_id,
        "text": "Does the child have any allergies?",
        "question_type": "RADIO",
        "options": {"choices": ["Yes", "No"]},
        "order_number": 1
    },
    {
        "section_id": section_id,
        "text": "If yes, please list the allergies",
        "question_type": "TEXTAREA",
        "order_number": 2
    }
]

for q in questions:
    await client.post("/api/v1/intake/questions", json=q)

# 3. Create intake response
response = await client.post("/api/v1/intake/responses", json={
    "child_id": child_id
})
response_id = response.json()["id"]

# 4. Save answers
answers = [
    {
        "question_id": "q1-uuid",
        "raw_answer": "Yes"
    },
    {
        "question_id": "q2-uuid",
        "raw_answer": "Peanuts, shellfish"
    }
]

await client.post(
    f"/api/v1/intake/responses/{response_id}/answers/bulk",
    json=answers
)

# 5. Complete intake
await client.patch(
    f"/api/v1/intake/responses/{response_id}",
    json={"status": "COMPLETED"}
)
```

## Database Relationships

```
Tenant
  └─ Child
      └─ IntakeResponse (many)
          └─ IntakeAnswer (many)
              └─ IntakeQuestion
                  └─ IntakeSection

IntakeSection
  └─ IntakeQuestion (many)
```
