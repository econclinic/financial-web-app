"""Provider adapter layer for external market data sources.

All external API communication is isolated in this package.
Each provider implements a common Protocol defined in base.py,
producing normalized internal types defined in types.py.

Symbol routing is handled by registry.py, which maps symbols
to their responsible provider adapter.
"""
