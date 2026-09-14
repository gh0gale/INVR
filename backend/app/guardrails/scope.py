"""Is a tutor message within the tutor's remit? (audit OBS-02)

The tutor used to decide this itself, from its system prompt, so the boundary
was a tendency: it refused a cookie recipe and wrote a haiku. Asked how the
app is built, it confidently invented InfluxDB, Flask and tables that do not
exist. This module makes the decision before generation, outside the model
that answers, in three layers:

1. **Patterns** for questions about the system itself (architecture, code,
   database, prompts, model, the engine's thresholds). A rule, not judgement.
2. **Pleasantries** ("hi", "thanks") and messages in plain market vocabulary
   or naming the stock on screen are in scope without asking anyone.
3. **A binary classifier** (`Task.SCOPE`, temperature 0, one word) for the
   rest. It is not the tutor, so it cannot talk itself into helping.

An embedding-centroid gate was measured first and rejected: on a 40-message
labelled set it managed 33 correct at best, refusing "hi" while answering
questions about cricket and politics. Rules plus the classifier scored 45 of
47 and gave identical answers on a repeat run; both misses are fixed here.

A classifier failure fails **open**. This is a scope control, not a security
control: the injection guardrail runs first and fails closed, and the tutor
prompt still carries the same scope clause as a second line.
"""
import logging
import re
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm import Task, get_chat_model, message_text

logger = logging.getLogger(__name__)

INTERNALS_PATTERNS = [re.compile(p, re.I) for p in [
    r"\bsystem\s+prompt\b",
    r"\bsource\s+code\b",
    r"\b(gold|silver|bronze)\s+layer\b",
    r"\bmedallion\b",
    r"\b(your|this|the)\s+(app|application|system|platform|engine|tool|assistant|bot|website|site)('?s)?\s+"
    r"(architecture|code|codebase|database|db|tables?|schema|framework|stack|tech|backend|prompt|"
    r"thresholds?|rules|logic|algorithm|config(uration)?|model)\b",
    r"\b(architecture|database|tables?|framework|tech\s+stack|programming\s+language|codebase)\b.*\b(this|your)\s+"
    r"(app|application|system|platform|site|tool)\b",
    r"\b(this|your)\s+(app|application|system|platform|site|tool)\b.*\b(built|made|coded|written|architect)",
    r"\bhow\s+(was|is)\s+(this|the)\s+(app|application|system|platform|tool|site)\s+(built|made|coded|designed)\b",
    r"\b(programming\s+language|framework|tech\s+stack|architecture|database)\b.*\b(built\s+with|written\s+in|coded\s+in|runs?\s+on)\b",
    r"\b(is\s+)?this\s+(built|made|written|coded)\s+(with|in|on|using)\b",
    r"\b(what|which)\s+(ai|llm|language)?\s*model\s+(are\s+you|do\s+you|is\s+this|powers|runs)",
    r"\bwhat\s+model\s+are\s+you\b",
    r"\b(your|the\s+engine'?s?|the\s+system'?s?)\s+(exact\s+)?(gate\s+)?thresholds\b",
    r"\bthresholds?\b.*\b(your|this)\s+(engine|system|app|application|model|algorithm)\b",
    r"\bgate\s+thresholds?\b",
    r"\bwhich\s+database\b",
]]

# Market vocabulary that makes a message in scope without asking a model. Added
# after the live check refused "What should I watch before buying?": a false
# refusal of a real question is the worse failure, so anything plainly about
# markets skips the classifier. Deliberately excludes words with common
# non-financial senses ("capital" of a country, weight "loss", a "return"
# policy): those go to the classifier instead.
FINANCE_TERMS = re.compile(
    r"\b(stocks?|shares?|equit(y|ies)|markets?|nifty|sensex|bse|nse|invest\w*|portfolio|trad(e|es|ing|er)|"
    r"buy\w*|sell\w*|prices?|valuation|dividends?|sip|mutual\s+funds?|etfs?|bonds?|profit\w*|"
    r"stop[-\s]?loss|capital\s+gains?|risk\w*|verdict|analysis|targets?|entry|exit|rsi|sma|dma|ema|atr|macd|"
    r"p/?e|eps|roe|cagr|fcf|volume|trend\w*|breakout|support|resistance|sectors?|rall(y|ies)|bull\w*|bear\w*|"
    r"inflation|interest\s+rates?|rbi|gdp|ltcg|stcg|overbought|oversold|moving\s+average|circuit|"
    r"allocation|hedg\w*|volatil\w*|drawdown|earnings|revenue|debt|margin\w*)\b",
    re.I,
)

