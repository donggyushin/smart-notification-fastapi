import os
from datetime import datetime, timedelta
import requests
import feedparser
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from firecrawl import FirecrawlApp

# Load environment variables
load_dotenv()

# Initialize OpenAI LLM (GPT-4o)
llm = ChatOpenAI(
    model="gpt-4o",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.1
)

# Initialize Firecrawl
firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

def collect_comprehensive_news():
    """Enhanced news collection with both RSS and web scraping"""
    news_sources = {
        "rss": [
            "https://feeds.finance.yahoo.com/rss/2.0/headline",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "https://feeds.marketwatch.com/marketwatch/StockstoWatch/",
            "https://feeds.finance.yahoo.com/rss/2.0/category-stocks",
        ],
        "web": [
            "https://www.marketwatch.com/latest-news",
            "https://finance.yahoo.com/news/",
            "https://www.cnbc.com/markets/",
        ]
    }
    
    collected_news = []
    current_time = datetime.now()
    cutoff_time = current_time - timedelta(hours=8)  # Last 8 hours
    
    print("📡 Collecting from RSS sources...")
    # RSS Sources
    for source in news_sources["rss"]:
        try:
            print(f"  🔍 {source}")
            feed = feedparser.parse(source)
            
            for entry in feed.entries[:15]:  # Top 15 articles
                try:
                    pub_date = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') and entry.published_parsed else current_time
                except:
                    pub_date = current_time
                
                if pub_date > cutoff_time:
                    collected_news.append({
                        'title': getattr(entry, 'title', 'No title'),
                        'link': getattr(entry, 'link', 'No link'),
                        'published': pub_date.isoformat(),
                        'source': source,
                        'summary': getattr(entry, 'summary', '')[:400],
                        'type': 'rss'
                    })
        except Exception as e:
            print(f"    ❌ RSS Error: {e}")
            continue
    
    print("🌐 Collecting from web sources...")
    # Web Sources using Firecrawl
    for source in news_sources["web"]:
        try:
            print(f"  🔍 {source}")
            scrape_result = firecrawl.scrape(
                url=source,
                formats=["markdown"],
                only_main_content=True,
                wait_for=2000
            )
            
            if hasattr(scrape_result, 'markdown') and scrape_result.markdown:
                content = scrape_result.markdown[:3000]  # Limit content
                
                # Extract potential news from scraped content
                lines = content.split('\n')
                headlines = [line.strip() for line in lines 
                           if len(line.strip()) > 20 and len(line.strip()) < 200 
                           and any(keyword in line.lower() for keyword in 
                                 ['stock', 'market', 'earnings', 'price', 'shares', 'trading', 'nasdaq', 'dow', 'sp500', 'revenue'])]
                
                for headline in headlines[:5]:  # Max 5 headlines per source
                    collected_news.append({
                        'title': headline,
                        'content': headline,
                        'link': source,
                        'published': current_time.isoformat(),
                        'source': source,
                        'summary': headline[:200],
                        'type': 'web'
                    })
        except Exception as e:
            print(f"    ❌ Web scraping error for {source}: {e}")
            continue
    
    # Remove duplicates and sort by relevance
    unique_news = []
    seen_titles = set()
    
    for article in collected_news:
        title_key = article['title'].lower()[:50]  # Use first 50 chars as key
        if title_key not in seen_titles and any(keyword in title_key for keyword in 
            ['stock', 'market', 'earnings', 'price', 'shares', 'trading', 'nasdaq', 'dow', 'revenue', 'profit']):
            seen_titles.add(title_key)
            unique_news.append(article)
    
    print(f"✅ Collected {len(unique_news)} unique relevant articles")
    return unique_news

