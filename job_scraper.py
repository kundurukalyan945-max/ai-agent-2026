from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime

print("=" * 50)
print("  AI Job Scraper Agent for Kalyan")
print("=" * 50)
print("Searching for AI/ML jobs in Bengaluru...")
print("Please wait, this takes 20-30 seconds...")
print("=" * 50)

# Scrape jobs from multiple sites at once
jobs = scrape_jobs(
    site_name=["indeed", "glassdoor"],
    search_term="AI ML Python developer",
    location="Bengaluru, India",
    results_wanted=20,
    hours_old=72,
    country_indeed="India"
)

if jobs.empty:
    print("No jobs found right now. Try again later.")
else:
    # Keep only the useful columns
    jobs_clean = jobs[[
        "title",
        "company",
        "location", 
        "date_posted",
        "job_url"
    ]].copy()

    # Save to CSV file
    filename = f"jobs_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    jobs_clean.to_csv(filename, index=False)

    print(f"\nFound {len(jobs_clean)} jobs!")
    print(f"Saved to: {filename}")
    print("\nTop 5 jobs found:")
    print("-" * 50)
    
    for i, row in jobs_clean.head(5).iterrows():
        print(f"\n{i+1}. {row['title']}")
        print(f"   Company: {row['company']}")
        print(f"   Location: {row['location']}")
        print(f"   Posted: {row['date_posted']}")
        print(f"   Link: {row['job_url']}")