/** Steps of the first-login workspace tour, anchored by `data-tour` attributes. */
export type TourStep = { target: string; title: string; body: string };

export const WORKSPACE_TOUR: TourStep[] = [
  {
    target: 'ticker-search',
    title: 'Find a stock',
    body: 'Type a company name or an NSE symbol, then pick a match from the list. Only listed NSE stocks can be analysed.',
  },
  {
    target: 'horizon-select',
    title: 'Choose a horizon',
    body: 'Intraday, swing, positional or long-term. It sets the data fetched and the gates applied, and each stock remembers the horizon you last ran it on.',
  },
  {
    target: 'analyse',
    title: 'Run the analysis',
    body: 'Fetches market data, computes the indicators and scores each gate. It takes a few seconds.',
  },
  {
    target: 'analysis-area',
    title: 'Read the result',
    body: 'The verdict, confidence and gate results are fixed arithmetic. The written explanation is generated from those figures and never changes them.',
  },
  {
    target: 'recent-runs',
    title: 'Recent runs and watchlist',
    body: 'Your last five analyses and the stocks you follow. Select one to open it again.',
  },
  {
    target: 'tutor-launcher',
    title: 'Ask the tutor',
    body: 'Questions about the analysis in front of you, or any term you have not met. It opens beside the result after each run on a wide screen; the switch in its header turns that off.',
  },
  {
    target: 'tour-button',
    title: 'Come back any time',
    body: 'Replay this walkthrough from here whenever you want a refresher.',
  },
];
