---
name: meeting-analyzer
description: Analyze meeting transcripts for insights, action items, decisions
---

# Meeting Analyzer Skill

## Overview

Анализ транскриптов встреч: извлечение решений, action items, ключевых моментов.

## When to Use

- Обработка записей встреч
- Извлечение action items
- Анализ принятых решений
- Создание meeting notes
- Выявление паттернов коммуникации

## Meeting Analysis Framework

### 1. Extract Key Elements

```markdown
## Meeting Analysis Template

### Basic Info
- **Date:** [Date]
- **Duration:** [Duration]
- **Participants:** [List]
- **Meeting Type:** [Standup/Planning/Review/etc.]

### Decisions Made
1. [Decision 1]
2. [Decision 2]

### Action Items
| Task | Owner | Deadline | Priority |
|------|-------|----------|----------|
| [Task] | [Name] | [Date] | [H/M/L] |

### Key Discussion Points
- [Topic 1]: [Summary]
- [Topic 2]: [Summary]

### Open Questions
- [Question 1]
- [Question 2]

### Next Steps
1. [Step 1]
2. [Step 2]
```

## Extraction Patterns

### Action Item Detection

```python
import re

ACTION_PATTERNS = [
    r"(I|we|you|he|she|they)\s+will\s+(.+)",
    r"(I|we|you|he|she|they)\s+need to\s+(.+)",
    r"action item[:\s]+(.+)",
    r"todo[:\s]+(.+)",
    r"let'?s\s+(.+)",
    r"can you\s+(.+)\??",
    r"please\s+(.+)",
    r"@(\w+)\s+(.+)",  # @mentions
]

def extract_action_items(transcript: str) -> list:
    """Extract action items from meeting transcript"""
    actions = []

    for pattern in ACTION_PATTERNS:
        matches = re.findall(pattern, transcript, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                actions.append(" ".join(match))
            else:
                actions.append(match)

    return actions
```

### Decision Detection

```python
DECISION_PATTERNS = [
    r"we decided to\s+(.+)",
    r"decision[:\s]+(.+)",
    r"we agreed (that|to)\s+(.+)",
    r"the plan is to\s+(.+)",
    r"we'll go with\s+(.+)",
    r"let's do\s+(.+)",
    r"approved[:\s]+(.+)",
]

def extract_decisions(transcript: str) -> list:
    """Extract decisions from transcript"""
    decisions = []

    for pattern in DECISION_PATTERNS:
        matches = re.findall(pattern, transcript, re.IGNORECASE)
        decisions.extend(matches)

    return decisions
```

### Participant Analysis

```python
from collections import Counter

def analyze_participation(transcript_with_speakers: list) -> dict:
    """
    Analyze speaker participation
    Input: [{"speaker": "John", "text": "..."}, ...]
    """
    # Count speaking turns
    speaker_turns = Counter(entry["speaker"] for entry in transcript_with_speakers)

    # Count words per speaker
    speaker_words = {}
    for entry in transcript_with_speakers:
        speaker = entry["speaker"]
        word_count = len(entry["text"].split())
        speaker_words[speaker] = speaker_words.get(speaker, 0) + word_count

    # Calculate talk time percentage
    total_words = sum(speaker_words.values())
    participation = {
        speaker: {
            "turns": speaker_turns[speaker],
            "words": words,
            "percentage": round(words / total_words * 100, 1)
        }
        for speaker, words in speaker_words.items()
    }

    return participation
```

## AI-Powered Analysis

### With Claude/GPT

```python
def analyze_meeting_with_ai(transcript: str) -> dict:
    """Comprehensive meeting analysis using LLM"""

    prompt = f"""Analyze this meeting transcript and extract:

1. **Summary** (2-3 sentences)
2. **Key Decisions** (bullet list)
3. **Action Items** with owners and deadlines (table format)
4. **Topics Discussed** (brief summary of each)
5. **Risks/Blockers** mentioned
6. **Sentiment** (overall meeting tone)
7. **Follow-up Questions** (unresolved issues)

Transcript:
{transcript}

Provide structured JSON output.
"""

    # Call your LLM API here
    response = call_llm(prompt)
    return parse_json(response)
```

### Sentiment Analysis

```python
def analyze_meeting_sentiment(transcript: str) -> dict:
    """Analyze overall meeting sentiment"""

    prompt = """Analyze the sentiment of this meeting:

1. Overall tone: [Positive/Neutral/Negative]
2. Energy level: [High/Medium/Low]
3. Collaboration: [Excellent/Good/Needs Improvement]
4. Tension points: [List any conflicts or disagreements]
5. Enthusiasm about decisions: [High/Medium/Low]

Provide scores 1-10 for each category.
"""

    return call_llm(prompt + transcript)
```

