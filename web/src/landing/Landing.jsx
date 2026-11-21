import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, PlayCircle } from 'lucide-react'
import HeroTrace from './HeroTrace.jsx'
import HowItWorks from './HowItWorks.jsx'
import GroundingScrub from './GroundingScrub.jsx'
import Split from './Split.jsx'
import { useLandingMotion } from './useLandingMotion.js'
import { demo, turn1, turn2 } from './data.js'
import '../workspace/workspace.css'
import './landing.css'

const TOOLS = [
  ['group_aggregate', 'by, metric, agg, top, filters', 'Sum, mean, count, min, max or median of a metric per group.'],
  ['time_trend', 'date_col, metric, agg, grain, filters', 'A metric per day, week, month, quarter or year.'],
  ['distribution', 'column, bins, filters', 'Histogram of one numeric column.'],
  ['top_categories', 'column, top, filters', 'Most frequent values and their share.'],
  ['correlation', 'columns', 'Pairwise correlation of numeric columns.'],
  ['outliers', 'column', 'Rows outside 1.5 × the interquartile range.'],
  ['compare_groups', 'by, metric, filters', 'Count, mean, median and spread per group.'],
  ['crosstab', 'row, col, metric, agg', 'One metric across two categories.'],
  ['scatter', 'x, y, color, limit', 'Two numeric columns against each other.'],
  ['describe_column', 'column', 'Full profile of a single column.'],
  ['filter_rows', 'filters, columns, limit', 'The matching rows themselves, up to 50.'],
]

function ArgsDiff() {
  const a = turn1.plan[0], b = turn2.plan[0]
  const row = (k, v, kind) => (
    <div className={`diff-row is-${kind}`} key={k + kind}>
      <span className="diff-mark" aria-hidden="true">{kind === 'add' ? '+' : kind === 'del' ? '−' : ' '}</span>
      <span className="diff-k">{k}</span>
      <span className="diff-v">{typeof v === 'string' ? v : JSON.stringify(v)}</span>
      {kind !== 'same' && <span className="sr-only">{kind === 'add' ? '(added)' : '(removed)'}</span>}
    </div>
  )
  return (
    <div className="diff" role="group" aria-label="How the plan changed between the two questions">
      <div className="diff-head mono">{a.tool === b.tool ? <span>{b.tool}</span> : <><span className="diff-del-t">{a.tool}</span> → <span>{b.tool}</span></>}</div>
      {row('by', a.args.by, 'del')}
      {row('by', b.args.by, 'add')}
      {row('metric', b.args.metric, 'same')}
      {row('agg', b.args.agg, 'same')}
      {(b.args.filters || []).map((f) => row('filters', `${f.column} ${f.op} ${JSON.stringify(f.value)}`, 'add'))}
    </div>
  )
}

