// Shared design tokens + tiny helpers for the CDP profiles redesign.
// Dark slate surfaces, mono labels, muted green accent.

const TOKENS = {
  bg: '#0e1216',
  bg2: '#151a20',
  bg3: '#1c232b',
  surface: '#171d24',
  surfaceHi: '#1f262e',
  border: '#252d36',
  borderHi: '#323b45',
  text: '#e6e8eb',
  textDim: '#9aa3ad',
  textMute: '#6b7682',
  accent: '#4ade80',       // signup / positive
  accentDim: 'rgba(74,222,128,0.12)',
  customer: '#34d399',
  lead: '#60a5fa',
  leadDim: 'rgba(96,165,250,0.12)',
  signed: '#fbbf24',
  signedDim: 'rgba(251,191,36,0.12)',
  webinar: '#a78bfa',
  webinarDim: 'rgba(167,139,250,0.14)',
  call: '#f472b6',
  callDim: 'rgba(244,114,182,0.14)',
  form: '#22d3ee',
  formDim: 'rgba(34,211,238,0.14)',
  customerBg: 'rgba(52,211,153,0.14)',
  rowHover: 'rgba(255,255,255,0.025)',
  // "mono" is retained as a token name for minimal-change editing, but now
  // points to the same humanist sans used elsewhere — marketing users
  // found the terminal font too technical.
  mono: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif',
  sans: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif',
};

// Source/channel presentation — includes the new Calendly + WebinarGeek
// sources the user added.
const CHANNEL_META = {
  'Direct':           { dot: '#9aa3ad', tint: 'rgba(154,163,173,0.12)' },
  'Organic Search':   { dot: '#34d399', tint: 'rgba(52,211,153,0.12)' },
  'Paid Search':      { dot: '#fbbf24', tint: 'rgba(251,191,36,0.12)' },
  'Affiliates':       { dot: '#f472b6', tint: 'rgba(244,114,182,0.12)' },
  'Referral':         { dot: '#60a5fa', tint: 'rgba(96,165,250,0.12)' },
  'Email':            { dot: '#22d3ee', tint: 'rgba(34,211,238,0.12)' },
  'Calendly':         { dot: '#fb923c', tint: 'rgba(251,146,60,0.14)' },
  'WebinarGeek':      { dot: '#a78bfa', tint: 'rgba(167,139,250,0.14)' },
  'Social':           { dot: '#f87171', tint: 'rgba(248,113,113,0.12)' },
};

const STATUS_META = {
  'customer':  { label: 'CUSTOMER',  color: TOKENS.customer, bg: TOKENS.customerBg },
  'lead':      { label: 'LEAD',      color: TOKENS.lead,     bg: TOKENS.leadDim },
  'signed-up': { label: 'SIGNED UP', color: TOKENS.signed,   bg: TOKENS.signedDim },
};

const ACTIVITY_META = {
  first_session:        { label: 'First session',          color: TOKENS.textDim,  bg: 'rgba(154,163,173,0.12)' },
  form_submission:      { label: 'Form submission',        color: TOKENS.form,     bg: TOKENS.formDim },
  webinar_registration: { label: 'Webinar registration',   color: TOKENS.webinar,  bg: TOKENS.webinarDim },
  calendly_booking:     { label: 'Calendly booking',       color: TOKENS.call,     bg: TOKENS.callDim },
  signup:               { label: 'Signed up',              color: TOKENS.signed,   bg: TOKENS.signedDim },
  customer:             { label: 'Became customer',        color: TOKENS.customer, bg: TOKENS.customerBg },
  paying_started:       { label: 'Started paying',         color: TOKENS.customer, bg: TOKENS.customerBg },
};

