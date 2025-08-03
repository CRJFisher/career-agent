# Job Discovery Agent Guide

The Job Discovery Agent is an autonomous web scraping agent that intelligently discovers job opportunities from multiple job boards based on your career profile.

## Overview

Instead of manually searching through job boards, the agent:
- Crawls job listing sites starting from root URLs
- Extracts job details using AI
- Scores jobs based on relevance to your profile
- Filters and deduplicates results
- Provides a ranked list of opportunities

## How It Works

### 1. **Initialization**
The agent analyzes your career database to extract:
- Key skills and technologies
- Job titles from your experience
- Experience level (entry/mid/senior/executive)
- Search preferences (location, remote, etc.)

### 2. **Intelligent Crawling**
Starting from root URLs (job search pages), the agent:
- Navigates through pagination
- Identifies job listing URLs
- Respects rate limits and robots.txt
- Manages crawl depth to avoid going too deep

### 3. **Job Extraction**
For each discovered job URL:
- Loads the page content
- Uses LLM to extract structured data:
  - Title, company, location
  - Required and nice-to-have skills
  - Salary, benefits, team info
  - Application requirements

### 4. **Relevance Scoring**
Each job is scored based on:
- **Skills match** (40%): How well your skills align
- **Experience match** (25%): Appropriate seniority level
- **Location match** (15%): Meets location preferences
- **Career progression** (15%): Logical next step
- **Culture fit** (5%): Based on available info

### 5. **Output**
Results include:
- Ranked list of relevant jobs
- Detailed scoring for each position
- Key strengths and concerns
- Direct links to apply

## Usage

### Basic Discovery

Discover jobs using your career profile:

```bash
python main.py --discover-jobs --location "San Francisco, CA"
```

### Custom Search URLs

Provide specific search URLs to crawl:

```bash
python main.py --discover-jobs \
  --job-urls "https://linkedin.com/jobs/search/?keywords=python+developer" \
           "https://indeed.com/jobs?q=machine+learning+engineer"
```

### Advanced Options

```bash
python main.py --discover-jobs \
  --location "New York, NY" \
  --remote-ok \
  --min-relevance 0.7 \
  --max-pages 100 \
  --career-db my_career.yaml
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--discover-jobs` | Enable job discovery mode | Required |
| `--job-urls` | Custom URLs to start crawling | Auto-generated |
| `--location` | Preferred job location | None |
| `--remote-ok` | Include remote positions | True |
| `--min-relevance` | Minimum relevance score (0.0-1.0) | 0.6 |
| `--max-pages` | Max pages to crawl per site | 50 |
| `--career-db` | Path to career database | career_database.yaml |

## Supported Job Boards

The agent has specialized support for:
- **LinkedIn**: Job listings, company pages
- **Indeed**: General job search
- **Glassdoor**: Company reviews and salaries
- **Wellfound (AngelList)**: Startup jobs

It can also crawl generic job boards using pattern recognition.

## Output Format

### JSON Output (discovered_jobs.json)

```json
{
  "discovery_timestamp": "2024-01-15T10:30:00",
  "total_jobs": 25,
  "statistics": {
    "total_discovered": 150,
    "total_extracted": 75,
    "total_relevant": 25,
    "avg_relevance_score": 0.78
  },
  "jobs": [
    {
      "source_url": "https://linkedin.com/jobs/view/123456",
      "job_board": "linkedin",
      "discovered_at": "2024-01-15T10:15:00",
      "job_data": {
        "title": "Senior Python Developer",
        "company": "TechCorp",
        "location": "San Francisco, CA (Remote OK)",
        "salary_range": "$150k-$200k",
        "required_skills": ["Python", "AWS", "Docker"],
        "nice_to_have_skills": ["Kubernetes", "React"],
        "years_experience": "5+",
        "job_type": "Full-time",
        "key_responsibilities": [
          "Design scalable microservices",
          "Lead technical initiatives",
          "Mentor junior developers"
        ]
      },
      "relevance_score": {
        "overall_score": 0.88,
        "skills_match": 0.95,
        "experience_match": 0.85,
        "location_match": 1.0,
        "career_progression": 0.75,
        "culture_fit": 0.70,
        "key_strengths": [
          "Perfect Python and AWS match",
          "Remote option available",
          "Good career progression"
        ],
        "concerns": [
          "No Kubernetes experience mentioned"
        ],
        "recommendation": "strong_match"
      }
    }
  ]
}
```

### Summary Report (discovered_jobs_summary.txt)

```
=== Job Discovery Summary ===
Discovery Date: 2024-01-15 10:30

Statistics:
- Total URLs Discovered: 150
- Jobs Successfully Extracted: 75
- Jobs Meeting Relevance Threshold: 25
- Average Relevance Score: 78.00%

Top 10 Opportunities:

1. Senior Python Developer at TechCorp
   Location: San Francisco, CA (Remote OK)
   Relevance: 88.00% (strong_match)
   Key Match: Perfect Python and AWS match, Remote option available
   URL: https://linkedin.com/jobs/view/123456

2. Machine Learning Engineer at DataCo
   Location: Remote
   Relevance: 85.00% (strong_match)
   Key Match: Strong ML background, Fully remote position
   URL: https://linkedin.com/jobs/view/789012
...
```

