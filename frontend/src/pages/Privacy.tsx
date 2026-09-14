import { Link } from 'react-router-dom';
import { Clause, DocumentPage } from '../components/SiteChrome';

/**
 * DRAFT PENDING LEGAL REVIEW.
 *
 * Every category below was taken from the actual database schema and request
 * path, so this describes real behaviour rather than generic boilerplate. It
 * still needs review by a qualified lawyer, and it must be revisited whenever
 * the schema, the model providers (backend/app/llm.py) or the telemetry
 * configuration changes. Clause 04 was rewritten on 2026-09-14 when the models
 * moved from local Ollama to Groq and Google; it had said text never left the
 * operator's own infrastructure.
 */
const CONTACT = 'info.ghogale@gmail.com';

const ContactLink = () => (
  <a href={`mailto:${CONTACT}`} className="link">
    {CONTACT}
  </a>
);

const DATA = [
  {
    what: 'Email address and password',
    why: 'Authentication. Handled by Supabase Auth; passwords are stored hashed by that service and never in plain text.',
    where: 'Supabase Auth',
  },
  {
    what: 'Risk profile',
    why: 'Experience level, goal, horizon, risk tolerance, allocation weights and capital figure. Used to select which gates run and to size positions.',
    where: 'user_profiles',
  },
  {
    what: 'Learned concepts summary',
    why: 'A running list of financial terms you have demonstrated understanding of, extracted from conversation so explanations do not repeat what you know.',
    where: 'user_profiles.semantic_profile',
  },
  {
    what: 'Chat history',
    why: 'Recent messages are kept verbatim as working memory. Older stretches are replaced with short model-written summaries.',
    where: 'chat_sessions',
  },
  {
    what: 'Analysis records',
    why: 'Ticker, horizon, date, computed metrics and verdict. Kept so predictions can be scored against later market behaviour. These rows describe securities, not people.',
    where: 'algorithmic_ledger',
  },
  {
    what: 'Interaction records',
    why: 'That a given analysis was viewed in a given session.',
    where: 'prediction_interactions',
  },
];

export default function Privacy() {
  return (
    <DocumentPage
      title="Privacy policy"
      updated="14 September 2026"
      summary="INVR collects the profile it needs to run an analysis and the conversation it needs to stay useful. It never asks for brokerage credentials, holdings, PAN, or bank details, and it cannot place trades."
    >
      <Clause n="01" heading="Who controls this data">
        <p>
          The data controller is INVR. Privacy requests can be sent to <ContactLink />.
        </p>
      </Clause>

      <Clause n="02" heading="What is collected, and why">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[34rem] border-collapse text-sm">
            <thead>
              <tr className="border-y border-rule text-left">
                <th className="label py-2 pr-4 font-semibold">Data</th>
                <th className="label py-2 pr-4 font-semibold">Purpose</th>
                <th className="label py-2 font-semibold">Stored in</th>
              </tr>
            </thead>
            <tbody>
              {DATA.map((row) => (
                <tr key={row.what} className="border-b border-rule align-baseline">
                  <td className="py-3 pr-4 text-fg">{row.what}</td>
                  <td className="py-3 pr-4 leading-relaxed text-fg-2">{row.why}</td>
                  <td className="num py-3 text-xs text-fg-3">{row.where}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Clause>

      <Clause n="03" heading="What is never collected">
        <p>
          Brokerage credentials, brokerage account numbers, actual holdings, demat statements,
          PAN, Aadhaar, and bank or card details. The allocation figures you enter during setup
          are self-reported percentages and a single capital number. Nothing is verified against
          a broker, because the service is not connected to one.
        </p>
      </Clause>

      <Clause n="04" heading="Language models and where text goes">
        <p>
          Explanations, tutor replies, conversation summaries, safety screening and topic
          checks are produced by hosted language models. The text involved, meaning your tutor
          messages, recent conversation, and the analysis being discussed, is sent to Groq, and
          to Google (Gemini) when Groq is unavailable. Each tutor message is also sent to Google
          to classify its topic. Your risk profile figures are included where an explanation is
          tailored to them.
        </p>
        <p>
          Those providers process the text to return a response, under their own terms and
          privacy policies. Your email address and password are never sent to them. Do not enter
          anything in the chat that you would not want those providers to process.
        </p>
      </Clause>

      <Clause n="05" heading="Diagnostic tracing">
        <p>
          The backend can record execution traces for debugging and quality measurement. When
          tracing is switched on, those traces can include the text sent to and returned from a
          model, along with your account identifier, the ticker analysed, and timing data. They
          are operational records, not a product feature, and access is limited to whoever
          operates the deployment.
        </p>
      </Clause>

      <Clause n="06" heading="Third parties in the request path">
        <p>
          Supabase provides authentication and the database. Groq and Google provide the
          language models described in section 04. The backend runs on Render and this website
          is served by Cloudflare; both handle your requests and see connection details such as
          your IP address. Market data is retrieved from public financial data sources, which
          receive the ticker being requested but nothing about you. Web fonts are served by
          Google Fonts, which receives your IP address as part of that request.
        </p>
      </Clause>

      <Clause n="07" heading="Retention">
        <p>
          Profile data is kept while the account exists. Recent chat messages are retained as a
          rolling window and older content is condensed into summaries, which persist with the
          session. Analysis records are retained after a prediction matures so that accuracy can
          be measured over time.
        </p>
      </Clause>

      <Clause n="08" heading="Your choices">
        <p>
          You can request a copy of your profile and conversation data, correct your profile
          from the setup flow at any time, or ask for your account and associated records to be
          deleted. Send requests to <ContactLink />. Deleting your account does not
          remove analysis rows that describe a security rather than you.
        </p>
      </Clause>

      <Clause n="09" heading="Security">
        <p>
          Access is authenticated with a bearer token verified on every request. Database access
          from the browser is limited by row-level security policy. No system is immune to
          compromise, so do not enter anything in the chat that you would not want stored.
        </p>
      </Clause>

      <Clause n="10" heading="Changes">
        <p>
          Material changes will be reflected here with an updated date. The{' '}
          <Link to="/terms" className="link">
            terms of service
          </Link>{' '}
          cover the rest of the relationship.
        </p>
      </Clause>
    </DocumentPage>
  );
}
