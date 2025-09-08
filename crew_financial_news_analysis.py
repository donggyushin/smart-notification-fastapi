
from crewai import Agent, Crew, Task, Process
from crewai_tools import SerperDevTool
from pydantic import BaseModel
from typing import List
from datetime import date

class News(BaseModel):
    title: str 
    summarize: str 
    url: str 
    published_date: date 
    score: int 
    tickers: List[str]

class FinancialNewsAnalysis:
    def researcher(self) -> Agent:
        return Agent(
            role="Financial News Researcher",
            goal="Find and search news that have high impact on USA stock marget",
            backstory="",
            inject_date=True, # Automatically inject current date into tasks
            reasoning=True, 
            tools=[SerperDevTool()],
            llm="gpt-4o",
            verbose=True
        )
    
    def analyst(self) -> Agent:
        return Agent(
            role="Financial News Analyst",
            goal="""
            Provide perfectly summarized, analyzed and structured news data. 
            This agent analyze news very precisely and knows what is the key point of the news.
            """,
            backstory="",
            inject_date=True, # Automatically inject current date into tasks
            reasoning=True, 
            tools=[SerperDevTool()],
            llm="gpt-4o",
            verbose=True
        )
    
    def research(self) -> Task:
        return Task(
            description="""
            Read recent 15-20 news related with USA stock market and
            filter news that has potential high impact on USA stock marget.
            """,
            expected_output="""
            News urls: ["url1", "url2", ...]
            """,
            agent=self.researcher()
        )
    
    def analyze(self) -> Task:
        return Task(
            description="""
            Read news, comments, read count through all given news urls.
            what ticker this news can effect, that effect is negative or positive and how big impact this new has. 
            Analyze them and make score. If the new most high good impact, then the news's score is 10, 
            if the new most high bad impact then the news's score is -10. 
            Summarize news for easy reading. 
            """,
            expected_output="""
            Perfectly summarized and analyzed and structured new data
            """,
            output_pydantic=News,
            agent=self.analyst()
        )
    
    def crew(self) -> Crew:
        return Crew(
            agents=[self.researcher(), self.analyst()],
            tasks=[self.research(), self.analyze()],
            process=Process.sequential,
            verbose=True
        )

if __name__ == "__main__":
    analysis = FinancialNewsAnalysis()
    result = analysis.crew().kickoff()
    print(result)