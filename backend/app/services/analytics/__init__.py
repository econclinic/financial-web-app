"""Portfolio analytics engine.

Calculates portfolio performance metrics using normalized market data
from the market_data_service. This module never imports provider
modules directly.

Dependency flow: API → Analytics Layer → market_data_service → providers
"""
