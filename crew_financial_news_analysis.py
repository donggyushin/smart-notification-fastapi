
from crewai import Agent, Crew, Task, Process
from crewai_tools import SerperDevTool

class FinancialNewsAnalysis:
    def financialNewsResearcher(self) -> Agent:
        return Agent(
            role="Financial News Researcher",
            goal="Find and search news that have high impact on USA stock marget",
            backstory="",
            inject_date=True, # Automatically inject current date into tasks
            reasoning=True, 
            tools=[SerperDevTool()],
            allow_code_execution=True,
            llm="gpt-4o",
            verbose=True
        )
    
    def financialNewsResearch(self) -> Task:
        return Task(
            description="""
            Read recent 15-20 news related with USA stock market and
            filter news that has potential high impact on USA stock marget.
            """,
            expected_output="""
            News urls: ["url1", "url2", ...]
            """,
            agent=self.financialNewsResearcher()
        )
    
    def crew(self) -> Crew:
        return Crew(
            agents=[self.financialNewsResearcher()],
            tasks=[self.financialNewsResearch()],
            process=Process.sequential,
            verbose=True
        )

if __name__ == "__main__":
    analysis = FinancialNewsAnalysis()
    result = analysis.crew().kickoff(inputs={})
    print(result)