export default function Landing() {
  const root = useRef(null)
  useLandingMotion(root)
  useEffect(() => { document.title = 'Analyst — answers you can trace back to the data' }, [])

  return (
    <div className="landing" ref={root}>
      <a href="#how" className="skip-link">Skip to how it works</a>
      <header className="nav">
        <div className="wrap nav-in">
          <Link to="/" className="wordmark">Analyst</Link>
          <nav aria-label="Sections" className="nav-links">
            <a href="#how">How it works</a>
            <a href="#tools">Tools</a>
            <a href="#grounding">Grounding</a>
            <a href="#models">Models</a>
          </nav>
          <Link to="/app" className="btn btn-primary nav-cta">Open the workspace</Link>
        </div>
      </header>

      <main>
        <section className="hero" aria-labelledby="hero-title">
          <div className="wrap hero-grid">
            <div className="hero-copy">
              <p className="eyebrow" data-hero-fade>A data analyst you can audit</p>
              <Split as="h1" id="hero-title" className="h1" text="Answers you can trace back to the data." />
              <p className="hero-sub" data-hero-fade>
                Give it a dataset. It works out what the data is, answers your questions by running a fixed set of analysis tools,
                and underlines every number that came from a computed result.
              </p>
              <div className="hero-ctas" data-hero-fade>
                <Link to="/app" className="btn btn-primary btn-lg">Open the workspace <ArrowRight aria-hidden="true" /></Link>
                <Link to="/app?demo=1" className="btn btn-secondary btn-lg"><PlayCircle aria-hidden="true" /> Watch an example session</Link>
              </div>
              <ul className="hero-facts mono" data-hero-fade>
                <li>No generated code is run</li>
                <li>Any OpenAI-compatible model</li>
                <li>Works offline without one</li>
              </ul>
            </div>
            <HeroTrace />
          </div>
        </section>

        <HowItWorks />

        <section className="tools" id="tools" aria-labelledby="tools-title">
          <div className="wrap">
            <p className="eyebrow">Why the tools are a fixed list</p>
            <Split text="The model chooses. It never writes the code." id="tools-title" className="h2 h2-wide" />
            <div className="tools-grid">
              <div className="tools-then" data-reveal>
                <p className="tools-label mono">Version one · <span className="strike">execute_custom_analysis_agent.py</span></p>
                <pre className="sql code-old">{`restricted_globals = {
    "__builtins__": {"abs": abs, "min": min, ...},
    "df": self.engine.df.copy(),
    "np": np,
    "pd": pd,
}
exec(custom_code, restricted_globals, local_dict)`}</pre>
                <p className="tools-note">
                  The first version ran Python typed into a form field. The builtins were trimmed, but pandas and numpy were handed in,
                  and pandas alone can read any file the server can. A blocklist around <code>exec</code> is not a sandbox.
                </p>
                <p className="tools-note">
                  It also meant every answer depended on code nobody reviewed, so there was no way to say where a number came from.
                </p>
              </div>
              <div className="tools-now" data-reveal>
                <p className="tools-label mono">Now · analyst/tools.py · {TOOLS.length} functions</p>
                <ul className="registry">
                  {TOOLS.map(([name, sig, desc]) => (
                    <li key={name}>
                      <code className="reg-name">{name}<span className="reg-sig">({sig})</span></code>
                      <span className="reg-desc">{desc}</span>
                    </li>
                  ))}
                </ul>
                <p className="tools-note">
                  Arguments are validated against the dataset's columns, filters compile to parameterised SQL, and a bad call comes back
                  as an error naming the valid columns. Adding a capability means adding a reviewed function.
                </p>
              </div>
            </div>
          </div>
        </section>

        <GroundingScrub />

        <section className="follow-sec" aria-labelledby="follow-title">
          <div className="wrap follow-grid">
            <div>
              <p className="eyebrow">Conversation</p>
              <Split text="Follow-ups change the analysis. They don't start over." id="follow-title" className="h2" />
              <p className="lede" data-reveal>
                The planner sees earlier questions and their results. “Split that by category” and “leave out returned orders” are read as
                edits to the last plan: same tool and metric, a new breakdown, one added filter.
              </p>
            </div>
            <div className="convo" data-reveal>
              <div className="convo-turn">
                <p className="convo-n mono">Question 1</p>
                <p className="convo-q">{turn1.question}</p>
              </div>
              <div className="convo-turn">
                <p className="convo-n mono">Question 2</p>
                <p className="convo-q">{turn2.question}</p>
              </div>
              <ArgsDiff />
            </div>
          </div>
        </section>

        <section className="models" id="models" aria-labelledby="models-title">
          <div className="wrap models-grid">
            <div>
              <p className="eyebrow">Bring your own model</p>
              <Split text="Point it at any OpenAI-compatible endpoint." id="models-title" className="h2" />
              <p className="lede" data-reveal>
                Hosted or local: anything that speaks the chat completions API and can return JSON. Set three variables, or change them
                from the workspace while it runs. The key stays on the server and is never sent back to the browser.
              </p>
            </div>
            <div data-reveal>
              <pre className="sql env">{`# .env
LLM_BASE_URL=https://api.groq.com/openai/v1   # default
LLM_MODEL=openai/gpt-oss-120b                  # default
LLM_API_KEY=…

# or a local server
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.1`}</pre>
              <div className="offline">
                <h3>No key at all?</h3>
                <p>It still runs. Plans come from keyword rules, the same tools execute, and the answer is a plain table of their results
                  marked “LLM not configured”. Nothing is written by a model, so nothing can be invented.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="cta" aria-labelledby="cta-title">
          <div className="wrap cta-in">
            <div className="cta-main">
              <Split text="Bring a CSV. Ask it something." id="cta-title" className="h1 cta-h" />
              <div className="hero-ctas">
                <Link to="/app" className="btn btn-primary btn-lg">Open the workspace <ArrowRight aria-hidden="true" /></Link>
                <Link to="/app?demo=1" className="btn btn-quiet btn-lg">or watch an example session</Link>
              </div>
            </div>
            <div data-reveal>
              <dl className="tally tnum">
                <div><dt>Questions in the example session</dt><dd>{demo.turns.length}</dd></div>
                <div><dt>Tool calls</dt><dd>{demo.turns.reduce((a, t) => a + t.results.length, 0)}</dd></div>
                <div><dt>Time spent in DuckDB</dt><dd>{demo.turns.reduce((a, t) => a + t.results.reduce((b, r) => b + r.ms, 0), 0)} ms</dd></div>
                <div><dt>Numbers that trace to a result</dt><dd>{demo.turns.reduce((a, t) => a + t.grounded_count, 0)} of {demo.turns.reduce((a, t) => a + t.total_numbers, 0)}</dd></div>
              </dl>
              <p className="tally-cap mono">The one that doesn't is shown above, flagged.</p>
            </div>
          </div>
        </section>
      </main>

      <footer className="foot">
        <div className="wrap foot-in">
          <span className="wordmark">Analyst</span>
          <p>FastAPI · DuckDB · React. The figures on this page were computed by the analysis tools on the bundled retail sample (synthetic data). The prose around them was written for this page.</p>
        </div>
      </footer>
    </div>
  )
}
