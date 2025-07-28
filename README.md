# Multi-agent system personallized for healthcare support

## Works to do

- [x] Validator agent:
  - [x] Validate user inputs
  - [x] Store user information in memory:
    - Name
    - Age
    - Weight
    - Height
    - Current Living Style
  - [x] Display user information in Vietnamese
- [ ] Task decomposition
- [x] Redirect inputs to appropriatet agent
- [x] Nutrition agent:
  - [x] Web search
  - [x] Calculate health metrics
- [x] Schedule agent:
  - [x] Provide personalized schedule advice based on user underlying condition
  - [ ] Handle scheduling conflicts and suggest alternatives
  - [x] Integrate with calendar APIs for real-time scheduling
  - [ ] Allow users to set reminders for their schedules

## Usage
```bash
chainlit run main.py
```

## Requirements
- Python 3.12+
- Chainlit
- Pydantic AI
- PyPDF
- redis