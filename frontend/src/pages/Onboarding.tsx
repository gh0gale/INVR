import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/auth';
import { apiUrl } from '../api';
import { Wordmark } from '../components/SiteChrome';
import { IconArrowLeft, IconArrowRight, IconClose, IconPlus } from '../components/Icons';
import { errorMessage } from '../types';
import { useDocumentTitle } from '../hooks';

/**
 * Six questions, in the order the backend profile schema expects them. The
 * labels state what each answer actually changes downstream rather than
 * dressing the step up as a system operation.
 */
const QUESTIONS = [
  {
    id: 'experience',
    heading: 'How much market experience do you have?',
    why: 'Sets the vocabulary level the tutor writes in.',
    options: ['Beginner', 'Intermediate', 'Advanced'],
    type: 'choice',
  },
  {
    id: 'goal',
    heading: 'What are you investing for?',
    why: 'Frames how each verdict is explained back to you.',
    options: ['Wealth Growth', 'Dividend Income', 'Capital Preservation'],
    type: 'choice',
  },
  {
    id: 'style',
    heading: 'Which horizon do you trade on?',
    why: 'Selects the data the pipeline fetches and the gates it applies.',
    options: ['Intraday', 'Swing', 'Positional', 'Long-term'],
    type: 'choice',
  },
  {
    id: 'risk',
    heading: 'How much drawdown can you sit through?',
    why: 'Recorded on your profile and quoted in the tutor context.',
    options: ['Conservative', 'Moderate', 'Aggressive'],
    type: 'choice',
  },
  {
    id: 'portfolio',
    heading: 'How is your capital allocated today?',
    why: 'Stored as weights. Must total 100 percent.',
    type: 'allocation',
  },
  {
    id: 'capital',
    heading: 'How much capital can you deploy?',
    why: 'Position sizes are calculated at 2 percent risk of this amount.',
    type: 'numeric',
  },
] as const;

type QuestionId = (typeof QUESTIONS)[number]['id'];