_PLEASANTRY_WORDS = {
    "hi", "hii", "hello", "hey", "namaste", "thanks", "thank", "thx", "ok", "okay",
    "cool", "great", "nice", "good", "got",
}

CLASSIFIER_PROMPT = """You screen messages sent to the tutor inside a stock-analysis app for Indian equities.
The user is looking at an analysis of {ticker}.

Answer IN if the message is about any of: stocks, markets, investing, trading, personal finance,
the economy, financial terms or indicators, the user's portfolio or risk, or the analysis on screen.
Short follow-ups ("why?", "and the risk?"), greetings and thanks are also IN.

Answer OUT for everything else: jokes, poems, stories, recipes, travel, weather, sports, movies,
celebrities, politics, general knowledge, homework, translation, or writing code.

If earlier turns of the conversation are shown, judge the message as a
follow-up to them: a question about something said earlier in an on-topic
conversation is IN.

Examples:
"What should I watch before buying?" -> IN
"Is now a good time to enter?" -> IN
"Explain that again more simply" -> IN
"Write a poem about the sea" -> OUT
"Who won the match yesterday?" -> OUT

Reply with exactly one word: IN or OUT."""

REFUSALS = {
    "off_topic": (
        "I can only help with markets, investing and the analysis on your screen. "
        "Ask me about {ticker}'s verdict, a metric in the report, or what to watch next."
    ),
    "internals": (
        "I can't share how INVR is built or configured. "
        "I can explain what the analysis of {ticker} means and which figures drove it."
    ),
}


def is_internals_question(message: str) -> bool:
    return any(p.search(message) for p in INTERNALS_PATTERNS)


def is_pleasantry(message: str) -> bool:
    words = re.findall(r"[a-z]+", message.lower())
    return 0 < len(words) <= 3 and words[0] in _PLEASANTRY_WORDS


def mentions_finance(message: str, ticker: Optional[str] = None) -> bool:
    """Plainly about markets, or names the stock on screen."""
    if FINANCE_TERMS.search(message):
        return True
    base = (ticker or "").split(".")[0].lower()
    return bool(base) and base in re.findall(r"[a-z0-9&]+", message.lower())


HISTORY_TURNS = 2
HISTORY_CHARS = 300


def _history_block(history: Optional[List[str]]) -> str:
    """The last few turns, trimmed. A follow-up is only judgeable in context:
    without it, "How much did I say I'd invest?" read as off-topic (found by
    e2e_verify on the first hosted run)."""
    turns = [t.strip()[:HISTORY_CHARS] for t in (history or []) if t and t.strip()][-HISTORY_TURNS:]
    if not turns:
        return ""
    return "\n\nEarlier in this conversation:\n" + "\n".join(f"- {t}" for t in turns)


async def classify_with_model(message: str, ticker: str, history: Optional[List[str]] = None) -> Optional[str]:
    """'in', 'out', or None when the reply was neither."""
    model = get_chat_model(Task.SCOPE)
    reply = await model.ainvoke([
        SystemMessage(content=CLASSIFIER_PROMPT.format(ticker=ticker or "a stock") + _history_block(history)),
        HumanMessage(content=message),
    ])
    text = message_text(reply).strip().upper()
    if text.startswith("OUT"):
        return "out"
    if text.startswith("IN"):
        return "in"
    return None


async def assess_scope(message: str, ticker: Optional[str] = None, history: Optional[List[str]] = None) -> str:
    """'in', 'off_topic' or 'internals'. `history` is prior turns' text, oldest first."""
    text = (message or "").strip()
    if not text:
        return "in"
    if is_internals_question(text):
        return "internals"
    if is_pleasantry(text) or mentions_finance(text, ticker):
        return "in"
    try:
        verdict = await classify_with_model(text, ticker or "", history)
    except Exception as e:  # noqa: BLE001 - fail open, see module docstring
        logger.warning("Scope classifier unavailable (%s). Allowing the message.", e)
        return "in"
    return "off_topic" if verdict == "out" else "in"


def refusal_for(mode: str, ticker: Optional[str]) -> str:
    return REFUSALS[mode].format(ticker=ticker or "this stock")