# Define Enhanced Agents
news_collector = Agent(
    role='Advanced US Stock News Collector',
    goal='Collect comprehensive US stock market news from multiple sources including RSS feeds and web scraping',
    backstory="""You are a sophisticated financial news aggregator with advanced capabilities to collect news from 
    both traditional RSS feeds and modern web sources. You have access to Yahoo Finance, CNBC, MarketWatch, and other 
    major financial news platforms. You specialize in identifying market-moving events, earnings reports, and 
    regulatory developments that impact US equity markets.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

news_evaluator = Agent(
    role='Senior Market Impact Evaluator',
    goal='Provide deep analysis of news impact on US stock markets with quantitative scoring',
    backstory="""You are a senior quantitative analyst with 25+ years of experience in equity research at top-tier 
    investment banks. You have witnessed multiple market cycles and understand how different types of news impact 
    various sectors. You excel at identifying catalysts that move markets and can accurately predict the magnitude 
    and duration of price impacts. Your analysis is trusted by institutional investors and hedge funds.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

impact_filter = Agent(
    role='Elite High-Impact News Filter',
    goal='Select only the most market-moving news with surgical precision',
    backstory="""You are an elite quantitative researcher at a top hedge fund specializing in event-driven strategies. 
    You have access to historical market data and understand exactly which types of news events historically cause 
    significant price movements. Your filtering criteria are based on backtested strategies that have generated 
    consistent alpha. You focus on events that create tradeable opportunities for institutional investors.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

data_formatter = Agent(
    role='Financial Data Engineering Specialist',
    goal='Create production-ready structured data for algorithmic trading systems',
    backstory="""You are a senior data engineer at a quantitative trading firm specializing in alternative data 
    processing. You understand the exact data structures needed for high-frequency trading systems, portfolio 
    management platforms, and risk management tools. Your structured data feeds directly into trading algorithms 
    and must be precise, consistent, and machine-readable.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

def run_enhanced_news_analysis():
    """Run enhanced news analysis with comprehensive data collection"""
    print("🚀 Starting Enhanced US Stock News Analysis System...")
    print("=" * 70)
    
    # Step 1: Comprehensive News Collection
    print("\n📡 PHASE 1: Comprehensive News Collection...")
    raw_news = collect_comprehensive_news()
    
    if not raw_news:
        print("❌ No news collected. Exiting...")
        return None
    
    # Format news for LLM processing
    formatted_news = "\n\n".join([
        f"ARTICLE {i+1}:\nTitle: {article.get('title', 'No title')}\nLink: {article.get('link', 'No link')}\nPublished: {article.get('published', 'Unknown')}\nSummary: {article.get('summary', 'No summary')}\nSource: {article.get('source', 'Unknown')}\nType: {article.get('type', 'unknown')}"
        for i, article in enumerate(raw_news[:25])  # Limit to 25 most relevant
    ])
    
    news_input = f"COLLECTED {len(raw_news)} RECENT US STOCK NEWS ARTICLES FROM MULTIPLE SOURCES:\n\n{formatted_news}"
    
    # Define Enhanced Tasks
    collect_task = Task(
        description=f"""COMPREHENSIVE NEWS REVIEW:

{news_input}

Analyze and organize these articles focusing on:
1. US stock market relevance
2. Breaking news and market updates  
3. Earnings announcements and guidance
4. Regulatory developments and FDA approvals
5. Economic indicators affecting markets
6. Corporate actions and M&A activity
7. Analyst upgrades/downgrades

Prioritize articles that directly impact publicly traded US companies.""",
        agent=news_collector,
        expected_output="Organized list of US stock market relevant articles with clear market connection analysis."
    )

    evaluate_task = Task(
        description="""QUANTITATIVE IMPACT ANALYSIS:

For each relevant article, provide detailed analysis:

1. **Impact Score** (1-10): 
   - 1-3: Minimal impact (routine news)
   - 4-6: Moderate impact (sector-specific)
   - 7-8: High impact (market-moving)
   - 9-10: Extreme impact (market-wide event)

2. **Affected Assets**:
   - Specific tickers (use exact symbols)
   - Market sectors
   - Asset classes (equities, bonds, commodities)

3. **Impact Timeline**:
   - Immediate (within hours)
   - Short-term (1-5 days) 
   - Medium-term (1-4 weeks)
   - Long-term (1+ months)

4. **Price Impact Estimate**: Expected percentage move
5. **Volume Impact**: Expected trading volume increase
6. **Confidence Level**: Statistical confidence in assessment
7. **Historical Context**: Similar past events and outcomes

Consider market cap, liquidity, current sentiment, and volatility.""",
        agent=news_evaluator,
        expected_output="Detailed quantitative impact analysis for each article with scoring, targets, and timing."
    )

    filter_task = Task(
        description="""HIGH-IMPACT FILTERING:

Apply strict criteria to select only the most actionable news:

**INCLUSION CRITERIA:**
- Impact Score >= 7 OR
- Affects stocks with market cap > $10B OR  
- Expected price movement > 3% OR
- High confidence + sector-wide impact

**MANDATORY REQUIREMENTS:**
- Clear catalyst identification
- Quantifiable impact potential
- Tradeable within 1-5 days
- Affects liquid securities

**EXCLUSION CRITERIA:**
- Routine earnings meeting estimates
- Minor corporate housekeeping
- Unverified rumors or speculation
- Penny stock news
- General market commentary

Provide detailed justification for each selected article.""",
        agent=impact_filter,
        expected_output="Curated list of high-impact, actionable news with detailed selection rationale."
    )

    format_task = Task(
        description="""PRODUCTION DATA FORMATTING:

Create institutional-grade structured data for each selected article:

```json
{
    "id": "unique_hash_identifier",
    "title": "exact_article_title", 
    "url": "source_url",
    "published_date": "ISO_8601_datetime",
    "source": "news_source_name",
    "summary": "concise_summary_max_200_chars",
    "impact_score": integer_1_to_10,
    "affected_tickers": ["AAPL", "MSFT"],  // exact symbols
    "affected_sectors": ["Technology", "Healthcare"], 
    "market_cap_exposure": "large|mid|small|mixed",
    "impact_timeframe": "immediate|short-term|medium-term|long-term",
    "expected_price_move": "+/-X.X%",
    "expected_volume_increase": "X.Xx multiplier",
    "impact_reasoning": "detailed_catalyst_explanation",
    "confidence_level": "High|Medium|Low",
    "confidence_score": 0.XX,  // decimal 0-1
    "keywords": ["earnings", "FDA", "merger"],
    "event_category": "earnings|regulatory|ma|guidance|economic",
    "trading_strategy": "suggested_approach",
    "risk_factors": ["key", "risks"],
    "created_at": "current_ISO_8601_datetime",
    "analyst_notes": "additional_context"
}
```

Return valid JSON array only.""",
        agent=data_formatter,
        expected_output="Production-ready JSON array for institutional trading systems."
    )

    # Create Enhanced Crew
    crew = Crew(
        agents=[news_collector, news_evaluator, impact_filter, data_formatter],
        tasks=[collect_task, evaluate_task, filter_task, format_task],
        process=Process.sequential,
        verbose=True
    )
    
    try:
        print("\n🤖 PHASE 2-5: AI Analysis Pipeline...")
        result = crew.kickoff()
        print("\n" + "=" * 70)
        print("✅ Enhanced Analysis Complete!")
        print("=" * 70)
        return result
    except Exception as e:
        print(f"❌ Error running enhanced crew: {e}")
        return None

if __name__ == "__main__":
    result = run_enhanced_news_analysis()
    if result:
        print(f"\n📊 FINAL STRUCTURED RESULT:\n{result}")
        
        # Enhanced file saving
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Clean and parse JSON
            result_str = str(result).strip()
            if "```json" in result_str:
                # Extract JSON from markdown code block
                start = result_str.find("```json") + 7
                end = result_str.find("```", start)
                json_str = result_str[start:end].strip()
            else:
                json_str = result_str
            
            # Try to parse as JSON
            if json_str.startswith('[') and json_str.endswith(']'):
                parsed_result = json.loads(json_str)
                
                # Save structured JSON
                filename = f"enhanced_news_analysis_{timestamp}.json"
                with open(filename, 'w') as f:
                    json.dump(parsed_result, f, indent=2)
                
                print(f"\n💾 Structured data saved: {filename}")
                print(f"📈 Found {len(parsed_result)} high-impact news items")
                
                # Print summary
                if parsed_result:
                    print("\n🎯 SUMMARY:")
                    for item in parsed_result:
                        print(f"  • {item.get('title', 'N/A')[:60]}...")
                        print(f"    Impact: {item.get('impact_score', 'N/A')}/10 | Confidence: {item.get('confidence_level', 'N/A')}")
                        print(f"    Tickers: {', '.join(item.get('affected_tickers', [])[:3])}")
            else:
                # Save as text if not valid JSON
                with open(f"enhanced_news_analysis_{timestamp}.txt", 'w') as f:
                    f.write(str(result))
                print(f"\n💾 Results saved as text: enhanced_news_analysis_{timestamp}.txt")
                
        except Exception as e:
            print(f"❌ Error processing results: {e}")
            # Fallback: save raw result
            with open(f"raw_news_result_{timestamp}.txt", 'w') as f:
                f.write(str(result))
            print(f"💾 Raw results saved: raw_news_result_{timestamp}.txt")
    else:
        print("❌ No results to save")