// Tiny inline SVGs (no external icons).
const Icon = {
  search: (p) => (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}>
      <circle cx="7" cy="7" r="4.5" /><path d="M10.5 10.5 L13.5 13.5" strokeLinecap="round"/>
    </svg>
  ),
  chevDown: (p) => (
    <svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}>
      <path d="M3 6 L8 11 L13 6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  chevRight: (p) => (
    <svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}>
      <path d="M6 3 L11 8 L6 13" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  arrowLeft: (p) => (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}>
      <path d="M13 8 H3 M7 4 L3 8 L7 12" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  form: (p) => (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}>
      <rect x="3" y="2.5" width="10" height="11" rx="1.5"/>
      <path d="M5.5 6 H10.5 M5.5 8.5 H10.5 M5.5 11 H8.5" strokeLinecap="round"/>
    </svg>
  ),
  calendar: (p) => (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}>
      <rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/>
      <path d="M2.5 6.5 H13.5 M5.5 2 V5 M10.5 2 V5" strokeLinecap="round"/>
    </svg>
  ),
  video: (p) => (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}>
      <rect x="2" y="4" width="9" height="8" rx="1.5"/>
      <path d="M11 7 L14 5 V11 L11 9 Z"/>
    </svg>
  ),
  user: (p) => (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}>
      <circle cx="8" cy="5.5" r="2.5"/>
      <path d="M3 13.5 C3.5 10.5 6 9.5 8 9.5 C10 9.5 12.5 10.5 13 13.5" strokeLinecap="round"/>
    </svg>
  ),
  globe: (p) => (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}>
      <circle cx="8" cy="8" r="5.5"/>
      <path d="M2.5 8 H13.5 M8 2.5 C10 4.5 10.5 7 10.5 8 C10.5 9 10 11.5 8 13.5 C6 11.5 5.5 9 5.5 8 C5.5 7 6 4.5 8 2.5"/>
    </svg>
  ),
  euro: (p) => (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}>
      <path d="M12 4.5 C11 3.5 9.5 3 8 3 C5.5 3 3.5 5 3.5 8 C3.5 11 5.5 13 8 13 C9.5 13 11 12.5 12 11.5"/>
      <path d="M2.5 7 H8 M2.5 9 H7.5"/>
    </svg>
  ),
  dots: (p) => (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor" {...p}>
      <circle cx="3.5" cy="8" r="1.3"/><circle cx="8" cy="8" r="1.3"/><circle cx="12.5" cy="8" r="1.3"/>
    </svg>
  ),
  download: (p) => (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}>
      <path d="M8 2.5 V10.5 M4.5 7 L8 10.5 L11.5 7" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M3 13 H13" strokeLinecap="round"/>
    </svg>
  ),
  filter: (p) => (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}>
      <path d="M2.5 3.5 H13.5 L10 8 V12.5 L6 13.5 V8 Z" strokeLinejoin="round"/>
    </svg>
  ),
  external: (p) => (
    <svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}>
      <path d="M9 3 H13 V7 M13 3 L7.5 8.5 M12 9 V12.5 H3.5 V4 H7" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  plus: (p) => (
    <svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="1.8" {...p}>
      <path d="M8 3 V13 M3 8 H13" strokeLinecap="round"/>
    </svg>
  ),
  close: (p) => (
    <svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="1.8" {...p}>
      <path d="M4 4 L12 12 M12 4 L4 12" strokeLinecap="round"/>
    </svg>
  ),
};

// Relative-time formatter: "2h ago", "3d ago", "in 27d".
function relTime(date, now) {
  const d = typeof date === 'string' ? new Date(date) : date;
  const ms = d - now;
  const abs = Math.abs(ms);
  const s = Math.floor(abs / 1000);
  const m = Math.floor(s / 60);
  const h = Math.floor(m / 60);
  const day = Math.floor(h / 24);
  const label = day > 60 ? `${Math.floor(day / 30)}mo` :
                day > 0  ? `${day}d` :
                h > 0    ? `${h}h` :
                m > 0    ? `${m}m` : `${s}s`;
  return ms < 0 ? `${label} ago` : `in ${label}`;
}

function Dot({ color, size = 6 }) {
  return <span style={{ display: 'inline-block', width: size, height: size, borderRadius: '50%', background: color, flexShrink: 0 }} />;
}

function Avatar({ name, size = 32, bg }) {
  const initials = (name || '?').split(' ').map(s => s[0]).filter(Boolean).slice(0, 2).join('').toUpperCase();
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%',
      background: bg || TOKENS.accentDim,
      color: TOKENS.accent,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: size * 0.38, fontWeight: 600, fontFamily: TOKENS.mono,
      letterSpacing: '-0.02em', flexShrink: 0,
      border: `1px solid ${TOKENS.accentDim}`,
    }}>{initials}</div>
  );
}

function StatusPill({ status }) {
  const m = STATUS_META[status] || STATUS_META['lead'];
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '2px 8px', borderRadius: 3,
      fontSize: 10, fontFamily: TOKENS.mono, fontWeight: 500,
      letterSpacing: '0.08em',
      background: m.bg, color: m.color,
      border: `1px solid ${m.color}22`,
    }}>
      <Dot color={m.color} size={5} />
      {m.label}
    </span>
  );
}

function ChannelBadge({ channel, source }) {
  const m = CHANNEL_META[channel] || CHANNEL_META['Direct'];
  const isNew = channel === 'Calendly' || channel === 'WebinarGeek';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '2px 7px 2px 6px', borderRadius: 3,
      fontSize: 11, fontFamily: TOKENS.mono,
      background: m.tint, color: m.dot,
      border: `1px solid ${m.dot}22`,
    }}>
      <Dot color={m.dot} size={5} />
      <span>{channel}</span>
      {isNew && (
        <span style={{
          fontSize: 8, padding: '0 4px', borderRadius: 2,
          background: m.dot, color: '#0e1216', fontWeight: 700,
          letterSpacing: '0.05em', marginLeft: 2,
        }}>NEW</span>
      )}
    </span>
  );
}

Object.assign(window, {
  TOKENS, CHANNEL_META, STATUS_META, ACTIVITY_META,
  Icon, relTime, Dot, Avatar, StatusPill, ChannelBadge,
});
