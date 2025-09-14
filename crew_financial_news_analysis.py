#!/usr/bin/env python3

from crewai import Agent, Crew, Task, Process
from crewai_tools import WebsiteSearchTool
from crewai.tools import BaseTool
from models import NewsEntity
from typing import List
from pydantic import BaseModel
import json
import re
import logging
import yfinance as yf
from datetime import datetime, timedelta

class NewsAnalysisResult(BaseModel):
    """Structured container for news analysis results"""
    news_items: List[NewsEntity]

logger = logging.getLogger(__name__)

class YFinanceNewsTool(BaseTool):
    name: str = "YFinance News Tool"
    description: str = "Fetches real financial news from Yahoo Finance for major tickers and market news"

    def _run(self, query: str = "general") -> str:
        """
        Fetch real news from Yahoo Finance
        Args:
            query: Either 'general' for market news or specific ticker symbols
        """
        try:
            news_items = []

            if query.lower() == "general":
                # Get general market news from major indices and popular stocks
                tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META"]
                for ticker in tickers:
                    try:
                        stock = yf.Ticker(ticker)
                        news = stock.news
                        for item in news[:3]:  # Get top 3 news per ticker
                            content = item.get("content", {})
                            if content:
                                # Parse the new yfinance structure
                                url = ""
                                if content.get("clickThroughUrl"):
                                    url = content["clickThroughUrl"].get("url", "")
                                elif content.get("canonicalUrl"):
                                    url = content["canonicalUrl"].get("url", "")

                                if url and content.get("title"):
                                    # Parse publication date
                                    pub_date = content.get("pubDate", "")
                                    published_timestamp = 0
                                    if pub_date:
                                        try:
                                            dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                                            published_timestamp = dt.timestamp()
                                        except:
                                            published_timestamp = datetime.now().timestamp()

                                    news_items.append({
                                        "title": content["title"],
                                        "url": url,
                                        "published": published_timestamp,
                                        "source": content.get("provider", {}).get("displayName", "Yahoo Finance"),
                                        "ticker": ticker
                                    })
                    except Exception as e:
                        logger.warning(f"Error fetching news for {ticker}: {e}")
                        continue
            else:
                # Get news for specific tickers
                tickers = [t.strip().upper() for t in query.split(",")]
                for ticker in tickers[:10]:  # Limit to 10 tickers
                    try:
                        stock = yf.Ticker(ticker)
                        news = stock.news
                        for item in news[:3]:  # Get top 3 news per ticker
                            content = item.get("content", {})
                            if content:
                                # Parse the new yfinance structure
                                url = ""
                                if content.get("clickThroughUrl"):
                                    url = content["clickThroughUrl"].get("url", "")
                                elif content.get("canonicalUrl"):
                                    url = content["canonicalUrl"].get("url", "")

                                if url and content.get("title"):
                                    # Parse publication date
                                    pub_date = content.get("pubDate", "")
                                    published_timestamp = 0
                                    if pub_date:
                                        try:
                                            dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                                            published_timestamp = dt.timestamp()
                                        except:
                                            published_timestamp = datetime.now().timestamp()

                                    news_items.append({
                                        "title": content["title"],
                                        "url": url,
                                        "published": published_timestamp,
                                        "source": content.get("provider", {}).get("displayName", "Yahoo Finance"),
                                        "ticker": ticker
                                    })
                    except Exception as e:
                        logger.warning(f"Error fetching news for {ticker}: {e}")
                        continue

            # Filter for recent news (last 48 hours)
            cutoff_time = datetime.now().timestamp() - (48 * 3600)
            recent_news = [item for item in news_items if item.get("published", 0) > cutoff_time]

            # Remove duplicates by URL
            seen_urls = set()
            unique_news = []
            for item in recent_news:
                if item["url"] and item["url"] not in seen_urls:
                    seen_urls.add(item["url"])
                    unique_news.append(item)

            # Sort by publication time (newest first)
            unique_news.sort(key=lambda x: x.get("published", 0), reverse=True)

            return json.dumps(unique_news[:20])  # Return top 20 unique news items

        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance news: {e}")
            return json.dumps([])

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

    def get_real_news_data(self) -> List[dict]:
        """Get real news data with URLs and metadata directly from YFinanceNewsTool"""
        tool = YFinanceNewsTool()
        all_news = []
        seen_urls = set()

        # The exact queries the researcher should use
        queries = [
            "general",
            "AAPL,MSFT,GOOGL,AMZN,TSLA",
            "JPM,BAC,WFC,GS,MS",
            "JNJ,PFE,MRNA,ABBV",
            "XOM,CVX,COP"
        ]

        for query in queries:
            try:
                result = tool._run(query)
                news_data = json.loads(result)

                for item in news_data:
                    url = item.get('url', '')
                    if url and url not in seen_urls:  # Deduplicate
                        seen_urls.add(url)
                        all_news.append(item)

            except Exception as e:
                logger.error(f"Error fetching {query}: {e}")

        return all_news[:20]  # Return top 20

    analyst_agent = Agent(
        role="Financial News Analyst",
        goal="Transform raw financial news into actionable insights by analyzing market impact, identifying affected securities, and providing precise sentiment scoring with comprehensive summaries, with STRONG emphasis on news recency",
        backstory="You are a seasoned equity research analyst with deep expertise in fundamental and technical analysis. Having worked at top-tier investment banks for over a decade, you excel at quickly parsing complex financial information, identifying key market drivers, and quantifying potential stock price impacts. Your analytical framework combines quantitative metrics with qualitative assessment to deliver precise investment insights. You understand that NEWS RECENCY IS CRITICAL - older news has diminished market impact, and you automatically reduce scores for news older than 24 hours, with significant penalties for news older than 48 hours.",
        inject_date=True, # Automatically inject current date into tasks
        reasoning=True,
        tools=[WebsiteSearchTool(), YFinanceNewsTool()],
        llm="gpt-5",
        verbose=True
    )

    def create_analyze_task(self, news_data: List[dict]) -> Task:
        """Create analyze task with real news data including URLs and metadata"""

        # Extract just URLs for backward compatibility
        urls = [item['url'] for item in news_data]

        # Format the news data for the agent
        news_data_text = json.dumps(news_data, indent=2)

        return Task(
            description=f"""
            IMPORTANT: You have been provided with REAL news data from Yahoo Finance with accurate timestamps:
            {news_data_text}

            Each news item contains:
            - title: The news headline
            - url: The REAL Yahoo Finance URL (use this exact URL)
            - published: Unix timestamp of publication (use this for accurate published_date)
            - source: The news source/publisher
            - ticker: Associated stock ticker (if any)

            You must analyze each of these EXACT URLs and create a NewsEntity for each one.

            Using the URLs provided above, perform deep analysis of each news URL to extract actionable investment insights:

            1. Content Analysis:
               - Read full article content, comments, and engagement metrics
               - Identify key facts, data points, and market implications
               - Extract quotes from executives, analysts, and industry experts

            2. Market Impact Assessment:
               - Determine specific ticker symbols that will be affected
               - Classify impact as positive, negative, or neutral
               - Assign impact score from -10 (most bearish) to +10 (most bullish)
               - Consider both direct and indirect effects on related companies/sectors
               - CRITICAL: Apply recency penalty to scores based on published_date

            3. Summary Creation:
               - Create concise, investor-focused summary (2-3 sentences)
               - Highlight the most critical information for trading decisions
               - Focus on market impact and investment implications only

            Scoring Guidelines (BEFORE applying recency penalty):
            - Score 8-10: Major positive catalysts (earnings beats, breakthrough products, favorable regulations)
            - Score 6-7: Moderate positive developments (partnership announcements, analyst upgrades)
            - Score -6 to -7: Moderate negative developments (missed guidance, competitive threats)
            - Score -8 to -10: Major negative catalysts (regulatory penalties, accounting issues, leadership departures)

            MANDATORY RECENCY SCORING PENALTIES:
            - News 0-6 hours old: No penalty (full score)
            - News 6-24 hours old: Reduce absolute score by 1 point
            - News 24-48 hours old: Reduce absolute score by 3 points
            - News 48-72 hours old: Reduce absolute score by 5 points
            - News older than 72 hours: Maximum score of ±2 (severely outdated)

            Example: A +8 score news that is 30 hours old becomes +8 - 3 = +5

            CRITICAL OUTPUT REQUIREMENTS:
            - You MUST return ONLY a valid JSON array containing NewsEntity objects
            - Do NOT include any explanatory text, thoughts, or reasoning in your response
            - Do NOT wrap the JSON in markdown code blocks
            - Do NOT add any commentary before or after the JSON
            - The output must be a pure JSON array that can be directly parsed by json.loads()
            - Each object must have exactly these fields: title, summarize, url, published_date, score, tickers

            URL AND TIMESTAMP REQUIREMENTS:
            - CRITICAL: You must use the EXACT same URLs that were provided above
            - Do NOT modify, change, or generate new URLs
            - The "url" field must be one of the URLs from the news data above
            - NEVER create fake or synthetic URLs
            - CRITICAL: Use the "published" timestamp from the news data above to calculate the correct published_date
            - Convert the Unix timestamp to YYYY-MM-DD HH:MM:SS format
            - Do NOT try to scrape or guess the publication date from web pages
            """,
            expected_output="""
            RETURN ONLY THIS EXACT FORMAT - NO OTHER TEXT:
            [
                {
                    "title": "Clear, descriptive headline",
                    "summarize": "Concise 2-3 sentence investment summary focusing on market impact only",
                    "url": "EXACT URL from the provided news data - DO NOT CHANGE OR GENERATE",
                    "published_date": "Convert the 'published' timestamp to YYYY-MM-DD HH:MM:SS format",
                    "score": "Integer from -10 to +10 representing market impact",
                    "tickers": ["List of affected stock symbols"]
                }
            ]

            CRITICAL:
            - Use the EXACT URLs provided in the task description
            - Do NOT create or modify URLs in any way
            - Return only the JSON array above. No explanations, no markdown, no additional text.
            """,
            output_pydantic=NewsAnalysisResult,
            agent=self.analyst_agent
        )

    def crew(self) -> Crew:
        # Get real news data with URLs and metadata
        real_news_data = self.get_real_news_data()

        if not real_news_data:
            logger.error("No real news data found!")
            return None

        logger.info(f"Found {len(real_news_data)} real news items for analysis")

        # Create analyze task with real news data
        analyze_task = self.create_analyze_task(real_news_data)

        return Crew(
            agents=[self.analyst_agent],
            tasks=[analyze_task],
            process=Process.sequential,
            verbose=True,
            output_log_file=False,  # Disable output logging to keep results clean
            max_iter=1  # Single iteration to avoid multiple attempts that can add noise
        )

if __name__ == "__main__":
    analysis = FinancialNewsAnalysis()
    crew = analysis.crew()
    if crew:
        result = crew.kickoff()
        print(result)
    else:
        print("Failed to create crew - no real URLs found")