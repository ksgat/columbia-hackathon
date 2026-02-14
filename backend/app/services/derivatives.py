"""
Derivative and advanced trading strategies
(Re-export from chains.py for backward compatibility)
"""
from app.services.chains import (
    ChainService,
    DerivativeService,
    get_chain_service,
    get_derivative_service
)

__all__ = [
    "ChainService",
    "DerivativeService",
    "get_chain_service",
    "get_derivative_service"
]
