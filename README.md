# CWVisualization

> Project to conduct statistical analysis with CW experiment log

## Table Structure

### 1. Session Table
- **Granularity:** one row per session
- **Description:** stores session-level metadata extracted from each raw CW log

**Columns**
- `participantId`
- `taskId`
- `sessionId`
- `tabId`
- `startTime`
- `endTime`
- `startedUrl`
- `endedUrl`
- `userAgent`
- `eventCount`

---

### 2. Event Table
- **Granularity:** one row per event
- **Description:** stores detailed interaction events extracted from the nested `events` array

**Main Columns**
- `index`
- `type`
- `timestamp`
- `elapsedMs`
- `delay`
- `url`
- `title`
- `viewportWidth`
- `viewportHeight`
- `scrollX`
- `scrollY`
- `x`, `y`, `pageX`, `pageY`
- `button`
- `tagName`
- `id`
- `className`
- `text`
- `selector`
- `href`
- `participantId`
- `taskId`

---

### Relationship
- One session table row can be linked to many event table rows
- The tables can be joined using `participantId` and `taskId`