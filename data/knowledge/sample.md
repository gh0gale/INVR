# Financial RAG Knowledge Database: Core Concepts

This directory contains markdown files that act as the seed data for the Vector Database. The `rag_service` reads these files, generates embeddings, and uses them to answer user questions contextually.

When users ask "Why does this matter?" the agent retrieves segments from these files.

## Concept: Price-to-Earnings Ratio (P/E)
The P/E ratio measures a company's current share price relative to its per-share earnings. 
*   **High P/E:** May signify the stock is overvalued, or that investors are expecting high growth rates in the future.
*   **Low P/E:** Might indicate that the current stock price is undervalued, or that the company is performing exceptionally well relative to its past trends.
*   **Context for AI Agent:** Never evaluate P/E in a vacuum. A tech company might have a standard P/E of 35, while a high-street bank might have a standard P/E of 8. Always compare against the sector median.

## Concept: Relative Strength Index (RSI)
RSI is a momentum oscillator that measures the speed and change of price movements. RSI oscillates between zero and 100.
*   Traditionally, an RSI > 70 indicates that an asset is becoming overvalued or overbought, and may be primed for a trend reversal or corrective pullback.
*   An RSI < 30 indicates an oversold or undervalued condition.
*   **Context for AI Agent:** Stocks can remain overbought for a long time during strong bull markets. Use RSI as a confirmation tool, not a sole trigger.

*Add more definitions here over time. For example: Fibonacci Retracements, Free Cash Flow Yield, Nifty50 Beta, etc.*
