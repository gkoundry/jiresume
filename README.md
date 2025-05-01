# JIRESUME

## Description
This program will scan all Jira tickets assigned to you and create a list of skills
and job responsibilities and accomplishments which you can add to your resume.
You can optionally include a description of a job you are interested in and have
it emphasize skills and achievements which are most relevant.

This is useful if you:
- are lazy
- have a bad memory
- want to create a tailored resume for each job application

## Prerequisites

### System Requirements
- Python 3.8+
- pip
- virtualenv (recommended)

### Environment Variables
The following environment variables must be set:
- one of `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` or `GOOGLE_API_KEY`: The API key for your preferred LLM
- `JIRA_API_KEY`:  API key used to access Jira

## Installation

1. Clone the repository:
```bash
git clone https://github.com/gkoundry/jiresume.git
cd jiresume
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables:
```bash
# Linux/macOS
export OPENAI_API_KEY=llm_api_key
export JIRA_API_KEY=jira_api_key

# Windows (PowerShell)
$env:OPENAI_API_KEY = "llm_api_key"
$env:JIRA_API_KEY = "jira_api_key"
```

## Usage

### Command Line Arguments
```bash
Usage: python jiresume.py [OPTIONS]

  Create resume skills and work experience from Jira tickets.

Options:
  -url, --jira-url JIRA_URL       Jira URL to connect to. Example:
                                  https://your_company.atlassian.net
                                  [required]
  -u, --jira-username JIRA_USERNAME
                                  Jira username to retrieve tickets for.
                                  [required]
  -j, --job-desc-file FILENAME    File containing job description. If provided
                                  generated resume section will be based on
                                  this job description.
  -p, --llm-provider [openai|anthropic|google]
                                  LLM provider to use. Default is 'openai'.
  -mt, --max-tickets COUNT        Maximum number of tickets to fetch from
                                  Jira. Default is 1000.
  -ml, --max-description-length LENGTH
                                  Maximum length of the ticket description to
                                  include in the resume. Longer descriptions
                                  will be truncated. Default is 300.
  --help                          Show this message and exit.

```

### Example
```bash
python jiresume.py -url https://your_company.atlassian.net -u your_name@gmail.com -p openai
```

## Troubleshooting

- Ensure all environment variables are set correctly
- Check that all dependencies are installed
- Verify Python version compatibility
- If you are getting context size errors, you can use `--max-tickets` and/or `--max-description-length`
to limit the amount of data pulled from Jira


## Contact

Glen Koundry - gkoundry@gmail.com
