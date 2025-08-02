# Narrative Strategy Integration Guide

This document explains how the narrative strategy data structure integrates with CV and cover letter generation flows.

## Overview

The narrative strategy serves as the strategic foundation for all application materials. It contains:
- **Strategic decisions**: Which experiences to highlight and why
- **Tactical content**: Specific stories, messages, and narrative arc
- **Integration hooks**: Clear mapping to document sections

## Data Structure Components

### 1. Must-Tell Experiences (2-3)
**Purpose**: The most critical experiences that directly demonstrate fit for the role

**Integration**:
- CV: Featured prominently in experience section with expanded bullet points
- Cover Letter: Forms the core evidence in the value proposition section
- Key points become achievement bullets in CV

### 2. Differentiators (1-2)
**Purpose**: Unique value propositions that set the candidate apart

**Integration**:
- CV: Highlighted in professional summary
- Cover Letter: Woven throughout, especially in cultural fit section
- Used to craft unique positioning statement

### 3. Career Arc
**Purpose**: Three-phase narrative showing progression and future vision

**Components**:
- `past`: Foundation and growth story
- `present`: Current expertise and impact
- `future`: Vision for target role (must mention company)

**Integration**:
- Cover Letter Opening: Uses present + future to create compelling hook
- CV Summary: Incorporates all three phases concisely
- Interview: Ready-made answer for "walk me through your background"

### 4. Key Messages (exactly 3)
**Purpose**: Core themes to reinforce throughout all materials

**Integration**:
- CV: Each message supported by 2-3 bullet points across experiences
- Cover Letter: One message per main paragraph
- Consistency: Same messages across all touchpoints

### 5. Evidence Stories (0-2)
**Purpose**: Detailed CAR format stories for behavioral evidence

**Format**:
- Challenge: Problem/situation (50-500 chars)
- Action: Specific steps taken (50-500 chars)
- Result: Quantified outcomes (50-500 chars)
- Skills Demonstrated: 1-5 relevant skills

**Integration**:
- Cover Letter: Primary evidence in value proposition section
- CV: Results extracted as achievement bullets
- Interview: Pre-prepared STAR stories

## Cover Letter Mapping

The 5-paragraph cover letter structure maps directly to narrative strategy:

### Opening Paragraph
- Draws from `career_arc.present` and `career_arc.future`
- Incorporates first `key_message`
- Mentions target company from `career_arc.future`

### Value Proposition Paragraph
- Features `must_tell_experiences[0]` as primary evidence
- Highlights first `differentiator`
- Uses metrics from experience `key_points`

### Evidence Paragraph
- Uses `evidence_stories[0]` if available
- Otherwise uses `must_tell_experiences[1]`
- Demonstrates specific skills from requirements

### Cultural Fit Paragraph
- References `career_arc.future` vision
- Incorporates second `differentiator` for unique perspective
- Shows company research alignment

### Closing Paragraph
- Reinforces all three `key_messages`
- Restates commitment from `career_arc.future`
- Call to action

## CV Generation Mapping

### Professional Summary Section
- Combines all three `key_messages` into 3-4 lines
- Highlights both `differentiators`
- Incorporates `career_arc` progression

### Experience Section Prioritization
1. Current role (if in `must_tell_experiences`)
2. Other `must_tell_experiences` in order
3. Remaining experiences by recency

### Achievement Bullets
- `must_tell_experiences`: Use all `key_points` as bullets
- `evidence_stories`: Extract quantified results
- Other experiences: 2-3 most relevant achievements

### Skills Section
- Extracted from `evidence_stories.skills_demonstrated`
- Cross-referenced with job requirements
- Organized by category (technical, leadership, etc.)

## Validation Requirements

For successful generation, the narrative strategy must have:

1. **Minimum Content**:
   - At least 2 must-tell experiences
   - At least 1 differentiator
   - Complete career arc (all 3 phases)
   - Exactly 3 key messages
   - At least 1 evidence story OR detailed must-tell experiences

2. **Content Quality**:
   - Experiences with clear relevance reasons
   - Quantified results where possible
   - Future vision mentioning target company
   - CAR stories with sufficient detail (50+ chars each)

3. **Consistency**:
   - Key messages supported by experiences
   - Skills in stories match job requirements
   - Career arc aligns with target role

## Usage in Generation Nodes

### CVGenerationNode
```python
def generate_cv(narrative_strategy, career_db, requirements):
    # 1. Extract professional summary from key_messages + differentiators
    # 2. Prioritize experiences based on must_tell_experiences
    # 3. Generate bullets from key_points and evidence_stories
    # 4. Ensure all key_messages are supported
```

### CoverLetterNode
```python
def generate_cover_letter(narrative_strategy, requirements, company_research):
    # 1. Opening from career_arc.present + future
    # 2. Value prop from must_tell_experiences[0]
    # 3. Evidence from evidence_stories[0] or must_tell_experiences[1]
    # 4. Cultural fit from differentiators + career_arc.future
    # 5. Closing reinforces key_messages
```

## Best Practices

1. **Coherence**: Ensure all components tell a consistent story
2. **Specificity**: Use concrete examples and metrics
3. **Relevance**: Every element should support the target role
4. **Uniqueness**: Differentiators should be genuinely distinctive
5. **Completeness**: Provide all required fields for smooth generation

## Example Integration Flow

1. User provides job description and career database
2. ExperiencePrioritizationNode ranks all experiences
3. NarrativeStrategyNode synthesizes the strategy
4. User reviews/edits narrative strategy via checkpoint
5. CVGenerationNode uses strategy to create tailored CV
6. CoverLetterNode uses strategy to write compelling letter
7. All materials share consistent messaging and stories