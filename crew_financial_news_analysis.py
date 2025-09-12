
from crewai import Agent, Crew, Task, Process
from crewai_tools import SerperDevTool, WebsiteSearchTool
from models import NewsEntity
from typing import List, Union
from pydantic import BaseModel
import json
import re
import logging
from datetime import datetime
import pytz
from dateutil import parser

class NewsAnalysisResult(BaseModel):
    """Structured container for news analysis results"""
    news_items: List[NewsEntity]

logger = logging.getLogger(__name__)

class FinancialNewsAnalysis:
    
    def extract_news_entities_from_result(self, result) -> List[NewsEntity]:
        """
        Post-process crew result to ensure clean list of NewsEntity objects
        """
        try:
            # Extract raw data
            if hasattr(result, 'raw'):
                raw_data = result.raw
            elif hasattr(result, 'output'):
                raw_data = result.output
            else:
                raw_data = result
            
            # If it's already a NewsAnalysisResult, extract the news_items
            if isinstance(raw_data, NewsAnalysisResult):
                return raw_data.news_items
            
            # If it's already a list of NewsEntity objects
            if isinstance(raw_data, list) and all(isinstance(item, NewsEntity) for item in raw_data):
                return raw_data
            
            # If it's a string, try to parse JSON
            if isinstance(raw_data, str):
                # Clean the string - remove markdown, extra text, etc.
                json_content = self._clean_json_string(raw_data)
                
                try:
                    parsed = json.loads(json_content)
                    
                    # Handle NewsAnalysisResult format
                    if isinstance(parsed, dict) and 'news_items' in parsed:
                        news_data = parsed['news_items']
                    elif isinstance(parsed, list):
                        news_data = parsed
                    else:
                        news_data = [parsed]
                    
                    # Convert to NewsEntity objects
                    news_entities = []
                    for item in news_data:
                        if isinstance(item, dict):
                            try:
                                # Validate and create NewsEntity
                                news_entity = NewsEntity(**item)
                                news_entities.append(news_entity)
                            except Exception as e:
                                logger.warning(f"Failed to create NewsEntity from {item}: {e}")
                                continue
                        elif isinstance(item, NewsEntity):
                            news_entities.append(item)
                    
                    return news_entities
                
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from crew result: {e}")
                    return []
            
            # If it's a dict, try to extract news items
            if isinstance(raw_data, dict):
                if 'news_items' in raw_data:
                    return self.extract_news_entities_from_result(raw_data['news_items'])
                else:
                    # Single news item
                    try:
                        return [NewsEntity(**raw_data)]
                    except Exception as e:
                        logger.error(f"Failed to create NewsEntity from dict: {e}")
                        return []
            
            logger.error(f"Unexpected result type: {type(raw_data)}")
            return []
            
        except Exception as e:
            logger.error(f"Error extracting news entities: {e}")
            return []
    
    def _clean_json_string(self, content: str) -> str:
        """Clean JSON string from crew output"""
        # Remove markdown code blocks
        content = re.sub(r'```(?:json|javascript|js)?\s*\n?(.*?)\n?```', r'\1', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove leading/trailing whitespace
        content = content.strip()
        
        # Find JSON content (array or object)
        if '[' in content:
            start = content.find('[')
            end = content.rfind(']')
            if start != -1 and end != -1 and end > start:
                content = content[start:end+1]
        elif '{' in content:
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1 and end > start:
                content = content[start:end+1]
        
        return content

    researcher_agent = Agent(
            role="Financial News Researcher",
            goal="Discover and curate high-impact financial news that could significantly influence US stock market movements and investor sentiment",
            backstory="You are an experienced financial journalist with 15+ years covering Wall Street. You have an exceptional ability to identify breaking news, earnings reports, regulatory changes, and market-moving events before they become mainstream. Your network spans across major financial institutions, and you understand which news sources deliver the most reliable and timely market intelligence.",
            inject_date=True, # Automatically inject current date into tasks
            reasoning=True,
            tools=[SerperDevTool()],
            llm="gpt-4o",
            verbose=True
        )

    analyst_agent = Agent(
            role="Financial News Analyst",
            goal="Transform raw financial news into actionable insights by analyzing market impact, identifying affected securities, and providing precise sentiment scoring with comprehensive summaries",
            backstory="You are a seasoned equity research analyst with deep expertise in fundamental and technical analysis. Having worked at top-tier investment banks for over a decade, you excel at quickly parsing complex financial information, identifying key market drivers, and quantifying potential stock price impacts. Your analytical framework combines quantitative metrics with qualitative assessment to deliver precise investment insights.",
            inject_date=True, # Automatically inject current date into tasks
            reasoning=True,
            tools=[WebsiteSearchTool()],
            llm="gpt-4o",
            verbose=True
        )

    research_task = Task(
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
            agent=researcher_agent
        )

    analyze_task = Task(
            description="""
            Using the URLs provided by the research task, perform deep analysis of each news URL to extract actionable investment insights:

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
            
            CRITICAL OUTPUT REQUIREMENTS:
            - You MUST return ONLY a valid JSON array containing NewsEntity objects
            - Do NOT include any explanatory text, thoughts, or reasoning in your response
            - Do NOT wrap the JSON in markdown code blocks
            - Do NOT add any commentary before or after the JSON
            - The output must be a pure JSON array that can be directly parsed by json.loads()
            - Each object must have exactly these fields: title, summarize, url, published_date, score, tickers
            """,
            expected_output="""
            RETURN ONLY THIS EXACT FORMAT - NO OTHER TEXT:
            [
                {
                    "title": "Clear, descriptive headline",
                    "summarize": "Concise 2-3 sentence investment summary",
                    "url": "Original news source URL",
                    "published_date": "Publication date in YYYY-MM-DD HH:mm:ss format and timezone is UTC. Hours, minutes are mandatory if possible. Seconds could be 00.",
                    "score": "Integer from -10 to +10 representing market impact",
                    "tickers": ["List of affected stock symbols"]
                }
            ]
            
            IMPORTANT: Return only the JSON array above. No explanations, no markdown, no additional text.
            """,
            output_pydantic=NewsAnalysisResult,
            agent=analyst_agent,
            context=[research_task]
        )


    def crew(self) -> Crew:

        return Crew(
            agents=[self.researcher_agent, self.analyst_agent],
            tasks=[self.research_task, self.analyze_task],
            process=Process.sequential,
            verbose=True,
            output_log_file=False,  # Disable output logging to keep results clean
            max_iter=1  # Single iteration to avoid multiple attempts that can add noise
        )

if __name__ == "__main__":
    analysis = FinancialNewsAnalysis()
    result = analysis.crew().kickoff()
    print(result)