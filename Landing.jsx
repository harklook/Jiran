// src/pages/Landing.jsx
import { useEffect, useRef, useState } from "react";
import { useNavigate, Link, useLocation } from "react-router-dom";
import "/src/styles/Landing.css";
import { useAuth } from "../context/AuthContext";
import logo from "/src/styles/Logo.png";

function AnimatedNumber({ value, suffix = "", duration = 1200 }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReducedMotion) {
      setCount(value);
      return;
    }

    let frame;
    const animate = () => {
      const start = performance.now();
      const step = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        setCount(Math.round(value * eased));
        if (progress < 1) frame = requestAnimationFrame(step);
      };
      frame = requestAnimationFrame(step);
    };

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          animate();
          observer.disconnect();
        }
      },
      { threshold: 0.35 }
    );

    observer.observe(el);
    return () => {
      observer.disconnect();
      if (frame) cancelAnimationFrame(frame);
    };
  }, [value, duration]);

  return <span ref={ref}>{count}{suffix}</span>;
}

export default function Landing() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [active, setActive] = useState("home");
  const location = useLocation();

  const homeRef = useRef(null);
  const problemRef = useRef(null);
  const solutionRef = useRef(null);
  const featuresRef = useRef(null);
  const architectureRef = useRef(null);
  const competitorsRef = useRef(null);
  const socialRef = useRef(null);

  const sections = [
    { id: "home", ref: homeRef },
    { id: "problem", ref: problemRef },
    { id: "solution", ref: solutionRef },
    { id: "features", ref: featuresRef },
    { id: "architecture", ref: architectureRef },
    { id: "competitors", ref: competitorsRef },
    { id: "connect", ref: socialRef },
  ];

  const scrollTo = (id) => {
    const s = sections.find((x) => x.id === id);
    if (!s?.ref?.current) return;
    const top = s.ref.current.getBoundingClientRect().top + window.scrollY;
    const navOffset = 86;
    window.scrollTo({ top: Math.max(0, top - navOffset), behavior: "smooth" });
  };

  const handleLogout = async () => {
    await signOut();
    navigate("/");
  };

  useEffect(() => {
    const onScroll = () => {
      const navOffset = 120;
      const y = window.scrollY + navOffset;
      let current = "home";
      for (const s of sections) {
        const el = s.ref.current;
        if (!el) continue;
        if (y >= el.offsetTop) current = s.id;
      }
      setActive(current);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (location.hash === "#connect") scrollTo("connect");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location]);

  const navItems = [
    ["home", "Home"],
    ["problem", "Problem"],
    ["solution", "Solution"],
    ["features", "Features"],
    ["architecture", "How it works"],
    ["competitors", "Competitors"],
  ];

  const compareRows = [
    ["Hyperlocal optimization", "yes", "no", "partial"],
    ["Real-time data sync", "yes", "partial", "no"],
    ["AI-driven inventory guidance", "yes", "partial", "no"],
    ["Retailer-first workflows", "yes", "partial", "partial"],
    ["Cross-store rebalancing", "yes", "no", "partial"],
    ["B2B inventory exchange", "yes", "no", "yes"],
  ];

  return (
    <div className="landing-bg">
      {/* ===== NAVBAR ===== */}
      <nav className="navbar">
        <button className="nav-brand" onClick={() => scrollTo("home")} aria-label="Go to Home">
          <img className="nav-logo" src={logo} alt="Jiran Logo" />
          <span className="brand-text"><h1>Jiran</h1></span>
        </button>

        <div className="nav-mid" aria-label="Landing navigation">
          {navItems.map(([id, label]) => (
            <button key={id} className={`nav-link ${active === id ? "active" : ""}`} onClick={() => scrollTo(id)}>
              {label}
            </button>
          ))}
        </div>

        <div className="nav-right">
          {user ? (
            <>
              <Link className="nav-btn primary" to="/dashboard">Dashboard</Link>
              <button className="nav-btn" onClick={handleLogout}>Log Out</button>
              <Link className="nav-btn nav-about" to="/about">About</Link>
            </>
          ) : (
            <>
              <Link className="nav-btn primary" to="/signup">Sign Up</Link>
              <Link className="nav-btn" to="/login">Log In</Link>
            </>
          )}
        </div>
      </nav>

      {/* ===== HERO / HOME ===== */}
      <section ref={homeRef} className="section hero">
        <div className="container">
          <div className="hero-card">
            <h2 className="hero-title">Meet <span className="hero-accent">Jiran</span></h2>
            <p className="hero-sub">
              A smart inventory layer for retailers that turns live sales data into clearer decisions, healthier cash flow, and less dead stock.
            </p>
            <div className="hero-actions">
              <button className="btn primary" onClick={() => scrollTo("features")}>Explore Features</button>
              <button className="btn ghost" onClick={() => scrollTo("architecture")}>View Architecture</button>
            </div>
            <div className="hero-stats" aria-label="Jiran performance highlights">
              <div className="stat"><div className="stat-num"><AnimatedNumber value={60} suffix="%" /></div><div className="stat-label">Less dead stock</div></div>
              <div className="stat"><div className="stat-num"><AnimatedNumber value={12} suffix="x" /></div><div className="stat-label">Faster rebalancing</div></div>
              <div className="stat"><div className="stat-num"><AnimatedNumber value={98} suffix="%" /></div><div className="stat-label">Inventory accuracy</div></div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== PROBLEM ===== */}
      <section ref={problemRef} className="section soft">
        <div className="container">
          <div className="section-head center">
            <span className="pill">The Challenge</span>
            <h2>Retailers are drowning in stock, spreadsheets, and second guesses</h2>
            <p>Your store collects valuable sales data, but without clear next steps, teams still guess what to reorder, discount, move, or stop buying.</p>
          </div>

          <div className="grid cards-3">
            <article className="card pop-card">
              <div className="icon red">💸</div>
              <h3>Slow-moving stock traps cash</h3>
              <p>Every item that does not move is money stuck on a shelf, limiting cash flow and buying power.</p>
            </article>
            <article className="card pop-card">
              <div className="icon amber">🔁</div>
              <h3>Reordering is too reactive</h3>
              <p>Last month’s sales are useful, but demand shifts quickly. Jiran helps teams act before shelves become a problem.</p>
            </article>
            <article className="card pop-card">
              <div className="icon teal">📉</div>
              <h3>Surplus has nowhere smart to go</h3>
              <p>One retailer’s excess could be another retailer’s opportunity, but today that connection is mostly invisible.</p>
            </article>
          </div>
        </div>
      </section>

      {/* ===== SOLUTION ===== */}
      <section ref={solutionRef} className="section">
        <div className="container">
          <div className="two-col">
            <div>
              <span className="pill">The Jiran Way</span>
              <h2>From inventory noise to retail moves that make sense</h2>
              <p>No new system to learn. Jiran connects to your existing setup and turns sales and inventory data into smart, actionable decisions.</p>
              <ul className="checklist">
                <li>Connect securely with zero disruption</li>
                <li>See what is selling, slowing, overstocked, or critical</li>
                <li>Act immediately: reorder smarter, adjust pricing, and trade locally</li>
                <li>Turn weekly guesswork into confident daily decisions</li>
              </ul>
            </div>

            <div className="mini-grid">
              <div className="mini-card"><div className="mini-icon">🔌</div><div className="mini-title">POS</div><div className="mini-sub">Your existing sales and inventory data.</div></div>
              <div className="mini-card"><div className="mini-icon">🧠</div><div className="mini-title">Jiran</div><div className="mini-sub">Classification, insights, and recommendations.</div></div>
              <div className="mini-card"><div className="mini-icon">⚡</div><div className="mini-title">Action</div><div className="mini-sub">Restock, discount, and trade with confidence.</div></div>
              <div className="mini-card"><div className="mini-icon">→</div><div className="mini-title">Flow</div><div className="mini-sub">Connect. Analyze. Act.</div></div>
            </div>

            <div className="marquee-strip" aria-label="Jiran process marquee">
              <div className="marquee-track">
                {Array.from({ length: 8 }).map((_, i) => (
                  <span key={i}>POS <b>→</b> Jiran <b>→</b> Action</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== FEATURES ===== */}
      <section ref={featuresRef} className="section soft">
        <div className="container">
          <div className="section-head center capability-head">
            <span className="pill">Capabilities</span>
            <h2>Everything your store needs, split into three simple moves</h2>
            <p>
              Jiran keeps the workflow easy to scan: understand what is happening,
              decide what to do next, then connect with nearby retailers when stock needs to move.
            </p>
          </div>

          <div className="capability-grid">
            <article className="capability-card intelligence">
              <div className="capability-topline">
                <div className="icon blue">📊</div>
                <span className="capability-step">01</span>
              </div>
              <p className="eyebrow">INTELLIGENCE</p>
              <h3>Know what is happening</h3>
              <p className="capability-summary">
                Get a clear live view of your inventory, so slow stock and demand shifts are easy to spot before they become expensive.
              </p>
              <ul className="capability-list">
                <li>
                  <b>Live stock visibility</b>
                  <span>See what is selling, slowing down, or needs attention.</span>
                </li>
                <li>
                  <b>Demand signals</b>
                  <span>Catch changes early instead of reacting too late.</span>
                </li>
              </ul>
            </article>

            <article className="capability-card action">
              <div className="capability-topline">
                <div className="icon teal">🔄</div>
                <span className="capability-step">02</span>
              </div>
              <p className="eyebrow">ACTION</p>
              <h3>Decide what to do next</h3>
              <p className="capability-summary">
                Turn messy inventory data into simple next steps for buying, pricing, discounting, and rebalancing stock.
              </p>
              <ul className="capability-list">
                <li>
                  <b>Smarter reordering</b>
                  <span>Know what to buy, how much to buy, and when to act.</span>
                </li>
                <li>
                  <b>Automatic classification</b>
                  <span>Group items as fast, slow, surplus, or critical.</span>
                </li>
              </ul>
            </article>

            <article className="capability-card connection">
              <div className="capability-topline">
                <div className="icon purple">🤝</div>
                <span className="capability-step">03</span>
              </div>
              <p className="eyebrow">CONNECTION</p>
              <h3>Move stock where it works</h3>
              <p className="capability-summary">
                Give surplus inventory a second chance by matching it with retailers who actually need it.
              </p>
              <ul className="capability-list">
                <li>
                  <b>B2B inventory exchange</b>
                  <span>Trade excess stock instead of writing it off.</span>
                </li>
                <li>
                  <b>Secure retailer access</b>
                  <span>Keep every connection permission-based and transparent.</span>
                </li>
              </ul>
            </article>
          </div>
        </div>
      </section>

      {/* ===== HOW IT WORKS ===== */}
      <section ref={architectureRef} className="section">
        <div className="container">
          <div className="section-head center">
            <span className="pill">How it works</span>
            <h2>A left-to-right flow from data to decisions</h2>
            <p>Connect the data, classify the signal, recommend the move, then take action.</p>
          </div>

          <div className="flow-row">
            <div className="flow-card tint-blue"><span>1</span><h3>Connect</h3><p>POS, ERP, sales, and stock feeds sync securely.</p></div>
            <div className="flow-arrow">→</div>
            <div className="flow-card tint-cyan"><span>2</span><h3>Classify</h3><p>Jiran tags fast movers, slow movers, surplus, and critical stock.</p></div>
            <div className="flow-arrow">→</div>
            <div className="flow-card tint-indigo"><span>3</span><h3>Recommend</h3><p>AI highlights reorder, discount, rebalance, and trade opportunities.</p></div>
            <div className="flow-arrow">→</div>
            <div className="flow-card tint-teal"><span>4</span><h3>Act</h3><p>Retail teams move with clarity across stores and partners.</p></div>
          </div>

          <div className="stack-foot">
            <span className="tiny-pill">Real-time sync</span>
            <span className="tiny-pill">Secure APIs</span>
            <span className="tiny-pill">Inventory signals</span>
            <span className="tiny-pill">Action-ready insights</span>
          </div>
        </div>
      </section>

      {/* ===== COMPETITORS ===== */}
      <section ref={competitorsRef} className="section soft">
        <div className="container">
          <div className="section-head center">
            <span className="pill">Comparison</span>
            <h2>Why Jiran wins</h2>
            <p>A cleaner, smarter comparison against traditional systems and generic marketplaces.</p>
          </div>

          <div className="compare swanky">
            <div className="compare-head">
              <div className="compare-title">Capability</div>
              <div className="tab active">Jiran</div>
              <div className="tab">Traditional</div>
              <div className="tab">Marketplaces</div>
            </div>
            <div className="compare-table">
              {compareRows.map(([feature, jiran, traditional, marketplaces]) => (
                <div className="compare-row" key={feature}>
                  <div className="compare-cell feature">{feature}</div>
                  <div className={`compare-cell ${jiran}`}>{jiran === "yes" ? "✓" : jiran === "partial" ? "~" : "×"}</div>
                  <div className={`compare-cell ${traditional}`}>{traditional === "yes" ? "✓" : traditional === "partial" ? "~" : "×"}</div>
                  <div className={`compare-cell ${marketplaces}`}>{marketplaces === "yes" ? "✓" : marketplaces === "partial" ? "~" : "×"}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="compare-cards">
            <div className="compare-card primary"><div className="cc-title">Jiran</div><div className="cc-sub">Built for modern retail operations with real-time intelligence.</div></div>
            <div className="compare-card"><div className="cc-title">Traditional Systems</div><div className="cc-sub">Useful for records, but slower for cross-store decisions.</div></div>
            <div className="compare-card"><div className="cc-title">Marketplaces</div><div className="cc-sub">Designed for listings, not internal optimization or rebalancing.</div></div>
          </div>
        </div>
      </section>

      {/* ===== SOCIAL / CONNECT ===== */}
      <section ref={socialRef} className="section">
        <div className="container">
          <div className="section-head center">
            <span className="pill">Connect</span>
            <h2>Follow our build</h2>
            <p>We share progress, updates, and demos as we ship.</p>
          </div>
          <div className="social-grid">
            <a className="social-card" href="https://instagram.com/jiran.ae" target="_blank" rel="noreferrer"><span className="social-icon ig">📷</span><span className="social-text"><span className="social-title">Instagram</span><span className="social-handle">jiran.ae</span></span><span className="social-go">→</span></a>
            <a className="social-card" href="https://www.linkedin.com/company/jiran-ae" target="_blank" rel="noreferrer"><span className="social-icon in">in</span><span className="social-text"><span className="social-title">LinkedIn</span><span className="social-handle">Jiran</span></span><span className="social-go">→</span></a>
          </div>
        </div>
      </section>
    </div>
  );
}
