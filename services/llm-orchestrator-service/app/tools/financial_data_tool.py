"""
Financial Data Lookup Tool

Uses Alpha Vantage API (free tier) for financial data verification.
Provides real-time and historical stock data, earnings, and financial metrics.

Related: ADR-018 (DIA-Planner & Verifier - Phase 2)
"""

import logging
import httpx
import time
from typing import Dict, Optional

# Import from project root models
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from models.verification_events import ToolExecutionResult
from app.core.config import settings

logger = logging.getLogger(__name__)


async def financial_data_lookup(
    company: str,
    metric: str,
    period: Optional[str] = None
) -> ToolExecutionResult:
    """
    Lookup financial data using Alpha Vantage API.

    Args:
        company: Company ticker symbol (e.g., "TSLA", "AAPL")
        metric: Metric to lookup:
                - "quote" - Current stock price and basic data
                - "earnings" - Quarterly/annual earnings reports
                - "income_statement" - Income statement data
                - "balance_sheet" - Balance sheet data
                - "cash_flow" - Cash flow statement
        period: Optional period specification:
                - For earnings: "Q1 2024", "Q3 2024", "annual"
                - Not required for "quote"

    Returns:
        ToolExecutionResult with:
        - result_data: Financial data from Alpha Vantage
        - source_citations: ["Alpha Vantage API", official source URLs]
        - confidence: 0.9 (high confidence for official financial data)

    Example:
        result = await financial_data_lookup(
            company="TSLA",
            metric="earnings",
            period="Q3 2024"
        )

    API Key:
        Requires ALPHA_VANTAGE_API_KEY in .env
        Free tier: 25 requests/day, 5 requests/minute
        Get key: https://www.alphavantage.co/support/#api-key
    """
    start_time = time.time()

    tool_params = {
        "company": company,
        "metric": metric,
        "period": period
    }

    try:
        logger.info(f"[FinancialData] Looking up {metric} for {company} ({period or 'latest'})")

        # Check API key
        api_key = settings.ALPHA_VANTAGE_API_KEY
        if not api_key:
            # Use demo key for testing (limited functionality)
            api_key = "demo"
            logger.warning("[FinancialData] Using demo API key (limited data)")

        # Build API request based on metric
        endpoint, params = _build_request(company, metric, api_key)

        # Make API call
        async with httpx.AsyncClient(timeout=settings.TOOL_TIMEOUT_SECONDS) as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

        # Check for API errors
        if "Error Message" in data:
            raise ValueError(f"Alpha Vantage error: {data['Error Message']}")

        if "Note" in data:
            # Rate limit message
            logger.warning(f"[FinancialData] API rate limit: {data['Note']}")
            raise ValueError("Alpha Vantage rate limit reached")

        # Parse response based on metric type
        parsed_data = _parse_response(data, metric, period)

        execution_time = int((time.time() - start_time) * 1000)

        # Build source citations
        source_citations = [
            "Alpha Vantage Financial Data API",
            f"https://www.alphavantage.co/query?function={params.get('function')}&symbol={company}"
        ]

        # Add company-specific sources
        if company.upper() == "TSLA":
            source_citations.append("https://ir.tesla.com")
        elif company.upper() == "AAPL":
            source_citations.append("https://investor.apple.com")

        logger.info(
            f"[FinancialData] Lookup completed in {execution_time}ms. "
            f"Metric: {metric}, Data points: {len(parsed_data)}"
        )

        return ToolExecutionResult(
            tool_name="financial_data_lookup",
            tool_parameters=tool_params,
            success=True,
            execution_time_ms=execution_time,
            result_data={
                "company": company.upper(),
                "metric": metric,
                "period": period,
                "data": parsed_data,
                "api_source": "Alpha Vantage"
            },
            source_citations=source_citations,
            confidence=0.9  # High confidence for official financial data
        )

    except httpx.HTTPStatusError as e:
        execution_time = int((time.time() - start_time) * 1000)
        error_msg = f"Alpha Vantage API error: {e.response.status_code}"
        logger.error(f"[FinancialData] {error_msg}")

        return ToolExecutionResult(
            tool_name="financial_data_lookup",
            tool_parameters=tool_params,
            success=False,
            execution_time_ms=execution_time,
            error_message=error_msg,
            source_citations=[],
            confidence=0.0
        )

    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        error_msg = f"Tool execution failed: {str(e)}"
        logger.error(f"[FinancialData] {error_msg}", exc_info=True)

        return ToolExecutionResult(
            tool_name="financial_data_lookup",
            tool_parameters=tool_params,
            success=False,
            execution_time_ms=execution_time,
            error_message=error_msg,
            source_citations=[],
            confidence=0.0
        )


