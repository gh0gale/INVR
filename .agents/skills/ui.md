---
name: ui-component-generator
description: >
  Generates production-ready UI components for the AI Investment Intelligence platform.
  Use whenever building any screen, component, form, card, modal, chart, or interactive
  element. This project uses React 18 + TypeScript + Tailwind CSS + Recharts.
  Triggers on: "build a screen", "create a component", "make a form", "add a modal",
  "dashboard for X", "chart for Y", "UI for Z", "design the [screen name]".
  CRITICAL: Also triggers when building the disclaimer banner, scorecard cards,
  risk gauge, sector allocation chart, or any financial data display component.
---

# UI Component Generator — Investment Intelligence Platform

## Before Writing Any Component

Answer these first:
- Which user type sees this? (Beginner / Intermediate / Privacy-conscious)
- What financial data does it display? (list the exact fields from the backend schema)
- What actions can the user take? (list events)
- What are the loading, empty, and error states?
- Does this screen display investment analysis or recommendations? → MUST include disclaimer

## Every Component Must Have

1. Typed props interface (TypeScript)
2. Loading state — `<LoadingSpinner />`, never render nothing while waiting
3. Empty state — `<EmptyState />`, never leave a blank screen
4. Error state — `<ErrorBanner />`, never crash silently
5. All user-visible strings as constants (no magic strings)
6. ARIA labels on every interactive element
7. **If showing analysis or recommendations: `<DisclaimerBanner />`**

## Screen Component Pattern

```typescript
import { useTranslation } from 'react-i18next';
import { useStockAnalysis } from '@/hooks/useStockAnalysis';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { EmptyState } from '@/components/EmptyState';
import { ErrorBanner } from '@/components/ErrorBanner';
import { DisclaimerBanner } from '@/components/DisclaimerBanner';

interface StockAnalysisScreenProps {
  ticker: string;
}

export function StockAnalysisScreen({ ticker }: StockAnalysisScreenProps) {
  const { data, isLoading, error } = useStockAnalysis(ticker);

  if (isLoading) return <LoadingSpinner label="Analysing stock..." />;
  if (error) return <ErrorBanner message="Failed to load analysis. Please try again." />;
  if (!data) return <EmptyState message="Enter a ticker to begin analysis." />;

  return (
    <main role="main" aria-label={`Stock analysis for ${ticker}`}>
      <DisclaimerBanner />
      <h1 className="text-2xl font-bold">{ticker} Analysis</h1>
      <ScorecardCard scorecard={data.scorecard} />
      <VerdictBadge verdict={data.verdict} />
      <PriceLevelsCard entry={data.entry} stopLoss={data.stopLoss} target={data.target} />
    </main>
  );
}
```

## DisclaimerBanner — Required on Analysis/Advisory Screens

```typescript
// components/DisclaimerBanner.tsx
export function DisclaimerBanner() {
  return (
    <div
      role="note"
      aria-label="Investment disclaimer"
      className="bg-amber-50 border border-amber-300 rounded-lg p-3 text-sm text-amber-900"
    >
      ⚠️ <strong>Disclaimer:</strong> This tool is for educational and informational purposes
      only. It does not constitute financial advice. Always consult a SEBI-registered investment
      advisor before making investment decisions. Past performance does not guarantee future results.
    </div>
  );
}
```

## Scorecard Card Pattern

```typescript
interface ScorecardProps {
  scorecard: {
    macro: number;
    sector: number;
    fundamental: number;
    valuation: number;
    technical: number;
    risk: number;
    overall: number;
  };
}

export function ScorecardCard({ scorecard }: ScorecardProps) {
  const dimensions = [
    { label: 'Macro', value: scorecard.macro },
    { label: 'Sector', value: scorecard.sector },
    { label: 'Fundamental', value: scorecard.fundamental },
    { label: 'Valuation', value: scorecard.valuation },
    { label: 'Technical', value: scorecard.technical },
    { label: 'Risk', value: scorecard.risk },
  ];

  return (
    <div className="grid grid-cols-3 gap-3" role="list" aria-label="Analysis scorecard">
      {dimensions.map(({ label, value }) => (
        <div key={label} role="listitem" className="bg-white rounded-lg p-3 shadow-sm">
          <p className="text-xs text-gray-500">{label}</p>
          <p className="text-xl font-bold">{value}<span className="text-sm text-gray-400">/10</span></p>
        </div>
      ))}
    </div>
  );
}
```

## Verdict Badge

```typescript
const VERDICT_STYLES = {
  Buy:   'bg-green-100 text-green-800 border-green-300',
  Wait:  'bg-yellow-100 text-yellow-800 border-yellow-300',
  Avoid: 'bg-red-100 text-red-800 border-red-300',
} as const;

type Verdict = keyof typeof VERDICT_STYLES;

export function VerdictBadge({ verdict }: { verdict: Verdict }) {
  return (
    <span
      className={`inline-block px-4 py-1 rounded-full border font-semibold ${VERDICT_STYLES[verdict]}`}
      aria-label={`Recommendation: ${verdict}`}
    >
      {verdict}
    </span>
  );
}
```

## Anti-Patterns — Never

- Hardcode any financial value, price, or ticker symbol
- Fetch data directly inside a component — always use a custom hook
- Return `null` for loading/error states — always show feedback
- Use `any` in TypeScript
- Mix business logic with rendering
- Show analysis/advisory output without `<DisclaimerBanner />`
- Show a Buy/Sell verdict without the supporting scorecard

## Component File Structure

```
ComponentName/
  index.tsx              ← component
  ComponentName.test.tsx
  ComponentName.types.ts
```
