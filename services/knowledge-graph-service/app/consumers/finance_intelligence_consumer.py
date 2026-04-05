"""
Finance Intelligence Event Consumer for Knowledge-Graph Service.

Listens for ALL finance.* events from FMP Service background jobs
and automatically syncs financial intelligence data to Neo4j.

Supported Events:
- finance.company.* (Company updates, market cap, employees, M&A)
- finance.executives.* (Executive changes)
- finance.sec.filing.new (SEC filings)
- finance.insider.trade.new (Insider trading)
- finance.financials.* (Financial statements, ratios, growth)
- finance.key_metrics.updated (TTM key metrics)
- finance.volatility.* (VIX, VVIX, MOVE)
- finance.indices.dxy.* (Dollar Index)
- finance.carry_trade.* (AUD/JPY)
- finance.treasury.yields.* (Treasury yields + spreads)
- finance.inflation.breakeven.* (Inflation expectations)
- finance.real_rates.* (TIPS yields)
- finance.correlation.* (Asset correlations from DCC-GARCH)
- finance.regime.* (Market regime state)
"""

import logging
import asyncio
from typing import Dict, Any, Optional
import aio_pika
from aio_pika import ExchangeType
from aio_pika.abc import AbstractIncomingMessage
import json
from datetime import datetime, date

from app.config import settings
from app.services.neo4j_service import neo4j_service
from app.services.cypher_validator import CypherSyntaxError

logger = logging.getLogger(__name__)


# Non-retriable errors - these should go to DLQ immediately
NON_RETRIABLE_ERRORS = (
    CypherSyntaxError,
    json.JSONDecodeError,
    KeyError,  # Missing required fields in event payload
    ValueError,  # Invalid data format
)


