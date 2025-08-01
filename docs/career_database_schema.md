# Career Database YAML Schema

This document defines the schema for career database YAML files used by the Career Application Agent.

## Overview

The career database represents the ground truth of an applicant's professional history. It contains comprehensive information about experience, skills, education, projects, and achievements that can be selectively used to tailor job applications.

## Schema Structure

### Root Level

The career database is a YAML file with the following top-level sections:

```yaml
personal_info:    # Personal and contact information
experience:       # Professional work experience (list)
education:        # Educational background (list)
skills:           # Technical and soft skills
projects:         # Notable projects (list)
certifications:   # Professional certifications (list)
publications:     # Publications and articles (list)
awards:           # Awards and recognition (list)
```

### personal_info (Required)

Personal and contact information.

```yaml
personal_info:
  name: string              # Required: Full name
  email: string             # Required: Email address
  phone: string             # Optional: Phone number
  location: string          # Optional: City, State/Country
  linkedin: string          # Optional: LinkedIn profile URL
  github: string            # Optional: GitHub profile URL
  website: string           # Optional: Personal website URL
```

### experience (Required)

List of professional experiences, ordered from most recent to oldest.

```yaml
experience:
  - title: string           # Required: Job title
    company: string         # Required: Company name
    duration: string        # Required: Time period (e.g., "2020-Present", "Jan 2019 - Dec 2020")
    location: string        # Optional: Office location
    description: string     # Required: Role description
    achievements:           # Required: List of quantified achievements
      - string
    technologies:           # Optional: Technologies used
      - string
    team_size: number       # Optional: Size of team managed/worked with
    reason_for_leaving: string  # Optional: Why you left this position
    company_culture_pros:   # Optional: Positive aspects of company culture
      - string
    company_culture_cons:   # Optional: Challenging aspects of company culture
      - string
    projects:               # Optional: Notable projects during this role
      - title: string       # Required: Project title/name
        description: string # Required: Detailed project description including technologies used
        achievements:       # Required: Results and impact (KPIs improved, metrics achieved)
          - string
        role: string        # Optional: Your specific role if it differed from job title
        technologies:       # Optional: Specific technologies used in this project
          - string
        key_stakeholders:   # Optional: Types of stakeholders involved
          - string
        notable_challenges: # Optional: Major challenges faced and overcome
          - string
        direct_reports: number  # Optional: Number of direct reports on this project
        reports_to: string      # Optional: Who you reported to for this project
```

### education (Required)

Educational background.

```yaml
education:
  - degree: string          # Required: Degree type and field
    institution: string     # Required: University/College name
    year: string            # Required: Graduation year or years attended
    location: string        # Optional: Institution location
    gpa: string             # Optional: GPA (e.g., "3.9/4.0")
    honors: string          # Optional: Honors received
    details: string         # Optional: Additional details
    coursework:             # Optional: Relevant coursework
      - string
```

### skills (Required)

Categorized skills inventory.

**Note**: This section is intentionally denormalized. Skills listed here should be a comprehensive union of:

- Technologies used in work experience
- Technologies from personal projects
- Skills acquired through education/certifications
- Additional skills not mentioned elsewhere

This redundancy helps LLM parsers quickly identify all capabilities without traversing the entire document.

```yaml
skills:
  technical:                # Required: Technical skills (programming languages, databases, etc.)
    - string
  soft:                     # Optional: Soft skills (leadership, communication, etc.)
    - string
  languages:                # Optional: Spoken languages
    - string
  tools:                    # Optional: Software tools (IDEs, design tools, etc.)
    - string
  frameworks:               # Optional: Frameworks and libraries
    - string
  methodologies:            # Optional: Work methodologies (Agile, Scrum, etc.)
    - string
```

### projects (Optional)

Notable personal, open source, freelance, or side projects outside of primary employment.

```yaml
projects:
  - name: string            # Required: Project name
    type: string            # Required: Type (personal, open_source, freelance, hackathon, academic, volunteer)
    description: string     # Required: Project description
    role: string            # Optional: Your role in the project
    duration: string        # Optional: Project duration
    technologies:           # Required: Technologies used
      - string
    outcomes:               # Required: Quantified outcomes/impact
      - string
    url: string             # Optional: Project URL or repository
    context: string         # Optional: Context (e.g., "Built to solve X problem", "Contract for Y client")
    team_size: number       # Optional: Number of collaborators
    users: string           # Optional: User base or audience (e.g., "500+ GitHub stars", "10K monthly users")
```

### certifications (Optional)

Professional certifications.

```yaml
certifications:
  - name: string            # Required: Certification name
    issuer: string          # Required: Issuing organization
    year: string            # Required: Year obtained
    expiry: string          # Optional: Expiration date
    credential_id: string   # Optional: Credential ID
    url: string             # Optional: Verification URL
```

### publications (Optional)

Publications, articles, or presentations.

```yaml
publications:
  - title: string           # Required: Publication title
    venue: string           # Required: Where published
    year: string            # Required: Publication year
    type: string            # Optional: Type (paper, article, presentation)
    url: string             # Optional: Link to publication
    coauthors:              # Optional: Co-authors
      - string
```

### awards (Optional)

Awards and recognition.

```yaml
awards:
  - name: string            # Required: Award name
    organization: string    # Required: Awarding organization
    year: string            # Required: Year received
    description: string     # Optional: Award description
```

## Validation Rules

1. **Required Sections**: `personal_info`, `experience`, `education`, `skills` must be present
2. **Required Fields**: Fields marked as "Required" must have non-empty values
3. **Date Formats**:
   - Years: YYYY format (e.g., "2023")
   - Durations: "YYYY-YYYY" or "Mon YYYY - Mon YYYY" format
   - Use "Present" for current positions
4. **Lists**: All list fields must contain at least one item if present
5. **Achievements**: Should be quantified where possible (include numbers, percentages, metrics)
6. **Technologies**: Use consistent naming (e.g., "JavaScript" not "JS")

## Best Practices

1. **Quantify Impact**: Use numbers, percentages, and metrics in achievements
   - Good: "Reduced API response time by 45% serving 1M+ daily requests"
   - Poor: "Improved API performance"

2. **Action Verbs**: Start achievements with strong action verbs
   - Examples: Led, Developed, Implemented, Optimized, Designed

3. **Technology Naming**: Be consistent and use full names
   - Use: PostgreSQL, JavaScript, Amazon Web Services
   - Avoid: Postgres, JS, AWS (unless widely recognized)

4. **Chronological Order**: List experiences and education from most recent to oldest

5. **Relevance**: Include all experiences but focus details on relevant ones
