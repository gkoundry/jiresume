"""Jiresume: Create resume sections from Jira tickets."""

import os

import click
from jira import JIRA
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

JOB_HISTORY_PROMPT = """
Objective: Generate a comprehensive and cohesive summary of responsibilities and accomplishments
based on the provided Jira tickets to be used on a resume.

Instructions:

Input: You will be provided with a potentially long list of Jira tickets.
Each ticket includes a title and a description.  The list will be in chronological
order to make grouping tickets easier.

Output: Produce a well-structured, concise summary highlighting key responsibilities,
skills, and accomplishments.

The summary should:
- Group similar tasks and projects together to form a larger narrative.
- Avoid focusing on individual tickets; instead, emphasize overarching themes and patterns.
- Ensure all significant contributions are included without omitting any major areas of work.
- Use professional language suitable for a resume.

Highlight quantifiable achievements where possible (e.g., improved performance
by X%, reduced bugs by Y%, etc.).

Guidelines:

Avoid Hallucinations: Stick closely to the information provided in the tickets.
Do not infer or assume details that are not explicitly mentioned.

Comprehensive Coverage: Ensure that all major tasks and projects are included in the summary.
Cross-reference tickets to avoid omissions.

Narrative Structure: Organize the summary into clear sections (e.g., Project Management,
Software Development, Bug Fixing, Collaboration, Innovation). Within each section,
create sub-points that group related tickets.

Quantifiable Achievements: Where possible, extract and highlight metrics, percentages,
and other quantifiable data to demonstrate impact.

Professional Tone: Use formal and professional language.
Avoid jargon unless it is industry-standard and well-understood.

The list of tickets I will provide starts with ***Tickets*** and each items contains
both a "Summary:" and "Descripton": section. The tickets are delimited by '++++++++++'.

{job_desc_prompt}

***Tickets***
{ticket_list}
"""

JOB_DESC_PROMPT = """
I will also provide you with a description of the job I am applying for.
When creating the list of skills and work experience please prioritize the ones
which are relevant to this job description.

The job description starts with ***Job Description***.

***Job Description***

{job_desc}
"""


def get_llm_api_key(llm_provider: str) -> str:
    """Get the API key for the specified LLM provider from environment variables."""
    llm_env_var_name = f"{llm_provider.upper()}_API_KEY"
    llm_api_key = os.getenv(llm_env_var_name)
    if not llm_api_key:
        raise ValueError(f"Please set the {llm_env_var_name} environment variable")
    return llm_api_key


def get_job_desc_prompt(job_desc_file: str | None) -> str:
    """Read the job description from a file if provided and return the job description prompt."""
    if not job_desc_file:
        return ""
    with open(job_desc_file, "r", encoding="utf-8") as f:
        job_desc = f.read()
        return JOB_DESC_PROMPT.format(job_desc=job_desc)


def get_jira_issues(
    jira_url: str,
    jira_username: str,
    jira_api_key: str,
    max_tickets: int,
    max_description_length: int,
) -> list[str]:
    """Fetch Jira issues assigned to the user"""
    jira = JIRA(server=jira_url, basic_auth=(jira_username, jira_api_key))
    sanitized_name = jira_username.replace('"', '\\"')
    jql_query = f'assignee = "{sanitized_name}" ORDER BY updated ASC'

    chunk_size = 200  # 200 is under the 1000-item cap
    start_at = 0

    issue_list = []
    while True:
        issues = jira.search_issues(
            jql_str=jql_query,
            startAt=start_at,
            maxResults=chunk_size,
            fields="description,summary",
        )
        if not issues:
            break

        for issue in issues:
            desc = (
                issue.fields.description[:max_description_length]
                if issue.fields.description
                else ""
            )
            issue_list.append(f"Summary: {issue.fields.summary}\nDescription: {desc}")
            if len(issue_list) >= max_tickets:
                return issue_list

        # move the window forward
        start_at += chunk_size

        # stop if we've fetched all
        if start_at >= issues.total:
            break
    return issue_list


def get_llm(provider: str, api_key: str) -> BaseChatModel:
    """Instantiate the appropriate LLM based on provider"""
    provider = provider.lower()
    if provider == "openai":
        return ChatOpenAI(api_key=api_key, model="gpt-4o")
    if provider == "anthropic":
        return ChatAnthropic(
            anthropic_api_key=api_key, model="claude-3-7-sonnet-latest"
        )
    if provider == "google":
        return ChatGoogleGenerativeAI(api_key=api_key, model="gemini-2.0-flash")
    raise ValueError(f"Unsupported provider: {provider}")


def get_job_summary(
    issue_list: list[str], job_desc_prompt: str, llm_provider: str, llm_api_key: str
) -> str:
    """Generate a job summary from a list of Jira issues using the LLM"""

    # Create prompt
    issue_list_str = "\n++++++++++\n".join(issue_list)
    prompt = JOB_HISTORY_PROMPT.format(
        ticket_list=issue_list_str, job_desc_prompt=job_desc_prompt
    )

    # Create LLM and chain
    llm = get_llm(llm_provider, llm_api_key)
    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert resume writer.  "
                "You assist people with writing high quality resumes.",
            ),
            ("user", "{input}"),
        ]
    )
    output_parser = StrOutputParser()
    chain = prompt_template | llm | output_parser

    # Run the chain and return the result
    return str(chain.invoke({"input": prompt}))


@click.command()
@click.option(
    "-url",
    "--jira-url",
    required=True,
    type=str,
    help="Jira URL to connect to. Example: https://your_company.atlassian.net",
    metavar="JIRA_URL",
)
@click.option(
    "-u",
    "--jira-username",
    required=True,
    type=str,
    help="Jira username to retrieve tickets for.",
    metavar="JIRA_USERNAME",
)
@click.option(
    "-j",
    "--job-desc-file",
    required=False,
    type=str,
    help=(
        "File containing job description. If provided generated resume section "
        "will be based on this job description."
    ),
    metavar="FILENAME",
)
@click.option(
    "-p",
    "--llm-provider",
    required=False,
    default="openai",
    type=click.Choice(["openai", "anthropic", "google"]),
    help="LLM provider to use. Default is 'openai'.",
)
@click.option(
    "-mt",
    "--max-tickets",
    required=False,
    type=int,
    default=1000,
    help="Maximum number of tickets to fetch from Jira. Default is 1000.",
    metavar="COUNT",
)
@click.option(
    "-ml",
    "--max-description-length",
    required=False,
    type=int,
    default=300,
    help=(
        "Maximum length of the ticket description to include in the resume. "
        "Longer descriptions will be truncated. Default is 300."
    ),
    metavar="LENGTH",
)
def run(
    jira_url: str,
    jira_username: str,
    job_desc_file: str | None,
    llm_provider: str,
    max_tickets: int,
    max_description_length: int,
) -> None:
    """
    Create resume skills and work experience from Jira tickets.
    """
    llm_api_key = get_llm_api_key(llm_provider)

    jira_api_key = os.getenv("JIRA_API_KEY")
    if not jira_api_key:
        raise ValueError("JIRA_API_KEY environment variable is not set.")

    job_desc_prompt = get_job_desc_prompt(job_desc_file)

    issue_list = get_jira_issues(
        jira_url, jira_username, jira_api_key, max_tickets, max_description_length
    )

    job_summary = get_job_summary(
        issue_list, job_desc_prompt, llm_provider, llm_api_key
    )
    print(job_summary)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    run()