class FinanceIntelligenceConsumer:
    """
    RabbitMQ consumer for all finance.* events from FMP Service.

    Routing: finance.# (wildcard - matches all finance.* events)
    Queue: knowledge_graph_finance_intelligence
    Exchange: finance (Topic)
    """

    def __init__(self):
        """Initialize consumer."""
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None

        # Event handling statistics
        self.stats = {
            'total_processed': 0,
            'total_success': 0,
            'total_failed': 0,
            'by_event_type': {}
        }

    async def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            # Create robust connection (auto-reconnects)
            self.connection = await aio_pika.connect_robust(
                settings.rabbitmq_url,
                timeout=30
            )

            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            # Declare exchange (must match FMP Service exchange)
            self.exchange = await self.channel.declare_exchange(
                'finance',  # Same as FMP Service
                ExchangeType.TOPIC,
                durable=True
            )

            # Declare queue
            self.queue = await self.channel.declare_queue(
                'knowledge_graph_finance_intelligence',
                durable=True,
                arguments={
                    'x-dead-letter-exchange': 'finance.dlx',
                    'x-message-ttl': 86400000,  # 24 hours
                }
            )

            # Bind queue to exchange with wildcard routing key
            # finance.# matches ALL finance.* events
            await self.queue.bind(
                self.exchange,
                routing_key='finance.#'
            )

            logger.info("FinanceIntelligenceConsumer connected to RabbitMQ")
            logger.info("Listening on queue 'knowledge_graph_finance_intelligence'")
            logger.info("Routing key: 'finance.#' (wildcard - all finance events)")

        except Exception as e:
            logger.error(f"Failed to connect FinanceIntelligenceConsumer: {e}")
            raise

    async def start_consuming(self):
        """Start consuming messages."""
        if not self.queue:
            raise RuntimeError("Consumer not connected. Call connect() first.")

        await self.queue.consume(self._handle_message)
        logger.info("FinanceIntelligenceConsumer started consuming")

    async def disconnect(self):
        """Disconnect from RabbitMQ."""
        if self.connection:
            await self.connection.close()
            logger.info("FinanceIntelligenceConsumer disconnected from RabbitMQ")

    async def _handle_message(self, message: AbstractIncomingMessage):
        """
        Handle incoming finance event.

        Post-Incident #18: Improved error handling with distinction between
        retriable and non-retriable errors.
        """
        event_type = "unknown"
        symbol = "unknown"

        try:
            # Parse message body
            body = json.loads(message.body.decode())
            event_type = body.get("event_type", "unknown")
            symbol = body.get("symbol", "unknown")

            # INFO-level logging for production visibility
            records_count = body.get('records_count', body.get('count', 'N/A'))
            logger.info(f"📥 Received: {event_type} ({records_count} records)")
            logger.debug(f"Event payload: {body}")

            # Update statistics
            self.stats['total_processed'] += 1
            if event_type not in self.stats['by_event_type']:
                self.stats['by_event_type'][event_type] = {'success': 0, 'failed': 0}

            # Route to appropriate handler based on event type
            handler = self._get_handler(event_type)

            if handler:
                await handler(body)
                self.stats['total_success'] += 1
                self.stats['by_event_type'][event_type]['success'] += 1
                logger.info(f"✅ Processed: {event_type} (total: {self.stats['total_success']})")
            else:
                logger.warning(f"⚠️ No handler for event type: {event_type}")
                # Still acknowledge to prevent requeue loop

            # Acknowledge message
            await message.ack()

        except NON_RETRIABLE_ERRORS as e:
            # Non-retriable error - send to DLQ (reject without requeue)
            self.stats['total_failed'] += 1
            if event_type in self.stats['by_event_type']:
                self.stats['by_event_type'][event_type]['failed'] += 1

            logger.error(
                f"✗ Non-retriable error for {event_type} symbol={symbol}: "
                f"{type(e).__name__}: {e}",
                extra={
                    "event_type": event_type,
                    "symbol": symbol,
                    "error_type": type(e).__name__,
                    "retriable": False
                }
            )
            # Reject WITHOUT requeue → goes to DLQ
            await message.reject(requeue=False)

        except asyncio.TimeoutError:
            # Timeout - potentially retriable after backoff
            self.stats['total_failed'] += 1
            if event_type in self.stats['by_event_type']:
                self.stats['by_event_type'][event_type]['failed'] += 1

            logger.warning(
                f"⚠ Timeout for {event_type} symbol={symbol}",
                extra={
                    "event_type": event_type,
                    "symbol": symbol,
                    "retriable": True
                }
            )
            # Requeue for retry
            await message.reject(requeue=True)

        except Exception as e:
            # Unknown error - log details and requeue for retry
            self.stats['total_failed'] += 1
            if event_type in self.stats['by_event_type']:
                self.stats['by_event_type'][event_type]['failed'] += 1

            logger.error(
                f"✗ Unexpected error for {event_type} symbol={symbol}: "
                f"{type(e).__name__}: {e}",
                exc_info=True,
                extra={
                    "event_type": event_type,
                    "symbol": symbol,
                    "error_type": type(e).__name__,
                    "retriable": True
                }
            )
            # Requeue for retry (will go to DLX after max retries)
            await message.reject(requeue=True)

    def _get_handler(self, event_type: str):
        """
        Get handler function for event type.

        Args:
            event_type: Event type string (e.g., 'finance.company.updated')

        Returns:
            Handler function or None
        """
        # Map event types to handlers
        handler_map = {
            # ==========================================================
            # Company Intelligence Events
            # ==========================================================
            # Original names (backward compatibility)
            'finance.company.updated': self._handle_company_update,
            'finance.executives.updated': self._handle_executives_update,
            'finance.marketcap.updated': self._handle_marketcap_update,
            'finance.employees.updated': self._handle_employees_update,
            'finance.ma.new': self._handle_ma_event,

            # Actual FMP Service event names (from background jobs)
            'finance.company.profile.updated': self._handle_company_update,
            'finance.company.executives.updated': self._handle_executives_update,
            'finance.company.market_cap.updated': self._handle_marketcap_update,
            'finance.company.employees.updated': self._handle_employees_update,

            # ==========================================================
            # SEC & Insider Trading
            # ==========================================================
            'finance.sec.filing.new': self._handle_sec_filing,
            'finance.insider.trade.new': self._handle_insider_trade,

            # ==========================================================
            # Financial Statements
            # ==========================================================
            'finance.financials.income.updated': self._handle_financials,
            'finance.financials.balance.updated': self._handle_financials,
            'finance.financials.cashflow.updated': self._handle_financials,
            'finance.financials.ratios.updated': self._handle_financials,
            'finance.financials.growth.updated': self._handle_financials,

            # ==========================================================
            # Key Metrics
            # ==========================================================
            'finance.key_metrics.updated': self._handle_key_metrics,

            # ==========================================================
            # Market Indicators
            # ==========================================================
            'finance.volatility.updated': self._handle_volatility,
            'finance.indices.dxy.updated': self._handle_dxy,
            'finance.carry_trade.updated': self._handle_carry_trade,
            'finance.treasury.yields.updated': self._handle_treasury_yields,
            'finance.inflation.breakeven.updated': self._handle_inflation_breakeven,
            'finance.real_rates.updated': self._handle_real_rates,

            # ==========================================================
            # Correlations & Regime
            # ==========================================================
            'finance.correlation.updated': self._handle_correlation,
            'finance.regime.changed': self._handle_regime_change,
        }

        return handler_map.get(event_type)

    # ========================================================================
    # COMPANY INTELLIGENCE HANDLERS
    # ========================================================================

    async def _handle_company_update(self, event: Dict[str, Any]):
        """
        Handle finance.company.updated or finance.company.profile.updated event.

        Creates or updates Company node in Neo4j.

        Supports both formats:
        - Nested: {'symbol': 'AAPL', 'company_data': {'name': 'Apple', ...}}
        - Flat:   {'symbol': 'AAPL', 'company_name': 'Apple', 'sector': 'Tech', ...}
        """
        symbol = event.get('symbol')

        if not symbol:
            logger.warning("Missing symbol in company update event")
            return

        # Support both nested (legacy) and flat (FMP background jobs) format
        company_data = event.get('company_data', {})
        if not company_data:
            # Flat format from FMP background jobs
            company_data = event

        # Build Cypher query to MERGE Company node
        query = """
        MERGE (c:Company {symbol: $symbol})
        ON CREATE SET c.created_at = datetime()
        SET c.name = $name,
            c.cik = $cik,
            c.sector = $sector,
            c.industry = $industry,
            c.country = $country,
            c.exchange = $exchange,
            c.market_cap = $market_cap,
            c.employees = $employees,
            c.updated_at = datetime()
        RETURN c
        """

        params = {
            'symbol': symbol,
            # Support both 'name' and 'company_name' field names
            'name': company_data.get('name') or company_data.get('company_name'),
            'cik': company_data.get('cik'),
            'sector': company_data.get('sector'),
            'industry': company_data.get('industry'),
            'country': company_data.get('country'),
            'exchange': company_data.get('exchange'),
            'market_cap': company_data.get('market_cap'),
            'employees': company_data.get('employees'),
        }

        await neo4j_service.execute_write(query, params)
        logger.info(f"Updated Company node: {symbol}")

    async def _handle_executives_update(self, event: Dict[str, Any]):
        """
        Handle finance.executives.updated event.

        Creates Executive nodes and WORKS_FOR relationships.
        """
        symbol = event.get('symbol')
        executives_data = event.get('executives_data', [])

        if not symbol or not executives_data:
            return

        # Process each executive
        for exec_data in executives_data:
            query = """
            // Ensure Company exists
            MERGE (c:Company {symbol: $symbol})

            // Create or update Executive
            MERGE (e:Executive {name: $name, title: $title})
            ON CREATE SET e.created_at = datetime()
            SET e.age = $age,
                e.since_year = $since_year,
                e.pay_usd = $pay_usd,
                e.updated_at = datetime()

            // Create WORKS_FOR relationship
            MERGE (e)-[r:WORKS_FOR]->(c)
            ON CREATE SET r.created_at = datetime()
            SET r.title = $title,
                r.since_year = $since_year,
                r.pay_usd = $pay_usd,
                r.updated_at = datetime()

            RETURN e, r, c
            """

            params = {
                'symbol': symbol,
                'name': exec_data.get('name'),
                'title': exec_data.get('title'),
                'age': exec_data.get('age'),
                'since_year': exec_data.get('since'),
                'pay_usd': exec_data.get('pay'),
            }

            await neo4j_service.execute_write(query, params)

        logger.debug(f"Updated {len(executives_data)} executives for {symbol}")

    async def _handle_marketcap_update(self, event: Dict[str, Any]):
        """Handle finance.marketcap.updated event."""
        symbol = event.get('symbol')
        market_cap = event.get('market_cap')

        if not symbol or market_cap is None:
            return

        query = """
        MERGE (c:Company {symbol: $symbol})
        SET c.market_cap = $market_cap,
            c.updated_at = datetime()
        RETURN c
        """

        await neo4j_service.execute_write(query, {
            'symbol': symbol,
            'market_cap': market_cap
        })

    async def _handle_employees_update(self, event: Dict[str, Any]):
        """Handle finance.employees.updated event."""
        symbol = event.get('symbol')
        employee_count = event.get('employee_count')

        if not symbol or employee_count is None:
            return

        query = """
        MERGE (c:Company {symbol: $symbol})
        SET c.employee_count = $employee_count,
            c.updated_at = datetime()
        RETURN c
        """

        await neo4j_service.execute_write(query, {
            'symbol': symbol,
            'employee_count': employee_count
        })

    async def _handle_ma_event(self, event: Dict[str, Any]):
        """
        Handle finance.ma.new event.

        Creates MergerAcquisition node and ACQUIRED relationship.
        """
        acquiring_symbol = event.get('acquiring_symbol')
        target_symbol = event.get('target_symbol')
        ma_data = event.get('ma_data', {})

        if not acquiring_symbol or not target_symbol:
            return

        query = """
        // Ensure both companies exist
        MERGE (acquirer:Company {symbol: $acquiring_symbol})
        MERGE (target:Company {symbol: $target_symbol})

        // Create MergerAcquisition event node
        CREATE (ma:Event:MergerAcquisition {
            ma_id: $ma_id,
            acquiring_symbol: $acquiring_symbol,
            target_symbol: $target_symbol,
            target_name: $target_name,
            announcement_date: date($announcement_date),
            completion_date: date($completion_date),
            deal_value_usd: $deal_value_usd,
            deal_type: $deal_type,
            status: $status,
            created_at: datetime()
        })

        // Create ACQUIRED relationship
        CREATE (acquirer)-[r:ACQUIRED {
            announcement_date: date($announcement_date),
            completion_date: date($completion_date),
            deal_value_usd: $deal_value_usd,
            deal_type: $deal_type,
            status: $status,
            created_at: datetime()
        }]->(target)

        RETURN acquirer, ma, target, r
        """

        params = {
            'acquiring_symbol': acquiring_symbol,
            'target_symbol': target_symbol,
            'ma_id': ma_data.get('id'),
            'target_name': ma_data.get('target_name'),
            'announcement_date': ma_data.get('announcement_date'),
            'completion_date': ma_data.get('completion_date'),
            'deal_value_usd': ma_data.get('deal_value'),
            'deal_type': ma_data.get('deal_type'),
            'status': ma_data.get('status'),
        }

        await neo4j_service.execute_write(query, params)
        logger.debug(f"Created M&A event: {acquiring_symbol} → {target_symbol}")

    # ========================================================================
    # SEC & INSIDER TRADING HANDLERS
    # ========================================================================

    async def _handle_sec_filing(self, event: Dict[str, Any]):
        """
        Handle finance.sec.filing.new event.

        Creates SECFiling node and FILED relationship.
        """
        symbol = event.get('symbol')
        filing_data = event.get('filing_data', {})

        if not symbol:
            return

        query = """
        // Ensure Company exists
        MERGE (c:Company {symbol: $symbol})

        // Create SECFiling event node
        CREATE (f:Event:SECFiling {
            filing_id: $filing_id,
            symbol: $symbol,
            filing_type: $filing_type,
            filing_date: date($filing_date),
            report_date: date($report_date),
            accepted_date: datetime($accepted_date),
            filing_url: $filing_url,
            created_at: datetime()
        })

        // Create FILED relationship
        CREATE (c)-[r:FILED {
            filing_type: $filing_type,
            filing_date: date($filing_date),
            created_at: datetime()
        }]->(f)

        RETURN c, f, r
        """

        params = {
            'symbol': symbol,
            'filing_id': filing_data.get('id'),
            'filing_type': filing_data.get('type'),
            'filing_date': filing_data.get('filing_date'),
            'report_date': filing_data.get('report_date'),
            'accepted_date': filing_data.get('accepted_date'),
            'filing_url': filing_data.get('url'),
        }

        await neo4j_service.execute_write(query, params)
        logger.debug(f"Created SEC filing: {symbol} {filing_data.get('type')}")

    async def _handle_insider_trade(self, event: Dict[str, Any]):
        """
        Handle finance.insider.trade.new event.

        Creates InsiderTrade node, Executive node, and relationships.
        """
        symbol = event.get('symbol')
        trade_data = event.get('trade_data', {})

        if not symbol:
            return

        query = """
        // Ensure Company exists
        MERGE (c:Company {symbol: $symbol})

        // Create or update Executive (insider)
        MERGE (e:Executive {name: $insider_name})
        ON CREATE SET e.created_at = datetime()
        SET e.title = $insider_title,
            e.updated_at = datetime()

        // Create InsiderTrade event node
        CREATE (t:Event:InsiderTrade {
            trade_id: $trade_id,
            symbol: $symbol,
            filing_date: date($filing_date),
            transaction_date: date($transaction_date),
            insider_name: $insider_name,
            insider_title: $insider_title,
            transaction_type: $transaction_type,
            shares: $shares,
            price_per_share: $price_per_share,
            total_value: $total_value,
            shares_owned_after: $shares_owned_after,
            created_at: datetime()
        })

        // Create TRADES_IN relationship (Executive → Trade)
        CREATE (e)-[r1:TRADES_IN {
            transaction_type: $transaction_type,
            transaction_date: date($transaction_date),
            shares: $shares,
            price_per_share: $price_per_share,
            total_value: $total_value,
            created_at: datetime()
        }]->(t)

        // Create OF_COMPANY relationship (Trade → Company)
        CREATE (t)-[r2:OF_COMPANY]->(c)

        RETURN e, t, c, r1, r2
        """

        params = {
            'symbol': symbol,
            'trade_id': trade_data.get('id'),
            'filing_date': trade_data.get('filing_date'),
            'transaction_date': trade_data.get('transaction_date'),
            'insider_name': trade_data.get('insider_name'),
            'insider_title': trade_data.get('insider_title'),
            'transaction_type': trade_data.get('transaction_type'),
            'shares': trade_data.get('shares'),
            'price_per_share': trade_data.get('price'),
            'total_value': trade_data.get('value'),
            'shares_owned_after': trade_data.get('shares_owned_after'),
        }

        await neo4j_service.execute_write(query, params)
        logger.debug(f"Created insider trade: {trade_data.get('insider_name')} → {symbol}")

    # ========================================================================
    # FINANCIAL STATEMENTS & KEY METRICS HANDLERS
    # ========================================================================

    async def _handle_financials(self, event: Dict[str, Any]):
        """
        Handle finance.financials.* events.

        NOTE: FMP events contain only notification metadata (symbol, statement_type, count),
        NOT the actual financial data. To implement full Neo4j sync:
        - Option A: Modify FMP to include data in events (larger payloads)
        - Option B: Fetch data from FMP API when receiving notification

        Current behavior: Log and track for monitoring purposes.
        """
        symbol = event.get('symbol')
        statement_type = event.get('statement_type')  # 'income', 'balance', 'cashflow', 'ratios', 'growth'
        records_count = event.get('records_count', event.get('count', 0))

        # Track for metrics - useful for monitoring FMP data flow
        self.stats['financials_events'] = self.stats.get('financials_events', 0) + 1

        logger.info(f"📊 Financial notification: {symbol} {statement_type} ({records_count} records) - Data in FMP only")

    async def _handle_key_metrics(self, event: Dict[str, Any]):
        """
        Handle finance.key_metrics.updated event.

        NOTE: FMP events contain only notification metadata (symbol, count),
        NOT the actual metrics data (P/E, ROE, etc.). To implement full Neo4j sync:
        - Option A: Modify FMP to include metrics in events
        - Option B: Fetch data from FMP API when receiving notification

        Current behavior: Log and track for monitoring purposes.
        """
        symbol = event.get('symbol')
        records_count = event.get('records_count', event.get('count', 0))

        # Track for metrics - useful for monitoring FMP data flow
        self.stats['key_metrics_events'] = self.stats.get('key_metrics_events', 0) + 1

        logger.info(f"📈 Key metrics notification: {symbol} ({records_count} records) - Data in FMP only")

    # ========================================================================
    # MARKET INDICATORS HANDLERS
    # ========================================================================

    async def _handle_volatility(self, event: Dict[str, Any]):
        """
        Handle finance.volatility.updated event.

        Creates MarketIndicator nodes for VIX, VVIX, MOVE.
        """
        event_date = event.get('date')
        vix = event.get('vix')
        vvix = event.get('vvix')
        move = event.get('move')

        if not event_date:
            return

        # Create indicator nodes for each value
        indicators = []
        if vix is not None:
            indicators.append(('VIX', vix))
        if vvix is not None:
            indicators.append(('VVIX', vvix))
        if move is not None:
            indicators.append(('MOVE', move))

        for indicator_type, value in indicators:
            query = """
            CREATE (i:MarketIndicator {
                indicator_id: $indicator_id,
                indicator_type: $indicator_type,
                date: date($date),
                value: $value,
                created_at: datetime()
            })
            RETURN i
            """

            params = {
                'indicator_id': f"{indicator_type}_{event_date}",
                'indicator_type': indicator_type,
                'date': event_date,
                'value': value,
            }

            await neo4j_service.execute_write(query, params)

        logger.debug(f"Created {len(indicators)} volatility indicators for {event_date}")

    async def _handle_dxy(self, event: Dict[str, Any]):
        """Handle finance.indices.dxy.updated event."""
        event_date = event.get('date')
        dxy_value = event.get('dxy')

        if not event_date or dxy_value is None:
            return

        query = """
        CREATE (i:MarketIndicator {
            indicator_id: $indicator_id,
            indicator_type: 'DXY',
            date: date($date),
            value: $value,
            created_at: datetime()
        })
        RETURN i
        """

        await neo4j_service.execute_write(query, {
            'indicator_id': f"DXY_{event_date}",
            'date': event_date,
            'value': dxy_value,
        })

    async def _handle_carry_trade(self, event: Dict[str, Any]):
        """Handle finance.carry_trade.updated event."""
        event_date = event.get('date')
        audjpy_value = event.get('audjpy')

        if not event_date or audjpy_value is None:
            return

        query = """
        CREATE (i:MarketIndicator {
            indicator_id: $indicator_id,
            indicator_type: 'AUDJPY',
            date: date($date),
            value: $value,
            created_at: datetime()
        })
        RETURN i
        """

        await neo4j_service.execute_write(query, {
            'indicator_id': f"AUDJPY_{event_date}",
            'date': event_date,
            'value': audjpy_value,
        })

    async def _handle_treasury_yields(self, event: Dict[str, Any]):
        """
        Handle finance.treasury.yields.updated event.

        Creates MarketIndicator nodes for:
        - TREASURY_3M, TREASURY_2Y, TREASURY_10Y (yields)
        - SPREAD_10Y2Y, SPREAD_10Y3M (yield curve indicators)
        """
        yields = event.get('yields', [])
        if not yields:
            logger.warning("No yields data in event")
            return

        created_count = 0

        for yield_data in yields:
            date_str = yield_data.get('date')
            if not date_str:
                continue

            # Create indicator nodes for each maturity
            indicators = [
                ('TREASURY_3M', yield_data.get('yield_3m')),
                ('TREASURY_2Y', yield_data.get('yield_2y')),
                ('TREASURY_10Y', yield_data.get('yield_10y')),
                ('SPREAD_10Y2Y', yield_data.get('spread_10y2y')),
                ('SPREAD_10Y3M', yield_data.get('spread_10y3m'))
            ]

            for indicator_type, value in indicators:
                if value is None:
                    continue  # Skip if no data

                indicator_id = f"{indicator_type}_{date_str}"

                query = """
                MERGE (i:MarketIndicator {indicator_id: $indicator_id})
                SET i.indicator_type = $indicator_type,
                    i.date = date($date),
                    i.value = $value,
                    i.created_at = datetime()
                """

                try:
                    await neo4j_service.execute_write(query, {
                        'indicator_id': indicator_id,
                        'indicator_type': indicator_type,
                        'date': date_str,
                        'value': value
                    })
                    created_count += 1
                except Exception as e:
                    logger.error(f"Failed to create {indicator_type} indicator: {e}")

        logger.info(f"Created {created_count} treasury yield MarketIndicator nodes")

    async def _handle_inflation_breakeven(self, event: Dict[str, Any]):
        """
        Handle finance.inflation.breakeven.updated event.

        Creates MarketIndicator nodes for:
        - INFLATION_5Y (5-Year Breakeven Inflation Expectation)
        - INFLATION_10Y (10-Year Breakeven Inflation Expectation)
        """
        breakevens = event.get('breakevens', [])
        if not breakevens:
            logger.warning("No breakevens data in event")
            return

        created_count = 0

        for breakeven_data in breakevens:
            date_str = breakeven_data.get('date')
            if not date_str:
                continue

            # Create indicator nodes for each maturity
            indicators = [
                ('INFLATION_5Y', breakeven_data.get('t5yie')),
                ('INFLATION_10Y', breakeven_data.get('t10yie'))
            ]

            for indicator_type, value in indicators:
                if value is None:
                    continue  # Skip if no data

                indicator_id = f"{indicator_type}_{date_str}"

                query = """
                MERGE (i:MarketIndicator {indicator_id: $indicator_id})
                SET i.indicator_type = $indicator_type,
                    i.date = date($date),
                    i.value = $value,
                    i.created_at = datetime()
                """

                try:
                    await neo4j_service.execute_write(query, {
                        'indicator_id': indicator_id,
                        'indicator_type': indicator_type,
                        'date': date_str,
                        'value': value
                    })
                    created_count += 1
                except Exception as e:
                    logger.error(f"Failed to create {indicator_type} indicator: {e}")

        logger.info(f"Created {created_count} inflation breakeven MarketIndicator nodes")

    async def _handle_real_rates(self, event: Dict[str, Any]):
        """
        Handle finance.real_rates.updated event.

        Creates MarketIndicator nodes for:
        - TIPS_10Y (10-Year Treasury Inflation-Protected Securities)
        """
        real_rates = event.get('real_rates', [])
        if not real_rates:
            logger.warning("No real_rates data in event")
            return

        created_count = 0

        for real_rate_data in real_rates:
            date_str = real_rate_data.get('date')
            tips_10y = real_rate_data.get('tips_10y')

            if not date_str or tips_10y is None:
                continue  # Skip if no data

            indicator_id = f"TIPS_10Y_{date_str}"

            query = """
            MERGE (i:MarketIndicator {indicator_id: $indicator_id})
            SET i.indicator_type = $indicator_type,
                i.date = date($date),
                i.value = $value,
                i.created_at = datetime()
            """

            try:
                await neo4j_service.execute_write(query, {
                    'indicator_id': indicator_id,
                    'indicator_type': 'TIPS_10Y',
                    'date': date_str,
                    'value': tips_10y
                })
                created_count += 1
            except Exception as e:
                logger.error(f"Failed to create TIPS_10Y indicator: {e}")

        logger.info(f"Created {created_count} TIPS MarketIndicator nodes")

    # ========================================================================
    # CORRELATION & REGIME HANDLERS
    # ========================================================================

    async def _handle_correlation(self, event: Dict[str, Any]):
        """
        Handle finance.correlation.updated event.

        NOTE: FMP events contain only notification metadata (date, pairs_count),
        NOT the actual correlation pairs. Full implementation would require:
        - Option A: Modify FMP to include correlation matrix in events (large payload: 50+ pairs)
        - Option B: Fetch correlation data from FMP API when receiving notification
        - Option C: Direct database sync (bypass RabbitMQ for bulk data)

        Current behavior: Log and track for monitoring purposes.
        """
        calculation_date = event.get('calculation_date') or event.get('date')
        pairs_count = event.get('pairs_count', event.get('count', 0))

        # Track for metrics - useful for monitoring FMP data flow
        self.stats['correlation_events'] = self.stats.get('correlation_events', 0) + 1

        logger.info(f"🔗 Correlation notification: {calculation_date} ({pairs_count} pairs) - Data in FMP only")

    async def _handle_regime_change(self, event: Dict[str, Any]):
        """
        Handle finance.regime.changed event.

        Creates MarketRegime node.
        """
        event_date = event.get('date')
        regime_type = event.get('regime_type')
        regime_score = event.get('regime_score')
        signals = event.get('signals', {})

        if not event_date or not regime_type:
            return

        query = """
        MERGE (r:MarketRegime {date: date($date)})
        ON CREATE SET r.created_at = datetime()
        SET r.regime_type = $regime_type,
            r.regime_score = $regime_score,
            r.vix_signal = $vix_signal,
            r.correlation_signal = $correlation_signal,
            r.yield_curve_signal = $yield_curve_signal,
            r.dxy_signal = $dxy_signal,
            r.carry_trade_signal = $carry_trade_signal,
            r.updated_at = datetime()
        RETURN r
        """

        params = {
            'date': event_date,
            'regime_type': regime_type,
            'regime_score': regime_score,
            'vix_signal': signals.get('vix'),
            'correlation_signal': signals.get('correlation'),
            'yield_curve_signal': signals.get('yield_curve'),
            'dxy_signal': signals.get('dxy'),
            'carry_trade_signal': signals.get('carry'),
        }

        await neo4j_service.execute_write(query, params)
        logger.debug(f"Created market regime: {regime_type} for {event_date}")

    def get_stats(self) -> Dict[str, Any]:
        """Get consumer statistics."""
        return {
            **self.stats,
            'is_connected': self.connection is not None and not self.connection.is_closed
        }


# Global instance
_finance_intelligence_consumer: Optional[FinanceIntelligenceConsumer] = None


async def get_finance_intelligence_consumer() -> FinanceIntelligenceConsumer:
    """Get or create global finance intelligence consumer instance."""
    global _finance_intelligence_consumer
    if _finance_intelligence_consumer is None:
        _finance_intelligence_consumer = FinanceIntelligenceConsumer()
        await _finance_intelligence_consumer.connect()
    return _finance_intelligence_consumer


async def close_finance_intelligence_consumer():
    """Close global finance intelligence consumer."""
    global _finance_intelligence_consumer
    if _finance_intelligence_consumer:
        await _finance_intelligence_consumer.disconnect()
        _finance_intelligence_consumer = None
