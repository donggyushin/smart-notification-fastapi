
from crewai import Agent, Crew, Task, Process
from crewai_tools import SerperDevTool, WebsiteSearchTool
from models import NewsEntity

class FinancialNewsAnalysis:
    def researcher(self) -> Agent:
        return Agent(
            role="Financial News Researcher",
            goal="Discover and curate high-impact financial news that could significantly influence US stock market movements and investor sentiment",
            backstory="You are an experienced financial journalist with 15+ years covering Wall Street. You have an exceptional ability to identify breaking news, earnings reports, regulatory changes, and market-moving events before they become mainstream. Your network spans across major financial institutions, and you understand which news sources deliver the most reliable and timely market intelligence.",
            inject_date=True, # Automatically inject current date into tasks
            reasoning=True, 
            tools=[SerperDevTool()],
            llm="gpt-4o",
            verbose=True
        )
    
    def analyst(self) -> Agent:
        return Agent(
            role="Financial News Analyst",
            goal="Transform raw financial news into actionable insights by analyzing market impact, identifying affected securities, and providing precise sentiment scoring with comprehensive summaries",
            backstory="You are a seasoned equity research analyst with deep expertise in fundamental and technical analysis. Having worked at top-tier investment banks for over a decade, you excel at quickly parsing complex financial information, identifying key market drivers, and quantifying potential stock price impacts. Your analytical framework combines quantitative metrics with qualitative assessment to deliver precise investment insights.",
            inject_date=True, # Automatically inject current date into tasks
            reasoning=True, 
            tools=[WebsiteSearchTool()],
            llm="gpt-4o",
            verbose=True
        )
    
    def research(self) -> Task:
        return Task(
            description="""
            Conduct comprehensive research to identify 15-20 recent financial news articles that could significantly impact US stock market performance. Focus on:
            - Breaking earnings reports and guidance updates
            - Federal Reserve policy announcements and economic indicators
            - Major corporate mergers, acquisitions, and strategic partnerships
            - Regulatory changes and government policy shifts
            - Geopolitical events affecting market sentiment
            - Sector-specific developments in technology, healthcare, finance, and energy
            
            Filter and prioritize news based on potential market impact, credibility of source, and relevance to major publicly traded companies.
            """,
            expected_output="""
            A curated list of high-impact financial news URLs in the following format:
            [
                "https://example.com/news1",
                "https://example.com/news2",
                ...
            ]
            Each URL should represent news with significant potential to move individual stocks or broader market indices.
            """,
            agent=self.researcher()
        )
    
    def analyze(self) -> Task:
        return Task(
            description="""
            Perform deep analysis of each provided news URL to extract actionable investment insights:
            
            1. Content Analysis:
               - Read full article content, comments, and engagement metrics
               - Identify key facts, data points, and market implications
               - Extract quotes from executives, analysts, and industry experts
            
            2. Market Impact Assessment:
               - Determine specific ticker symbols that will be affected
               - Classify impact as positive, negative, or neutral
               - Assign impact score from -10 (most bearish) to +10 (most bullish)
               - Consider both direct and indirect effects on related companies/sectors
            
            3. Summary Creation:
               - Create concise, investor-focused summary (2-3 sentences)
               - Highlight the most critical information for trading decisions
               - Include publication date and source credibility assessment
            
            Scoring Guidelines:
            - Score 8-10: Major positive catalysts (earnings beats, breakthrough products, favorable regulations)
            - Score 6-7: Moderate positive developments (partnership announcements, analyst upgrades)
            - Score -6 to -7: Moderate negative developments (missed guidance, competitive threats)
            - Score -8 to -10: Major negative catalysts (regulatory penalties, accounting issues, leadership departures)
            """,
            expected_output="""
            A list of News objects, with each article analyzed and structured conforming to the News Pydantic model:
            [
                {
                    "title": "Clear, descriptive headline",
                    "summarize": "Concise 2-3 sentence investment summary",
                    "url": "Original news source URL",
                    "published_date": "Publication date in YYYY-MM-DD format",
                    "score": "Integer from -10 to +10 representing market impact",
                    "tickers": ["List of affected stock symbols"]
                },
                ...
            ]
            Analyze ALL provided URLs from the research task.
            """,
            output_pydantic=NewsEntity,
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