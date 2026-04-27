import logging
from crewai import Crew, Process
from .agents import ResearcherAgent, WriterAgent

logger = logging.getLogger(__name__)

def run_agentic_workflow(topic: str):
    logger.info(f"Starting agentic workflow for topic: {topic}")
    
    # Initialize agents
    researcher_agent_wrapper = ResearcherAgent()
    writer_agent_wrapper = WriterAgent()
    
    researcher = researcher_agent_wrapper.get_agent()
    writer = writer_agent_wrapper.get_agent()
    
    # Define tasks
    research_task = researcher_agent_wrapper.get_task(topic, researcher)
    
    # We'll use a sequential process where the writer depends on the researcher
    write_task = writer_agent_wrapper.get_task(topic, writer)
    write_task.context = [research_task]
    
    # Assemble the crew
    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.sequential,
        verbose=True
    )
    
    # Execute
    result = crew.kickoff()
    
    # Extract individual task outputs
    # result.tasks_output is a list of TaskOutput objects
    research_output = ""
    writer_output = str(result)
    
    if hasattr(result, 'tasks_output') and len(result.tasks_output) >= 2:
        research_output = result.tasks_output[0].raw
        writer_output = result.tasks_output[1].raw

    # Return the result
    return {
        "topic": topic,
        "writer_report": writer_output,
        "research_findings": research_output,
        "status": "completed"
    }
