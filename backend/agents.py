import os
from textwrap import dedent
from crewai import Agent, Task
from crewai_tools import SerperDevTool, ScrapeWebsiteTool

def get_llm(temperature=0.3):
    api_key = os.getenv("LLM_API_KEY")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    
    model_name = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    # For CrewAI, use the 'gemini/' prefix to trigger LiteLLM correctly
    if not model_name.startswith("gemini/"):
        return f"gemini/{model_name}"
    return model_name

class ResearcherAgent:
    ROLE = "Expert Educational Researcher"
    GOAL = "Conduct thorough academic research on the given study topic and produce structured insights."
    BACKSTORY = "You are a senior academic researcher specialist. You excel at breaking complex topics into digestible study material."

    def get_agent(self):
        # Tools initialization
        # Note: SerperDevTool requires SERPER_API_KEY in .env
        search_tool = SerperDevTool()
        scrape_tool = ScrapeWebsiteTool()

        return Agent(
            role=self.ROLE,
            goal=self.GOAL,
            backstory=self.BACKSTORY,
            llm=get_llm(temperature=0.2),
            tools=[search_tool, scrape_tool],
            allow_delegation=False,
            verbose=True
        )

    def get_task(self, topic: str, agent: Agent):
        return Task(
            description=dedent(f"""
                Research the topic "{topic}" thoroughly using the available web search and scraping tools.
                Your goal is to move beyond general knowledge and find specific, up-to-date, and authentic academic information.
                
                Focus on:
                1. Core definition and contemporary context.
                2. 5-8 Key concepts, theories, or pillars.
                3. Real-world applications, case studies, or examples.
                4. Potential study resources, including recent papers, reputable websites, or book titles.
                
                Ensure you verify information from multiple sources.
                
                Provide a very concise 'Research Trace' report. 
                DO NOT include any titles, headers, or introductory text. Start directly with the list.
                For each piece of information or topic found, list it in this exact format:
                - **[Short Topic Name]**: [Website Name] - [Full URL Link]
                
                Keep the descriptions extremely brief. The goal is to show the user exactly where the information came from with clickable links.
            """).strip(),
            agent=agent,
            expected_output="A concise list of research topics with their corresponding website names and clickable Markdown links, without any headers."
        )

class WriterAgent:
    ROLE = "Expert Educational Content Writer"
    GOAL = "Transform structured research data into high-quality, student-friendly educational content."
    BACKSTORY = "You are an award-winning educational content writer. You excel at simplifying academic topics into readable study guides."

    def get_agent(self):
        return Agent(
            role=self.ROLE,
            goal=self.GOAL,
            backstory=self.BACKSTORY,
            llm=get_llm(temperature=0.5),
            allow_delegation=False,
            verbose=True
        )

    def get_task(self, topic: str, agent: Agent):
        return Task(
            description=dedent(f"""
                Using the research provided by the Researcher, create a comprehensive Study Guide for the topic "{topic}".
                
                The Study Guide should be in Markdown and include:
                - A clear Title
                - Detailed Overview
                - Key Concepts explained simply
                - Practical Examples
                - Summary Conclusion
            """).strip(),
            agent=agent,
            expected_output="A well-formatted Markdown Study Guide."
        )
