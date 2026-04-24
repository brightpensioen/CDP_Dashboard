// Updated Profiles list view. Changes vs. current design:
//  • Channel badges now visually highlight the new Calendly + WebinarGeek sources
//  • A small "source mix" row makes the new sources discoverable at a glance
//  • Engagement column replaces the old "First form" column, summarizing
//    forms / webinars / calls per profile at a glance
//  • Row click opens the detail page

function ProfilesList({ profiles, onOpen, onOpenDetail, compact = false }) {
  const [query, setQuery] = React.useState('');
  const [statusFilter, setStatusFilter] = React.useState('all');
  const [channelFilter, setChannelFilter] = React.useState('all');
  const [sortKey, setSortKey] = React.useState('profileDate');
  const [sortDir, setSortDir] = React.useState('desc');

  const filtered = React.useMemo(() => {
    let rows = profiles;
    if (query) {
      const q = query.toLowerCase();
      rows = rows.filter(p => p.email.toLowerCase().includes(q)
        || (p.firstName + ' ' + p.lastName).toLowerCase().includes(q)
        || p.channel.toLowerCase().includes(q)
        || (p.source || '').toLowerCase().includes(q));
    }
    if (statusFilter !== 'all') rows = rows.filter(p => p.status === statusFilter);
    if (channelFilter !== 'all') rows = rows.filter(p => p.channel === channelFilter);
    rows = [...rows].sort((a, b) => {
      const va = a[sortKey], vb = b[sortKey];
      if (va == null) return 1;
      if (vb == null) return -1;
      const cmp = va < vb ? -1 : va > vb ? 1 : 0;
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return rows;
  }, [profiles, query, statusFilter, channelFilter, sortKey, sortDir]);

  const totals = React.useMemo(() => {
    const t = { all: profiles.length, customer: 0, lead: 0, 'signed-up': 0 };
    profiles.forEach(p => { t[p.status] = (t[p.status] || 0) + 1; });
    return t;
  }, [profiles]);

  // Source mix: counts per channel, feeds both the info strip and the
  // filter dropdown so the new Calendly/WebinarGeek sources surface.
  const sourceMix = React.useMemo(() => {
    const m = {};
    profiles.forEach(p => { m[p.channel] = (m[p.channel] || 0) + 1; });
    return m;
  }, [profiles]);

  const toggleSort = (k) => {
    if (sortKey === k) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(k); setSortDir('desc'); }
  };

  return (
    <div style={{
      background: TOKENS.bg, color: TOKENS.text, fontFamily: TOKENS.sans,
      minHeight: '100%', padding: compact ? '20px 24px' : '28px 36px',
      fontSize: 13,
    }}>
      {/* Title */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 14, marginBottom: 18 }}>
        <h1 style={{ fontSize: 20, fontWeight: 600, margin: 0, letterSpacing: '-0.01em' }}>Profiles</h1>
        <span style={{ fontSize: 11, fontFamily: TOKENS.mono, color: TOKENS.textMute, letterSpacing: '0.05em' }}>
          tab.profiles
        </span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <button style={ghostBtn}><Icon.download /> Export</button>
          <button style={primaryBtn}><Icon.plus /> New segment</button>
        </div>
      </div>

      {/* KPI cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
        <Kpi label="MATCHING PROFILES" value={totals.all} sub="+34 this week" />
        <Kpi label="CUSTOMERS"         value={totals.customer} color={TOKENS.customer} sub="49% of base" />
        <Kpi label="LEADS"             value={totals.lead}     color={TOKENS.lead}     sub="+12 this week" />
        <Kpi label="SIGNED UP"         value={totals['signed-up']} color={TOKENS.signed} sub="pending conversion" />
      </div>

      {/* Source mix strip — makes new sources discoverable */}
      <div style={sourceStrip}>
        <span style={{ fontSize: 10, fontFamily: TOKENS.mono, color: TOKENS.textMute, letterSpacing: '0.1em', marginRight: 4 }}>
          SOURCE MIX
        </span>
        {Object.entries(CHANNEL_META).map(([name, meta]) => {
          const count = sourceMix[name] || 0;
          const isNew = name === 'Calendly' || name === 'WebinarGeek';
          const active = channelFilter === name;
          return (
            <button
              key={name}
              onClick={() => setChannelFilter(active ? 'all' : name)}
              style={{
                ...sourceChip,
                background: active ? meta.tint : 'transparent',
                borderColor: active ? meta.dot + '55' : TOKENS.border,
                color: active ? meta.dot : TOKENS.textDim,
              }}
            >
              <Dot color={meta.dot} size={5} />
              <span>{name}</span>
              <span style={{ color: active ? meta.dot : TOKENS.textMute, fontFamily: TOKENS.mono, fontSize: 10 }}>
                {count}
              </span>
              {isNew && (
                <span style={{
                  fontSize: 8, padding: '0 4px', borderRadius: 2,
                  background: meta.dot, color: TOKENS.bg, fontWeight: 700,
                  letterSpacing: '0.05em',
                }}>NEW</span>
              )}
            </button>
          );
        })}
        {channelFilter !== 'all' && (
          <button onClick={() => setChannelFilter('all')} style={{...sourceChip, color: TOKENS.textMute}}>
            <Icon.close /> clear
          </button>
        )}
      </div>

      {/* Filter row */}
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 14 }}>
        <div style={{ position: 'relative', flex: '0 0 280px' }}>
          <div style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: TOKENS.textMute }}>
            <Icon.search />
          </div>
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search email, name, channel…"
            style={searchInput}
          />
        </div>
        <div style={{ display: 'flex', gap: 4, background: TOKENS.surface, border: `1px solid ${TOKENS.border}`, borderRadius: 6, padding: 3 }}>
          {[['all', 'All'], ['customer', 'Customers'], ['lead', 'Leads'], ['signed-up', 'Signed up']].map(([v, label]) => (
            <button
              key={v}
              onClick={() => setStatusFilter(v)}
              style={{
                ...segBtn,
                background: statusFilter === v ? TOKENS.surfaceHi : 'transparent',
                color: statusFilter === v ? TOKENS.text : TOKENS.textDim,
              }}
            >
              {label}
            </button>
          ))}
        </div>
        <button style={ghostBtn}><Icon.filter /> More filters</button>
        <div style={{ flex: 1 }} />
        <span style={{ fontSize: 11, fontFamily: TOKENS.mono, color: TOKENS.textMute }}>
          {filtered.length} of {profiles.length}
        </span>
      </div>

      {/* Table */}
      <div style={tableWrap}>
        <div style={{ ...tableRow, ...tableHeader }}>
          <div style={{ ...colEmail }}>
            <HeaderCell label="Email" k="email" sortKey={sortKey} sortDir={sortDir} onClick={toggleSort} />
          </div>
          <div style={colStatus}><HeaderCell label="Status" k="status" sortKey={sortKey} sortDir={sortDir} onClick={toggleSort} /></div>
          <div style={colDate}><HeaderCell label="Profile date" k="profileDate" sortKey={sortKey} sortDir={sortDir} onClick={toggleSort} /></div>
          <div style={colChannel}><HeaderCell label="Channel / Source" k="channel" sortKey={sortKey} sortDir={sortDir} onClick={toggleSort} /></div>
          <div style={colLoc}><HeaderCell label="Location" k="city" sortKey={sortKey} sortDir={sortDir} onClick={toggleSort} /></div>
          <div style={colEngage}>
            <span style={{ fontSize: 10, fontFamily: TOKENS.mono, color: TOKENS.textMute, letterSpacing: '0.08em' }}>ENGAGEMENT</span>
          </div>
          <div style={colDays}><HeaderCell label="→ Signup" k="daysFirstToSignup" sortKey={sortKey} sortDir={sortDir} onClick={toggleSort} right /></div>
          <div style={colDays}><HeaderCell label="→ Customer" k="daysFirstToCustomer" sortKey={sortKey} sortDir={sortDir} onClick={toggleSort} right /></div>
          <div style={colName}><HeaderCell label="Name" k="firstName" sortKey={sortKey} sortDir={sortDir} onClick={toggleSort} /></div>
          <div style={colAction} />
        </div>

        {filtered.slice(0, 30).map((p, i) => (
          <ProfileRow key={p.email} p={p} idx={i} onOpen={onOpenDetail} />
        ))}
      </div>
    </div>
  );
}