## Configuration

### Search Preferences

Create a config file for persistent preferences:

```yaml
# job_discovery_config.yaml
search_preferences:
  location: "San Francisco, CA"
  remote_ok: true
  min_salary: 150000
  excluded_companies:
    - "Company1"
    - "Company2"
  industries:
    - "Technology"
    - "Finance"
    - "Healthcare"

discovery_config:
  max_pages_per_site: 100
  max_crawl_depth: 3
  min_relevance_score: 0.7
  extraction_batch_size: 10
```

### Custom Root URLs

Define your preferred job search URLs:

```yaml
# job_urls.yaml
root_urls:
  - "https://linkedin.com/jobs/search/?keywords=python+developer&location=San+Francisco"
  - "https://indeed.com/jobs?q=senior+engineer&l=CA"
  - "https://wellfound.com/jobs?q=python&remote=true"
  - "https://careers.google.com/jobs/results/?q=software+engineer"
```

## Best Practices

### 1. **Start Focused**
Begin with specific search URLs rather than broad queries:
```bash
# Good: Specific search
--job-urls "https://linkedin.com/jobs/search/?keywords=senior+python+developer+aws"

# Less effective: Too broad
--job-urls "https://linkedin.com/jobs"
```

### 2. **Tune Relevance Threshold**
- Start with default (0.6) and adjust based on results
- Higher threshold (0.8+) for targeted search
- Lower threshold (0.5) for exploration

### 3. **Respect Rate Limits**
The agent includes polite crawling by default:
- 2-second delay between requests
- Respects robots.txt
- Limited concurrent connections

### 4. **Regular Runs**
Schedule periodic discovery:
```bash
# Weekly job discovery
0 9 * * 1 python main.py --discover-jobs --location "San Francisco"
```

### 5. **Review and Iterate**
- Check `discovered_jobs_summary.txt` first
- Review top matches in detail
- Adjust search parameters based on results

## Troubleshooting

### No Jobs Found

1. **Check URLs**: Ensure root URLs lead to search results
2. **Broaden Search**: Lower min_relevance threshold
3. **Verify Database**: Ensure career database has skills/experience

### Low Relevance Scores

1. **Update Profile**: Add more skills to career database
2. **Refine Search**: Use more specific job titles in URLs
3. **Check Preferences**: Ensure location/remote preferences match

### Crawling Issues

1. **Rate Limiting**: Increase delay between requests
2. **JavaScript Sites**: Some sites may require browser automation
3. **Login Walls**: Some job boards require authentication

### Performance

1. **Reduce Scope**: Lower max_pages per site
2. **Batch Size**: Decrease extraction_batch_size
3. **Selective Boards**: Focus on specific job boards

## Advanced Usage

### Batch Processing Applications

After discovery, process applications in batch:

```bash
# Discover jobs
python main.py --discover-jobs --location "SF" --min-relevance 0.8

# Review results
cat outputs/discovered_jobs_summary.txt

# Apply to top matches
python main.py --batch-apply --job-list outputs/discovered_jobs.json --top 5
```

### Integration with Monitoring

Set up automated monitoring:

```python
# monitor_jobs.py
import schedule
import subprocess

def run_discovery():
    subprocess.run([
        "python", "main.py",
        "--discover-jobs",
        "--location", "San Francisco",
        "--min-relevance", "0.75"
    ])
    
    # Send notification with results
    # ...

schedule.every().monday.at("09:00").do(run_discovery)
```

### Custom Extraction Rules

For specific job boards, customize extraction:

```python
# custom_extractors.py
BOARD_PATTERNS = {
    "greenhouse.io": {
        "title_selector": "h1.job-title",
        "company_selector": ".company-name",
        "description_selector": ".job-description"
    }
}
```

## Comparison with API-Based Approaches

### Advantages of Agent-Based Discovery

| Feature | Agent-Based | API-Based |
|---------|------------|-----------|
| Cost | Free | Often paid |
| Rate Limits | Polite crawling | Strict limits |
| Coverage | Any website | Limited partners |
| Flexibility | Fully customizable | Fixed endpoints |
| Data Freshness | Real-time | May be delayed |

### When to Use Each

**Use Agent-Based When:**
- Exploring multiple job boards
- Need flexibility in data extraction
- Want to avoid API costs
- Searching niche job boards

**Consider APIs When:**
- Need structured, guaranteed data
- High-volume, automated processing
- Specific partnership benefits
- Real-time job alerts required

## Future Enhancements

Planned improvements include:

1. **Incremental Crawling**: Only discover new jobs since last run
2. **Smart Scheduling**: Optimal times for different job boards  
3. **Application Tracking**: Track which jobs you've applied to
4. **Market Analytics**: Trends in job requirements over time
5. **Personalized Alerts**: Notify for high-relevance matches

## Conclusion

The Job Discovery Agent transforms job searching from a manual, time-consuming task into an intelligent, automated process. By leveraging your career profile and AI-powered analysis, it surfaces the most relevant opportunities while you focus on preparing strong applications.

For questions or contributions, see the main project documentation.