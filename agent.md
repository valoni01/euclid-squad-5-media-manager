# Agent Documentation

This document provides a high-level overview of the agents within the codebase. Each agent's primary role, key interactions, and tools/functions used are described below.

## Agents Overview

### Assistant Agent
- **Primary Role**: Acts as a social media assistant responsible for handling user requests and producing social media content.
- **Key Interactions**: Interacts with users to gather requirements for content creation, retrieves media plans, and submits content requests.
- **Tools/Functions Used**: `submit_request`, `list_saved_plans`, `get_plan_details`.

### Relevance Checker Agent
- **Primary Role**: Determines whether a user message is related to social media content creation or calendar management.
- **Key Interactions**: Works as a filter to ensure only relevant messages are processed by the assistant agent.
- **Tools/Functions Used**: N/A

### Research Agent
- **Primary Role**: Focuses on researching social media trends, audience behavior, and platform dynamics.
- **Key Interactions**: Gathers information to support content creation by using various research tools.
- **Tools/Functions Used**: `serper_web_search`, `fetch_url_text`, `browse_url_with_playwright`.

### Research Analyst Agent
- **Primary Role**: Acts as a research analyst for social media and marketing teams, evaluating research coverage and providing content guidance.
- **Key Interactions**: Analyzes accumulated research reports to make decisions on content strategies.
- **Tools/Functions Used**: N/A

### Research Tools
- **Primary Role**: Provides various tools for conducting research, such as web searching and fetching URL text.
- **Key Interactions**: Used by the research agent to gather data from the web.
- **Tools/Functions Used**: `serper_web_search`, `fetch_url_text`, `browse_url_with_playwright`.

## Maintenance
- Ensure this documentation is updated whenever new agents are added or existing agents are modified.

## Style Guidelines
- Follow the style guidelines as seen in `README.md` for consistency and readability.