function HeaderCell({ label, k, sortKey, sortDir, onClick, right }) {
  const active = sortKey === k;
  return (
    <button
      onClick={() => onClick(k)}
      style={{
        background: 'none', border: 'none', padding: 0, cursor: 'pointer',
        fontSize: 10, fontFamily: TOKENS.mono, letterSpacing: '0.08em',
        color: active ? TOKENS.text : TOKENS.textMute,
        display: 'flex', alignItems: 'center', gap: 4,
        marginLeft: right ? 'auto' : 0,
      }}
    >
      <span>{label.toUpperCase()}</span>
      {active && (
        <span style={{ fontSize: 8 }}>{sortDir === 'asc' ? '▲' : '▼'}</span>
      )}
    </button>
  );
}

function ProfileRow({ p, idx, onOpen }) {
  const [hover, setHover] = React.useState(false);
  const { fmtDate } = window.profileHelpers;
  return (
    <div
      onClick={() => onOpen && onOpen(p.email)}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        ...tableRow,
        cursor: 'pointer',
        background: hover ? TOKENS.rowHover : 'transparent',
      }}
    >
      <div style={{ ...colEmail, display: 'flex', alignItems: 'center', gap: 10 }}>
        <Avatar name={`${p.firstName} ${p.lastName}`} size={22} />
        <span style={{ fontFamily: TOKENS.mono, fontSize: 12, color: TOKENS.text, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {p.email}
        </span>
      </div>
      <div style={colStatus}><StatusPill status={p.status} /></div>
      <div style={{ ...colDate, fontFamily: TOKENS.mono, fontSize: 11, color: TOKENS.textDim }}>{fmtDate(p.profileDate)}</div>
      <div style={colChannel}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
          <ChannelBadge channel={p.channel} source={p.source} />
          {p.source && (
            <span style={{ fontFamily: TOKENS.mono, fontSize: 11, color: TOKENS.textMute, overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {p.source}
            </span>
          )}
        </div>
      </div>
      <div style={{ ...colLoc, fontFamily: TOKENS.mono, fontSize: 11, color: TOKENS.textDim }}>
        {p.city}, {p.country.length > 12 ? p.country.slice(0, 10) + '…' : p.country}
      </div>
      <div style={colEngage}>
        <EngagementBadges p={p} />
      </div>
      <div style={{ ...colDays, fontFamily: TOKENS.mono, fontSize: 11, color: p.daysFirstToSignup == null ? TOKENS.textMute : TOKENS.textDim, textAlign: 'right' }}>
        {p.daysFirstToSignup == null ? '—' : p.daysFirstToSignup + 'd'}
      </div>
      <div style={{ ...colDays, fontFamily: TOKENS.mono, fontSize: 11, color: p.daysFirstToCustomer == null ? TOKENS.textMute : p.daysFirstToCustomer < 0 ? '#fbbf24' : TOKENS.textDim, textAlign: 'right' }}>
        {p.daysFirstToCustomer == null ? '—' : p.daysFirstToCustomer + 'd'}
      </div>
      <div style={{ ...colName, fontSize: 12, color: TOKENS.textDim }}>
        {p.firstName} {p.lastName}
      </div>
      <div style={{ ...colAction, color: hover ? TOKENS.text : TOKENS.textMute, textAlign: 'right' }}>
        <Icon.chevRight />
      </div>
    </div>
  );
}

// Inline engagement stripe. Replaces the old "First form" column and
// surfaces the three engagement types (forms / webinars / calls) so the
// table tells you _how_ a profile engaged, not just _if_ they did.
function EngagementBadges({ p }) {
  const items = [];
  if (p.formSubmissionsCount > 0) items.push({ icon: <Icon.form />, count: p.formSubmissionsCount, color: TOKENS.form, bg: TOKENS.formDim, title: 'Form submissions' });
  if (p.webinarCount > 0) items.push({ icon: <Icon.video />, count: p.webinarCount, color: TOKENS.webinar, bg: TOKENS.webinarDim, title: 'Webinar registrations' });
  if (p.calendlyCount > 0) items.push({ icon: <Icon.calendar />, count: p.calendlyCount, color: TOKENS.call, bg: TOKENS.callDim, title: 'Calendly bookings' });
  if (items.length === 0) {
    return <span style={{ fontFamily: TOKENS.mono, fontSize: 11, color: TOKENS.textMute }}>—</span>;
  }
  return (
    <div style={{ display: 'flex', gap: 5 }}>
      {items.map((it, i) => (
        <span key={i} title={it.title} style={{
          display: 'inline-flex', alignItems: 'center', gap: 4,
          padding: '2px 6px', borderRadius: 3,
          fontSize: 10, fontFamily: TOKENS.mono,
          background: it.bg, color: it.color,
          border: `1px solid ${it.color}22`,
        }}>
          {it.icon}
          <span>{it.count}</span>
        </span>
      ))}
    </div>
  );
}

function Kpi({ label, value, sub, color }) {
  return (
    <div style={{
      background: TOKENS.surface, border: `1px solid ${TOKENS.border}`,
      borderRadius: 8, padding: '14px 16px',
    }}>
      <div style={{ fontSize: 10, fontFamily: TOKENS.mono, color: TOKENS.textMute, letterSpacing: '0.1em', marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ fontSize: 28, fontWeight: 500, letterSpacing: '-0.02em', color: color || TOKENS.text, fontFamily: TOKENS.mono }}>
        {value.toLocaleString()}
      </div>
      {sub && (
        <div style={{ fontSize: 11, fontFamily: TOKENS.mono, color: TOKENS.textMute, marginTop: 4 }}>
          {sub}
        </div>
      )}
    </div>
  );
}

// ─────────── styles ───────────
const ghostBtn = {
  display: 'inline-flex', alignItems: 'center', gap: 6,
  background: TOKENS.surface, color: TOKENS.textDim,
  border: `1px solid ${TOKENS.border}`, borderRadius: 6,
  padding: '6px 12px', fontSize: 12, cursor: 'pointer',
  fontFamily: TOKENS.sans,
};
const primaryBtn = {
  ...ghostBtn,
  background: TOKENS.accentDim, color: TOKENS.accent,
  border: `1px solid ${TOKENS.accent}33`,
};
const searchInput = {
  width: '100%', padding: '7px 10px 7px 30px',
  background: TOKENS.surface, color: TOKENS.text,
  border: `1px solid ${TOKENS.border}`, borderRadius: 6,
  fontSize: 12, fontFamily: TOKENS.sans, outline: 'none',
};
const segBtn = {
  border: 'none', padding: '5px 12px', borderRadius: 4,
  fontSize: 11, fontFamily: TOKENS.sans, cursor: 'pointer',
};
const sourceStrip = {
  display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap',
  padding: '10px 12px', marginBottom: 14,
  background: TOKENS.bg2, borderRadius: 8,
  border: `1px solid ${TOKENS.border}`,
};
const sourceChip = {
  display: 'inline-flex', alignItems: 'center', gap: 6,
  padding: '4px 9px', borderRadius: 4,
  fontSize: 11, fontFamily: TOKENS.mono,
  cursor: 'pointer',
  border: `1px solid ${TOKENS.border}`,
  background: 'transparent',
  color: TOKENS.textDim,
};
const tableWrap = {
  background: TOKENS.bg2, border: `1px solid ${TOKENS.border}`,
  borderRadius: 8, overflow: 'hidden',
};
const tableRow = {
  display: 'grid',
  gridTemplateColumns: 'minmax(220px,2fr) 110px 100px 210px 150px 130px 80px 90px 120px 28px',
  padding: '10px 14px',
  borderBottom: `1px solid ${TOKENS.border}`,
  alignItems: 'center', gap: 12,
};
const tableHeader = {
  background: TOKENS.surface,
  padding: '8px 14px',
};
const colEmail = { minWidth: 0 };
const colStatus = {};
const colDate = {};
const colChannel = { minWidth: 0 };
const colLoc = { minWidth: 0, overflow: 'hidden' };
const colEngage = {};
const colDays = {};
const colName = {};
const colAction = {};

window.ProfilesList = ProfilesList;