## Report Templates

### Executive Summary

```markdown
# Meeting Summary
**Date:** [Date] | **Duration:** [Duration]

## TL;DR
[One paragraph executive summary]

## Key Decisions
1. ✅ [Decision 1]
2. ✅ [Decision 2]

## Critical Action Items
| Priority | Task | Owner | Due |
|----------|------|-------|-----|
| 🔴 High | [Task] | @name | [Date] |
| 🟡 Med | [Task] | @name | [Date] |

## Blockers/Risks
- ⚠️ [Blocker 1]
- ⚠️ [Blocker 2]

## Next Meeting
[Date/Time] - [Agenda]
```

### Detailed Notes

```markdown
# [Meeting Title] - [Date]

## Attendees
- [Name 1] (Role)
- [Name 2] (Role)
- Absent: [Name 3]

## Agenda vs Actual
| Planned | Covered | Time |
|---------|---------|------|
| Topic A | ✅ | 15m |
| Topic B | ✅ | 20m |
| Topic C | ❌ (postponed) | - |

## Discussion Summary

### Topic A: [Title]
**Context:** [Background]
**Discussion:** [Key points]
**Decision:** [What was decided]
**Action:** [What needs to be done]

### Topic B: [Title]
...

## Parking Lot
Items to discuss later:
- [ ] [Item 1]
- [ ] [Item 2]

## Action Items

### Immediate (This Week)
- [ ] @john: [Task] - by [Date]
- [ ] @jane: [Task] - by [Date]

### Short-term (This Sprint)
- [ ] @team: [Task] - by [Date]

## Open Questions
1. [Question requiring follow-up]
2. [Unresolved issue]

## Next Steps
1. [Step 1]
2. [Step 2]
3. Schedule follow-up: [Topic]
```

## Automation

### Post-Meeting Workflow

```python
def process_meeting_recording(audio_path: str) -> dict:
    """Full meeting processing pipeline"""

    # 1. Transcribe audio
    transcript = transcribe_audio(audio_path)  # Deepgram/Whisper

    # 2. Identify speakers (diarization)
    speakers_transcript = diarize_speakers(transcript)

    # 3. Extract structured data
    analysis = analyze_meeting_with_ai(speakers_transcript)

    # 4. Generate report
    report = generate_meeting_report(analysis)

    # 5. Create action items in task system
    for action in analysis['action_items']:
        create_task(
            title=action['task'],
            assignee=action['owner'],
            due_date=action['deadline']
        )

    # 6. Send summary to participants
    send_summary_email(analysis['participants'], report)

    return analysis
```

### Integration with Calendar

```python
def schedule_follow_ups(action_items: list, participants: list):
    """Create calendar events for action items"""

    for item in action_items:
        if item.get('requires_meeting'):
            create_calendar_event(
                title=f"Follow-up: {item['task']}",
                attendees=[item['owner']],
                date=item['deadline'],
                description=item['context']
            )
```

## Metrics & Insights

### Meeting Effectiveness Score

```python
def calculate_meeting_effectiveness(analysis: dict) -> dict:
    """Score meeting effectiveness"""

    scores = {
        "decisions_made": min(len(analysis['decisions']) * 20, 100),
        "action_items_assigned": min(len(analysis['action_items']) * 15, 100),
        "time_efficiency": analysis.get('on_time_percentage', 50),
        "participation_balance": calculate_participation_balance(analysis),
        "follow_up_clarity": 100 if analysis['next_steps'] else 0
    }

    overall = sum(scores.values()) / len(scores)

    return {
        "scores": scores,
        "overall": round(overall, 1),
        "grade": "A" if overall >= 80 else "B" if overall >= 60 else "C"
    }
```

### Historical Analysis

```python
def analyze_meeting_trends(meetings: list) -> dict:
    """Analyze patterns across multiple meetings"""

    return {
        "avg_duration": calculate_avg_duration(meetings),
        "avg_action_items": calculate_avg_actions(meetings),
        "completion_rate": calculate_action_completion(meetings),
        "most_active_participants": top_participants(meetings),
        "recurring_topics": extract_common_topics(meetings),
        "decision_velocity": decisions_per_meeting(meetings)
    }
```

## Tips

1. **Записывай** - всегда записывай встречи (с согласия)
2. **Структура** - используй agenda template
3. **Time-box** - ограничивай время обсуждения
4. **Assign owners** - каждый action item = владелец
5. **Follow up** - отслеживай выполнение
6. **Automate** - автоматизируй рутину
7. **Review** - периодически анализируй эффективность
