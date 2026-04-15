from enum import Enum

class IncomeBracket(str, Enum):
    BELOW_5L = "<5L"
    FROM_5L_TO_10L = "5L-10L"
    FROM_10L_TO_25L = "10L-25L"
    ABOVE_25L = ">25L"

class RiskAppetite(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class PrimaryGoal(str, Enum):
    WEALTH_CREATION = "wealth_creation"
    RETIREMENT = "retirement"
    CHILD_EDUCATION = "child_education"
    SHORT_TERM_GROWTH = "short_term_growth"
    DIVIDEND_INCOME = "dividend_income"
    PORTFOLIO_DIVERSIFICATION = "portfolio_diversification"

class ProficiencyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class InvestmentHorizon(str, Enum):
    INTRADAY = "intraday"
    SWING = "swing"
    POSITIONAL = "positional"
    LONG_TERM = "long_term"
