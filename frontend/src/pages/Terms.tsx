import { Link } from 'react-router-dom';
import { Clause, DocumentPage } from '../components/SiteChrome';

/**
 * DRAFT PENDING LEGAL REVIEW.
 *
 * The clauses below describe what this codebase actually does, so they are
 * accurate rather than boilerplate. They are not a substitute for review by a
 * qualified lawyer. The three operator facts were supplied by the owner on
 * 2026-09-14: operator "INVR" and contact info.ghogale@gmail.com. Governing
 * law is set to India because the product is built around NSE, INR and SEBI;
 * that one was inferred and should be confirmed.
 */
const CONTACT = 'info.ghogale@gmail.com';

export default function Terms() {
  return (
    <DocumentPage
      title="Terms of service"
      updated="14 September 2026"
      summary="INVR is an educational analysis tool for NSE-listed equities. Using it does not create an advisory relationship, and nothing it produces is a recommendation to buy or sell a security."
    >
      <Clause n="01" heading="Who provides this service">
        <p>
          This service is operated under the name INVR. Questions about these terms can be sent
          to{' '}
          <a href={`mailto:${CONTACT}`} className="link">
            {CONTACT}
          </a>
          . References to "we" and "us" mean that operator, and "you" means the account holder.
        </p>
      </Clause>

      <Clause n="02" heading="This is not investment advice">
        <p>
          INVR is not a SEBI-registered investment adviser or research analyst, and it does not
          provide personalised investment advice. Every verdict, score, gate result, entry
          level, stop loss and target the system produces is the output of fixed arithmetic
          applied to third-party market data, published for education and research.
        </p>
        <p>
          You are solely responsible for your own trading and investment decisions. Consider
          consulting a SEBI-registered adviser before committing capital.
        </p>
      </Clause>

      <Clause n="03" heading="What the system does and does not do">
        <p>
          The service fetches market data, computes indicators, applies fixed threshold gates,
          and produces one of five verdicts along with an explanation written by a language
          model. The language model cannot change the verdict or the confidence score.
        </p>
        <p>
          The service does not connect to your brokerage account, does not place orders, does
          not hold client funds or securities, and cannot execute a trade on your behalf.
        </p>
      </Clause>

      <Clause n="04" heading="Accuracy and availability">
        <p>
          Market data is retrieved from third-party sources and may be delayed, incomplete,
          adjusted, or wrong. When an input is unavailable, the check that depends on it is
          skipped rather than estimated, so a verdict can rest on fewer checks than usual. The
          explanation accompanying a verdict is written by a language model and can contain
          mistakes; the verdict and confidence score themselves are not model output.
        </p>
        <p>
          The service is provided on an as-is basis without warranty of accuracy, completeness,
          fitness for a particular purpose, or uninterrupted availability. Historical scoring of
          past predictions describes past behaviour and does not indicate future results.
        </p>
      </Clause>

      <Clause n="05" heading="Your account">
        <p>
          You need an account to run an analysis. You are responsible for keeping your
          credentials secure and for activity carried out under your account. Provide accurate
          information during profile setup: the risk profile and capital figure you enter are
          used directly in position sizing arithmetic, so inaccurate inputs produce misleading
          output.
        </p>
      </Clause>

      <Clause n="06" heading="Acceptable use">
        <p>
          Requests are rate limited per account. Do not attempt to exceed those limits, automate
          bulk extraction of analysis output, resell the output as a subscription or signal
          service, interfere with the operation of the service, or attempt to manipulate the
          language model into bypassing its safety instructions. Inbound messages are screened
          for prompt injection and abuse, and requests that fail screening are refused.
        </p>
      </Clause>

      <Clause n="07" heading="Intellectual property">
        <p>
          The software, gate logic, and interface remain the property of the operator. Market
          data belongs to its respective providers. You keep whatever rights you already hold in
          the content of your own messages.
        </p>
      </Clause>

      <Clause n="08" heading="Limitation of liability">
        <p>
          To the fullest extent permitted by applicable law, the operator is not liable for
          trading losses, lost profits, or any indirect, incidental or consequential damages
          arising from your use of the service or from reliance on its output.
        </p>
      </Clause>

      <Clause n="09" heading="Ending your use">
        <p>
          You can stop using the service at any time and request deletion of your account and
          associated records as described in the{' '}
          <Link to="/privacy" className="link">
            privacy policy
          </Link>
          . We may suspend access for a breach of these terms.
        </p>
      </Clause>

      <Clause n="10" heading="Changes and governing law">
        <p>
          These terms may be updated. The date at the top of this page reflects the current
          version, and continued use after a change constitutes acceptance of it.
        </p>
        <p>
          These terms are governed by the laws of India, and disputes are subject to the
          exclusive jurisdiction of the courts of India.
        </p>
      </Clause>
    </DocumentPage>
  );
}