def _build_request(company: str, metric: str, api_key: str) -> tuple[str, Dict]:
    """
    Build Alpha Vantage API request.

    Returns:
        Tuple of (endpoint_url, params_dict)
    """
    base_url = "https://www.alphavantage.co/query"

    # Map metric to Alpha Vantage function
    function_map = {
        "quote": "GLOBAL_QUOTE",
        "earnings": "EARNINGS",
        "income_statement": "INCOME_STATEMENT",
        "balance_sheet": "BALANCE_SHEET",
        "cash_flow": "CASH_FLOW"
    }

    function = function_map.get(metric)
    if not function:
        raise ValueError(f"Unknown metric: {metric}. Valid: {list(function_map.keys())}")

    params = {
        "function": function,
        "symbol": company.upper(),
        "apikey": api_key
    }

    return base_url, params


def _parse_response(data: Dict, metric: str, period: Optional[str]) -> Dict:
    """
    Parse Alpha Vantage response into standardized format.

    Args:
        data: Raw API response
        metric: Requested metric
        period: Optional period filter

    Returns:
        Parsed data dictionary
    """
    if metric == "quote":
        # Parse global quote
        quote_data = data.get("Global Quote", {})
        return {
            "symbol": quote_data.get("01. symbol"),
            "price": quote_data.get("05. price"),
            "change": quote_data.get("09. change"),
            "change_percent": quote_data.get("10. change percent"),
            "volume": quote_data.get("06. volume"),
            "latest_trading_day": quote_data.get("07. latest trading day")
        }

    elif metric == "earnings":
        # Parse earnings data
        quarterly_earnings = data.get("quarterlyEarnings", [])

        if period:
            # Filter for specific period (e.g., "Q3 2024")
            # Alpha Vantage uses format: "2024-09-30" for fiscal quarter end
            filtered = [
                e for e in quarterly_earnings
                if _matches_period(e.get("fiscalDateEnding"), period)
            ]
            earnings_data = filtered[0] if filtered else {}
        else:
            # Return latest quarter
            earnings_data = quarterly_earnings[0] if quarterly_earnings else {}

        return {
            "fiscal_date_ending": earnings_data.get("fiscalDateEnding"),
            "reported_eps": earnings_data.get("reportedEPS"),
            "estimated_eps": earnings_data.get("estimatedEPS"),
            "surprise": earnings_data.get("surprise"),
            "surprise_percentage": earnings_data.get("surprisePercentage"),
            "reported_date": earnings_data.get("reportedDate")
        }

    elif metric in ["income_statement", "balance_sheet", "cash_flow"]:
        # Parse financial statements (quarterly)
        quarterly_reports = data.get("quarterlyReports", [])

        if quarterly_reports:
            latest = quarterly_reports[0]
            return {
                "fiscal_date_ending": latest.get("fiscalDateEnding"),
                "reported_currency": latest.get("reportedCurrency"),
                **{k: v for k, v in latest.items() if k not in ["fiscalDateEnding", "reportedCurrency"]}
            }
        else:
            return {}

    else:
        # Return raw data for unknown metrics
        return data


def _matches_period(fiscal_date: str, period: str) -> bool:
    """
    Check if fiscal date matches requested period.

    Args:
        fiscal_date: Date string like "2024-09-30"
        period: Period like "Q3 2024" or "Q1 2024"

    Returns:
        True if matches
    """
    if not fiscal_date or not period:
        return False

    # Extract year and quarter from period
    period_upper = period.upper()

    if "Q1" in period_upper:
        quarter_months = ["03-31", "01-31", "02-28", "02-29"]
    elif "Q2" in period_upper:
        quarter_months = ["06-30", "04-30", "05-31"]
    elif "Q3" in period_upper:
        quarter_months = ["09-30", "07-31", "08-31"]
    elif "Q4" in period_upper:
        quarter_months = ["12-31", "10-31", "11-30"]
    else:
        return False

    # Check if fiscal date ends in matching quarter month
    return any(fiscal_date.endswith(month) for month in quarter_months)


# For testing
if __name__ == "__main__":
    import asyncio

    async def test_financial_lookup():
        """Test the financial data tool."""
        logging.basicConfig(level=logging.INFO)

        # Test 1: Current stock quote
        print("\nTest 1: Stock Quote")
        print("="*70)
        result1 = await financial_data_lookup(
            company="TSLA",
            metric="quote"
        )
        print(f"Success: {result1.success}")
        print(f"Data: {result1.result_data}")

        # Test 2: Earnings data
        print("\nTest 2: Earnings")
        print("="*70)
        result2 = await financial_data_lookup(
            company="TSLA",
            metric="earnings",
            period="Q3 2024"
        )
        print(f"Success: {result2.success}")
        print(f"Data: {result2.result_data}")

    asyncio.run(test_financial_lookup())