export default function Onboarding() {
  const navigate = useNavigate();
  const { session, setProfileState } = useAuth();
  useDocumentTitle('Profile setup');

  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [formData, setFormData] = useState<{
    experience: string;
    goal: string;
    style: string;
    risk: string;
    portfolio: { id: string; name: string; value: string }[];
    capital: string;
  }>({
    experience: '',
    goal: '',
    style: '',
    risk: '',
    portfolio: [
      { id: 'init-1', name: 'Equities', value: '' },
      { id: 'init-2', name: 'Cash', value: '' },
    ],
    capital: '',
  });

  const activeQuestion = QUESTIONS[step];
  const isLast = step === QUESTIONS.length - 1;
  const choiceOptions: readonly string[] =
    'options' in activeQuestion ? activeQuestion.options : [];

  const totalAlloc = formData.portfolio.reduce((a, b) => a + (Number(b.value) || 0), 0);
  const allocComplete = totalAlloc === 100;

  // No rows at all is a valid answer: it means "I hold only cash". The backend
  // accepts an empty portfolio for exactly that reason, and requiring an
  // allocation here forced new investors to invent one (audit E2E-01).
  const holdsNothing = formData.portfolio.length === 0;

  const isStepComplete = (): boolean => {
    if (activeQuestion.type === 'choice') {
      return formData[activeQuestion.id as QuestionId] !== '';
    }
    if (activeQuestion.type === 'allocation') {
      if (holdsNothing) return true;
      const allNamed = formData.portfolio.every((p) => p.name.trim() !== '');
      return allocComplete && allNamed;
    }
    if (activeQuestion.type === 'numeric') {
      return formData.capital !== '' && Number(formData.capital) > 0;
    }
    return false;
  };

  const handleNext = async () => {
    if (!isLast) {
      setStep((s) => s + 1);
      return;
    }

    if (!session) {
      setSubmitError('Your session expired. Sign in again to save this profile.');
      return;
    }

    setLoading(true);
    setSubmitError(null);

    // Rows with no name are dropped rather than sent as "": a blank key would
    // be stored as a holding the user never named.
    const finalPortfolio = formData.portfolio
      .filter((p) => p.name.trim() !== '')
      .reduce(
      (acc, curr) => {
        acc[curr.name] = Number(curr.value) / 100.0;
        return acc;
      },
      {} as Record<string, number>,
    );

    const goalMapped =
      formData.goal === 'Wealth Growth'
        ? 'wealth_growth'
        : formData.goal === 'Dividend Income'
          ? 'dividend_income'
          : 'capital_preservation';

    const styleMapped =
      formData.style === 'Long-term' ? 'long_term' : formData.style.toLowerCase();

    const payload = {
      experience: formData.experience.toLowerCase(),
      goal: goalMapped,
      timeframe: styleMapped,
      risk: formData.risk.toLowerCase(),
      portfolio: finalPortfolio,
      capital: parseFloat(formData.capital),
    };

    try {
      const response = await fetch(apiUrl('/api/v1/profiles/'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errData = (await response.json().catch(() => ({}))) as { detail?: string };
        throw new Error(errData.detail || 'The profile could not be saved.');
      }

      const responseData = await response.json();
      setProfileState(responseData);
      navigate('/workspace');
    } catch (err: unknown) {
      // fetch rejects with a TypeError ("Failed to fetch") when the request
      // never reaches the server, e.g. a CORS mismatch. Say that plainly.
      setSubmitError(
        err instanceof TypeError
          ? 'Could not reach the INVR server, so the profile was not saved. Your answers are still here; try again in a moment.'
          : errorMessage(err, 'Something went wrong while saving the profile.'),
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-term-950">
      <header className="border-b border-rule">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-baseline gap-2">
            <Wordmark />
            <span className="label hidden sm:inline">Profile setup</span>
          </Link>
          <p className="num text-xs text-fg-3">
            Step {step + 1} of {QUESTIONS.length}
          </p>
        </div>
        {/* Progress. Width is the state; there is no other decoration on it. */}
        <div className="h-px w-full bg-rule">
          <div
            className="h-px bg-accent transition-[width] duration-300"
            style={{ width: `${((step + 1) / QUESTIONS.length) * 100}%` }}
          />
        </div>
      </header>

      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-14">
        <p className="label mb-4">Question {String(step + 1).padStart(2, '0')}</p>
        <h1 className="text-4xl font-bold leading-tight tracking-tight text-fg md:text-5xl">
          {activeQuestion.heading}
        </h1>
        <p className="label mb-1.5 mt-6">What this changes</p>
        <p className="text-lg leading-relaxed text-fg-2">{activeQuestion.why}</p>

        <div className="mt-10">
          {/* --------------------------------------------------------- choice */}
          {activeQuestion.type === 'choice' && (
            <fieldset className="border-t border-rule">
              <legend className="sr-only">{activeQuestion.heading}</legend>
              {choiceOptions.map((option) => {
                const selected = formData[activeQuestion.id as QuestionId] === option;
                return (
                  <label
                    key={option}
                    // The radio itself is visually hidden, so its keyboard focus
                    // is drawn on the row that stands in for it.
                    className={`flex cursor-pointer items-center justify-between border-b border-rule px-4 py-4 transition-colors has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:-outline-offset-2 has-[:focus-visible]:outline-accent ${
                      selected ? 'bg-term-850' : 'hover:bg-term-900'
                    }`}
                  >
                    <span className="flex items-center gap-3">
                      <input
                        type="radio"
                        name={activeQuestion.id}
                        value={option}
                        checked={selected}
                        onChange={() =>
                          setFormData({ ...formData, [activeQuestion.id]: option })
                        }
                        className="sr-only"
                      />
                      <span
                        aria-hidden="true"
                        className={`flex h-3.5 w-3.5 items-center justify-center border ${
                          selected ? 'border-accent bg-accent' : 'border-rule-strong'
                        }`}
                      />
                      <span className={`text-lg ${selected ? 'text-fg' : 'text-fg-2'}`}>
                        {option}
                      </span>
                    </span>
                    {selected && <span className="label">Selected</span>}
                  </label>
                );
              })}
            </fieldset>
          )}

          {/* ----------------------------------------------------- allocation */}
          {activeQuestion.type === 'allocation' && (
            <div>
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-y border-rule">
                    <th className="label py-2 text-left font-semibold">Asset class</th>
                    <th className="label w-24 py-2 text-right font-semibold">Weight</th>
                    <th className="w-11 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {formData.portfolio.map((sector, index) => (
                    <tr key={sector.id} className="border-b border-rule">
                      <td className="py-2 pr-3">
                        <input
                          type="text"
                          aria-label={`Asset class ${index + 1}`}
                          placeholder="Name this holding"
                          value={sector.name}
                          onChange={(e) => {
                            const next = [...formData.portfolio];
                            next[index] = { ...next[index], name: e.target.value };
                            setFormData((prev) => ({ ...prev, portfolio: next }));
                          }}
                          className="field"
                        />
                      </td>
                      <td className="py-2">
                        <div className="flex items-center justify-end gap-1">
                          <input
                            type="number"
                            min="0"
                            max="100"
                            aria-label={`Weight for ${sector.name || `holding ${index + 1}`}`}
                            placeholder="0"
                            value={sector.value}
                            onChange={(e) => {
                              const val = Math.min(100, Math.max(0, Number(e.target.value) || 0));
                              const next = [...formData.portfolio];
                              next[index] = {
                                ...next[index],
                                value: e.target.value === '' ? '' : String(val),
                              };
                              setFormData((prev) => ({ ...prev, portfolio: next }));
                            }}
                            className="control num min-h-[44px] w-16 px-2 py-2 text-right text-sm [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                          />
                          <span className="text-sm text-fg-3">%</span>
                        </div>
                      </td>
                      <td className="py-2 text-right">
                        <button
                          type="button"
                          aria-label={`Remove ${sector.name || `holding ${index + 1}`}`}
                          onClick={() =>
                            setFormData((prev) => ({
                              ...prev,
                              portfolio: prev.portfolio.filter((p) => p.id !== sector.id),
                            }))
                          }
                          className="icon-btn hover:text-down"
                        >
                          <IconClose className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td className="py-3 text-sm text-fg-2">Total</td>
                    <td
                      className={`num py-3 text-right text-sm font-semibold ${
                        allocComplete ? 'text-up' : 'text-down'
                      }`}
                    >
                      {totalAlloc}%
                    </td>
                    <td />
                  </tr>
                </tfoot>
              </table>

              <div className="mt-4 flex items-center justify-between gap-4">
                <button
                  type="button"
                  onClick={() =>
                    setFormData((prev) => ({
                      ...prev,
                      portfolio: [
                        ...prev.portfolio,
                        { id: `row-${Date.now()}`, name: '', value: '' },
                      ],
                    }))
                  }
                  className="text-action shrink-0 gap-2 text-fg-2"
                >
                  <IconPlus className="h-3.5 w-3.5" />
                  Add a holding
                </button>
                {holdsNothing && (
                  <p className="mt-3 text-sm text-fg-3">
                    No holdings yet? Continue without adding any. You can analyse stocks
                    and build this up later.
                  </p>
                )}
                {!holdsNothing && !allocComplete && (
                  <p className="text-xs text-fg-3">
                    {totalAlloc > 100
                      ? `Remove ${totalAlloc - 100} percent to reach 100.`
                      : `Add ${100 - totalAlloc} percent to reach 100.`}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* -------------------------------------------------------- numeric */}
          {activeQuestion.type === 'numeric' && (
            <div className="panel-sunk p-6">
              <label htmlFor="capital" className="label mb-3 block">
                Capital available, in rupees
              </label>
              <div className="flex items-baseline gap-3">
                <span className="tracking-tight text-3xl text-fg-3">₹</span>
                <input
                  id="capital"
                  type="number"
                  min="0"
                  autoFocus
                  value={formData.capital}
                  onChange={(e) => setFormData({ ...formData, capital: e.target.value })}
                  placeholder="100000"
                  className="control num w-full max-w-xs px-3 py-2.5 text-2xl [appearance:textfield] placeholder:text-fg-3 [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                />
              </div>
              {Number(formData.capital) > 0 && (
                <p className="num mt-4 text-sm text-fg-2">
                  At 2 percent risk, each position risks{' '}
                  {`₹${Math.round(Number(formData.capital) * 0.02).toLocaleString('en-IN')}`}.
                </p>
              )}
            </div>
          )}
        </div>

        {submitError && (
          <p role="alert" className="panel-sunk mt-6 px-3.5 py-3 text-base text-down">
            {submitError}
          </p>
        )}

        {/* ---------------------------------------------------------- actions */}
        <div className="mt-10 flex items-center justify-between border-t border-rule pt-6">
          <button
            type="button"
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            disabled={step === 0 || loading}
            className={`btn-quiet flex items-center gap-2 ${step === 0 ? 'invisible' : ''}`}
          >
            <IconArrowLeft className="h-3.5 w-3.5" />
            Back
          </button>

          <button
            type="button"
            onClick={handleNext}
            disabled={!isStepComplete() || loading}
            className="btn-primary flex items-center gap-2"
          >
            {loading ? 'Saving profile' : isLast ? 'Save and continue' : 'Next'}
            {!loading && <IconArrowRight className="h-3.5 w-3.5" />}
          </button>
        </div>
      </main>
    </div>
  );
}
