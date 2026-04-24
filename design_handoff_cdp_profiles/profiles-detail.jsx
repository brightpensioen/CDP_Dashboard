// Profile detail page — dedicated route that shows everything about one
// profile, with a Pipedrive-style activity timeline as the centerpiece.
// Left column: identity + KPIs + acquisition + DAS.
// Right column (main): activity timeline grouped by day, filterable by type.

function ProfileDetail({ profile, onBack }) {
  const { fmtDate, fmtDateTime, now } = window.profileHelpers;
  const [activityFilter, setActivityFilter] = React.useState('all');
  const [tab, setTab] = React.useState('timeline');

  const filteredActivities = React.useMemo(() => {
    if (activityFilter === 'all') return profile.activities;
    if (activityFilter === 'engagement') {
      return profile.activities.filter(a =>
        ['form_submission', 'webinar_registration', 'calendly_booking'].includes(a.type));
    }
    return profile.activities.filter(a => a.type === activityFilter);
  }, [profile, activityFilter]);

  // Group by day for the timeline lane.
  const grouped = React.useMemo(() => {
    const map = new Map();
    filteredActivities.forEach(a => {
      const d = fmtDate(a.date);
      if (!map.has(d)) map.set(d, []);
      map.get(d).push(a);
    });
    return Array.from(map.entries());
  }, [filteredActivities]);

  const counts = React.useMemo(() => {
    const c = { form_submission: 0, webinar_registration: 0, calendly_booking: 0 };
    profile.activities.forEach(a => { if (c[a.type] != null) c[a.type]++; });
    return c;
  }, [profile]);

  const statusMeta = STATUS_META[profile.status] || STATUS_META.lead;

  return (
    <div style={{
      background: TOKENS.bg, color: TOKENS.text, fontFamily: TOKENS.sans,
      minHeight: '100%', fontSize: 13,
    }}>
      {/* Top bar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '12px 24px', borderBottom: `1px solid ${TOKENS.border}`,
        background: TOKENS.bg2, position: 'sticky', top: 0, zIndex: 10,
      }}>
        <button onClick={onBack} style={{
          ...backBtn
        }}>
          <Icon.arrowLeft /> Profiles
        </button>
        <span style={{ fontSize: 10, fontFamily: TOKENS.mono, color: TOKENS.textMute, letterSpacing: '0.1em' }}>
          / PROFILE DETAIL
        </span>
        <span style={{ fontFamily: TOKENS.mono, fontSize: 12, color: TOKENS.textDim }}>
          {profile.email}
        </span>
        <div style={{ flex: 1 }} />
        <button style={smallGhost}><Icon.external /> Open in DAS</button>
        <button style={smallGhost}><Icon.download /> Export</button>
        <button style={smallGhost}><Icon.dots /></button>
      </div>

      {/* Header card */}
      <div style={{
        display: 'flex', gap: 20, alignItems: 'flex-start',
        padding: '24px 32px',
        borderBottom: `1px solid ${TOKENS.border}`,
      }}>
        <Avatar name={`${profile.firstName} ${profile.lastName}`} size={64} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
            <h1 style={{ fontSize: 22, fontWeight: 600, margin: 0, letterSpacing: '-0.01em' }}>
              {profile.firstName} {profile.lastName}
            </h1>
            <StatusPill status={profile.status} />
            {profile.das && (
              <span style={{
                fontSize: 10, fontFamily: TOKENS.mono,
                padding: '2px 7px', borderRadius: 3,
                background: 'rgba(154,163,173,0.08)',
                color: TOKENS.textDim, letterSpacing: '0.05em',
                border: `1px solid ${TOKENS.border}`,
              }}>
                DAS #{profile.das.participant}
              </span>
            )}
          </div>
          <div style={{ fontFamily: TOKENS.mono, fontSize: 12, color: TOKENS.textDim, marginBottom: 10 }}>
            {profile.email}
          </div>
          <div style={{ display: 'flex', gap: 24, fontSize: 11, fontFamily: TOKENS.mono, color: TOKENS.textMute, flexWrap: 'wrap' }}>
            <MetaChip icon={<Icon.globe />} label={`${profile.city}, ${profile.country}`} />
            <MetaChip icon={<Icon.calendar />} label={`First seen ${fmtDate(profile.firstSessionDate)}`} />
            {profile.das && <MetaChip icon={<Icon.euro />} label={`Member since ${fmtDate(profile.das.memberSince)}`} />}
            <MetaChip icon={<Icon.user />} label={`${profile.device} · ${profile.browser} · ${profile.os}`} />
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }} />
      </div>

      {/* KPI strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', borderBottom: `1px solid ${TOKENS.border}` }}>
        <MiniStat label="DAYS ACTIVE" value={Math.max(0, Math.round((now - profile.firstSessionDate) / 86400000))} suffix="d" />
        <MiniStat label="FORM SUBMISSIONS" value={counts.form_submission} color={TOKENS.form} />
        <MiniStat label="WEBINAR REGISTRATIONS" value={counts.webinar_registration} color={TOKENS.webinar} />
        <MiniStat label="CALLS BOOKED" value={counts.calendly_booking} color={TOKENS.call} />
        <MiniStat label="→ SIGNUP" value={profile.daysFirstToSignup == null ? '—' : profile.daysFirstToSignup + 'd'} />
        <MiniStat label="→ CUSTOMER" value={profile.daysFirstToCustomer == null ? '—' : profile.daysFirstToCustomer + 'd'}
          color={profile.daysFirstToCustomer != null && profile.daysFirstToCustomer < 0 ? TOKENS.signed : null} />
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 0, padding: '0 32px', borderBottom: `1px solid ${TOKENS.border}` }}>
        {[
          ['timeline', 'Activity timeline', profile.activities.length],
          ['engagements', 'Engagements', counts.form_submission + counts.webinar_registration + counts.calendly_booking],
          ['acquisition', 'Acquisition', null],
          ['das', 'DAS / Member', profile.das ? 1 : 0],
          ['raw', 'Raw data', null],
        ].map(([k, label, count]) => (
          <button
            key={k}
            onClick={() => setTab(k)}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              padding: '12px 0', marginRight: 24,
              fontSize: 12, fontFamily: TOKENS.sans,
              color: tab === k ? TOKENS.text : TOKENS.textMute,
              borderBottom: `2px solid ${tab === k ? TOKENS.accent : 'transparent'}`,
              display: 'inline-flex', alignItems: 'center', gap: 6,
              marginBottom: -1,
            }}
          >
            {label}
            {count != null && count > 0 && (
              <span style={{
                fontSize: 10, fontFamily: TOKENS.mono,
                padding: '1px 6px', borderRadius: 2,
                background: tab === k ? TOKENS.accentDim : TOKENS.surface,
                color: tab === k ? TOKENS.accent : TOKENS.textMute,
              }}>{count}</span>
            )}
          </button>
        ))}
      </div>

      {/* Body */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 0 }}>
        {/* Main column */}
        <div style={{ padding: '24px 32px', minWidth: 0 }}>
          {tab === 'timeline' && (
            <TimelineView
              grouped={grouped}
              activityFilter={activityFilter}
              setActivityFilter={setActivityFilter}
              counts={counts}
              totalCount={profile.activities.length}
            />
          )}
          {tab === 'engagements' && <EngagementsView profile={profile} />}
          {tab === 'acquisition' && <AcquisitionView profile={profile} />}
          {tab === 'das' && <DasView profile={profile} />}
          {tab === 'raw' && <RawView profile={profile} />}
        </div>

        {/* Right rail */}
        <div style={{
          borderLeft: `1px solid ${TOKENS.border}`,
          background: TOKENS.bg2,
          padding: '24px 24px',
        }}>
          <RightRail profile={profile} />
        </div>
      </div>
    </div>
  );
}

// ─────────── Timeline view (the centerpiece) ───────────
function TimelineView({ grouped, activityFilter, setActivityFilter, counts, totalCount }) {
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 18, flexWrap: 'wrap' }}>
        <h2 style={{ fontSize: 14, fontWeight: 600, margin: 0, marginRight: 8 }}>Activity</h2>
        <div style={{ display: 'flex', gap: 4, background: TOKENS.surface, border: `1px solid ${TOKENS.border}`, borderRadius: 6, padding: 3 }}>
          <FilterChip active={activityFilter === 'all'} onClick={() => setActivityFilter('all')}>All <span style={{ opacity: 0.5 }}>{totalCount}</span></FilterChip>
          <FilterChip active={activityFilter === 'engagement'} onClick={() => setActivityFilter('engagement')} color={TOKENS.accent}>Engagement</FilterChip>
          <FilterChip active={activityFilter === 'form_submission'} onClick={() => setActivityFilter('form_submission')} color={TOKENS.form}>
            <Icon.form /> Forms {counts.form_submission > 0 && <span style={{ opacity: 0.6 }}>{counts.form_submission}</span>}
          </FilterChip>
          <FilterChip active={activityFilter === 'webinar_registration'} onClick={() => setActivityFilter('webinar_registration')} color={TOKENS.webinar}>
            <Icon.video /> Webinars {counts.webinar_registration > 0 && <span style={{ opacity: 0.6 }}>{counts.webinar_registration}</span>}
          </FilterChip>
          <FilterChip active={activityFilter === 'calendly_booking'} onClick={() => setActivityFilter('calendly_booking')} color={TOKENS.call}>
            <Icon.calendar /> Calls {counts.calendly_booking > 0 && <span style={{ opacity: 0.6 }}>{counts.calendly_booking}</span>}
          </FilterChip>
        </div>
      </div>

      {/* Timeline */}
      {grouped.length === 0 ? (
        <div style={{ padding: 40, textAlign: 'center', color: TOKENS.textMute, fontSize: 12, fontFamily: TOKENS.mono }}>
          No activities for this filter.
        </div>
      ) : (
        <div style={{ position: 'relative' }}>
          {/* Vertical rail */}
          <div style={{
            position: 'absolute', left: 11, top: 8, bottom: 8,
            width: 1, background: TOKENS.border,
          }} />
          {grouped.map(([day, events], di) => (
            <div key={day} style={{ marginBottom: 24 }}>
              <DayHeader day={day} />
              <div style={{ marginTop: 10 }}>
                {events.map((e, i) => <TimelineEvent key={i} event={e} />)}
              </div>
            </div>
          ))}
          {/* Genesis cap at bottom */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 12,
            marginLeft: 0, color: TOKENS.textMute, fontSize: 11, fontFamily: TOKENS.mono,
          }}>
            <div style={{
              width: 22, height: 22, borderRadius: '50%',
              background: TOKENS.bg, border: `1px dashed ${TOKENS.borderHi}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: TOKENS.textMute, fontSize: 10,
            }}>✦</div>
            <span>Profile begins</span>
          </div>
        </div>
      )}
    </div>
  );
}

function DayHeader({ day }) {
  const { now } = window.profileHelpers;
  const d = new Date(day);
  const today = new Date(now); today.setHours(0,0,0,0);
  const diffDays = Math.round((today - d) / 86400000);
  let rel = '';
  if (diffDays === 0) rel = 'Today';
  else if (diffDays === 1) rel = 'Yesterday';
  else if (diffDays < 0) rel = `in ${-diffDays}d`;
  else if (diffDays < 30) rel = `${diffDays}d ago`;
  else if (diffDays < 365) rel = `${Math.floor(diffDays/30)}mo ago`;
  else rel = `${Math.floor(diffDays/365)}y ago`;
  const formatted = d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      paddingLeft: 32, marginBottom: 2,
    }}>
      <span style={{ fontSize: 11, fontFamily: TOKENS.mono, color: TOKENS.textDim, fontWeight: 500 }}>
        {formatted}
      </span>
      <span style={{ fontSize: 10, fontFamily: TOKENS.mono, color: TOKENS.textMute, letterSpacing: '0.05em' }}>
        {rel}
      </span>
    </div>
  );
}

function TimelineEvent({ event }) {
  const meta = ACTIVITY_META[event.type] || ACTIVITY_META.first_session;
  const { fmtDate, fmtDateTime } = window.profileHelpers;
  const t = event.date.toISOString().slice(11, 16);

  const iconFor = {
    first_session: <Icon.globe />,
    form_submission: <Icon.form />,
    webinar_registration: <Icon.video />,
    calendly_booking: <Icon.calendar />,
    signup: <Icon.user />,
    customer: <Icon.euro />,
    paying_started: <Icon.euro />,
  }[event.type] || <Icon.dots />;

  return (
    <div style={{ display: 'flex', gap: 10, marginBottom: 8, position: 'relative' }}>
      {/* Node */}
      <div style={{
        width: 22, height: 22, borderRadius: '50%',
        background: meta.bg, color: meta.color,
        border: `1px solid ${meta.color}44`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0, zIndex: 1, marginTop: 2,
      }}>
        {iconFor}
      </div>
      {/* Card */}
      <div style={{
        flex: 1, minWidth: 0,
        background: TOKENS.surface, border: `1px solid ${TOKENS.border}`,
        borderRadius: 6, padding: '10px 14px',
        borderLeft: `2px solid ${meta.color}88`,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
          <span style={{ fontSize: 12, fontWeight: 500, color: TOKENS.text }}>
            {renderEventTitle(event)}
          </span>
          <span style={{
            fontSize: 9, padding: '1px 6px', borderRadius: 2,
            background: meta.bg, color: meta.color,
            fontFamily: TOKENS.mono, letterSpacing: '0.05em',
          }}>
            {meta.label.toUpperCase()}
          </span>
          <div style={{ flex: 1 }} />
          <span style={{ fontSize: 10, fontFamily: TOKENS.mono, color: TOKENS.textMute }}>{t}</span>
        </div>
        {renderEventBody(event)}
      </div>
    </div>
  );
}

function renderEventTitle(e) {
  switch (e.type) {
    case 'first_session':        return 'First session started';
    case 'form_submission':      return `Submitted "${e.form}"`;
    case 'webinar_registration': return `Registered for webinar`;
    case 'calendly_booking':     return `Booked "${e.eventType}"`;
    case 'signup':               return 'Created account';
    case 'customer':             return 'Became paying customer';
    case 'paying_started':       return 'First payment received';
    default:                     return e.type;
  }
}

function renderEventBody(e) {
  const { fmtDate, fmtDateTime } = window.profileHelpers;
  const row = (label, value) => (
    <div style={{ display: 'flex', gap: 8, fontSize: 11, fontFamily: TOKENS.mono }}>
      <span style={{ color: TOKENS.textMute, minWidth: 80 }}>{label}</span>
      <span style={{ color: TOKENS.textDim }}>{value}</span>
    </div>
  );
  switch (e.type) {
    case 'first_session':
      return (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2px 20px', marginTop: 4 }}>
          {row('channel', e.channel)}
          {row('device', `${e.device} · ${e.browser}`)}
          {row('source', e.source || '(none)')}
          {row('location', `${e.city}, ${e.country}`)}
          {row('medium', e.medium)}
          {row('campaign', e.campaign)}
        </div>
      );
    case 'webinar_registration':
      return (
        <div style={{ marginTop: 4 }}>
          <div style={{ fontSize: 12, color: TOKENS.text, marginBottom: 3 }}>{e.title}</div>
          {row('scheduled', fmtDateTime(e.webinarDate) + ' UTC')}
        </div>
      );
    case 'calendly_booking':
      return (
        <div style={{ marginTop: 4 }}>
          {row('scheduled', fmtDateTime(e.eventStart) + ' UTC')}
          {row('duration', `${e.duration} minutes`)}
        </div>
      );
    case 'form_submission':
      return (
        <div style={{ marginTop: 4 }}>
          {row('form', e.form)}
        </div>
      );
    case 'customer':
      return (
        <div style={{ marginTop: 4 }}>
          {row('participant', e.participant)}
        </div>
      );
    default:
      return null;
  }
}

function FilterChip({ children, active, onClick, color }) {
  return (
    <button onClick={onClick} style={{
      border: 'none', padding: '5px 10px', borderRadius: 4,
      fontSize: 11, fontFamily: TOKENS.sans, cursor: 'pointer',
      display: 'inline-flex', alignItems: 'center', gap: 5,
      background: active ? TOKENS.surfaceHi : 'transparent',
      color: active ? (color || TOKENS.text) : TOKENS.textDim,
    }}>{children}</button>
  );
}

// ─────────── Other tabs ───────────
function EngagementsView({ profile }) {
  const forms = profile.activities.filter(a => a.type === 'form_submission');
  const webinars = profile.activities.filter(a => a.type === 'webinar_registration');
  const calls = profile.activities.filter(a => a.type === 'calendly_booking');
  return (
    <div style={{ display: 'grid', gap: 20 }}>
      <EngagementBucket title="Form submissions" items={forms} emptyText="No forms submitted yet."
        color={TOKENS.form} icon={<Icon.form />}
        renderItem={(f) => (
          <div>
            <div style={{ fontSize: 12, fontFamily: TOKENS.mono, color: TOKENS.text }}>{f.form}</div>
            <div style={{ fontSize: 11, fontFamily: TOKENS.mono, color: TOKENS.textMute }}>
              {window.profileHelpers.fmtDateTime(f.date)}
            </div>
          </div>
        )} />
      <EngagementBucket title="Webinar registrations" items={webinars} emptyText="No webinar registrations yet."
        color={TOKENS.webinar} icon={<Icon.video />}
        renderItem={(w) => (
          <div>
            <div style={{ fontSize: 12, color: TOKENS.text }}>{w.title}</div>
            <div style={{ fontSize: 11, fontFamily: TOKENS.mono, color: TOKENS.textMute }}>
              Registered {window.profileHelpers.fmtDateTime(w.date)} · Scheduled {window.profileHelpers.fmtDate(w.webinarDate)}
            </div>
          </div>
        )} />
      <EngagementBucket title="Calendly bookings" items={calls} emptyText="No calls booked yet."
        color={TOKENS.call} icon={<Icon.calendar />}
        renderItem={(c) => (
          <div>
            <div style={{ fontSize: 12, color: TOKENS.text }}>{c.eventType}</div>
            <div style={{ fontSize: 11, fontFamily: TOKENS.mono, color: TOKENS.textMute }}>
              Scheduled {window.profileHelpers.fmtDateTime(c.eventStart)} · {c.duration} min
            </div>
          </div>
        )} />
    </div>
  );
}

function EngagementBucket({ title, items, color, icon, renderItem, emptyText }) {
  return (
    <div style={{
      background: TOKENS.surface, border: `1px solid ${TOKENS.border}`,
      borderRadius: 8, overflow: 'hidden',
    }}>
      <div style={{
        padding: '10px 14px', borderBottom: `1px solid ${TOKENS.border}`,
        display: 'flex', alignItems: 'center', gap: 8,
        background: TOKENS.bg2,
      }}>
        <span style={{ color, display: 'inline-flex' }}>{icon}</span>
        <span style={{ fontSize: 12, fontWeight: 600 }}>{title}</span>
        <span style={{ fontSize: 11, fontFamily: TOKENS.mono, color: TOKENS.textMute }}>
          {items.length}
        </span>
      </div>
      {items.length === 0 ? (
        <div style={{ padding: 20, color: TOKENS.textMute, fontSize: 12 }}>{emptyText}</div>
      ) : (
        items.map((it, i) => (
          <div key={i} style={{ padding: '10px 14px', borderBottom: i < items.length - 1 ? `1px solid ${TOKENS.border}` : 'none' }}>
            {renderItem(it)}
          </div>
        ))
      )}
    </div>
  );
}

function AcquisitionView({ profile }) {
  const rows = [
    ['Channel',  profile.channel],
    ['Source',   profile.source || '(none)'],
    ['Medium',   profile.medium],
    ['Campaign', profile.campaign],
    ['Country',  profile.country],
    ['City',     profile.city],
    ['Device',   profile.device],
    ['Browser',  profile.browser],
    ['OS',       profile.os],
  ];
  return (
    <div style={detailCard}>
      <DetailCardHeader>Acquisition</DetailCardHeader>
      <div style={{ padding: '4px 0' }}>
        {rows.map(([l, v]) => <DetailRow key={l} label={l} value={v} />)}
      </div>
    </div>
  );
}

function DasView({ profile }) {
  const { fmtDate } = window.profileHelpers;
  if (!profile.das) {
    return (
      <div style={{ ...detailCard, padding: 20, color: TOKENS.textMute, fontSize: 12 }}>
        This profile is not yet a DAS member.
      </div>
    );
  }
  const rows = [
    ['DAS ID',          profile.das.id],
    ['Participant #',   profile.das.participant],
    ['Member since',    fmtDate(profile.das.memberSince)],
    ['Paying since',    fmtDate(profile.das.payingSince)],
    ['Retirement date', fmtDate(profile.das.retirementDate)],
    ['Status',          profile.das.status === 1 ? 'Active' : 'Inactive'],
  ];
  return (
    <div style={detailCard}>
      <DetailCardHeader>DAS / Member</DetailCardHeader>
      <div style={{ padding: '4px 0' }}>
        {rows.map(([l, v]) => <DetailRow key={l} label={l} value={v} mono />)}
      </div>
    </div>
  );
}

function RawView({ profile }) {
  const json = JSON.stringify(profile, (k, v) => {
    if (v instanceof Date) return v.toISOString();
    return v;
  }, 2);
  return (
    <pre style={{
      background: TOKENS.surface, border: `1px solid ${TOKENS.border}`,
      borderRadius: 8, padding: 16,
      fontFamily: TOKENS.mono, fontSize: 11, color: TOKENS.textDim,
      overflow: 'auto', maxHeight: 700,
    }}>{json}</pre>
  );
}

// ─────────── Right rail ───────────
function RightRail({ profile }) {
  const { fmtDate } = window.profileHelpers;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      <RailSection title="Snapshot">
        <SnapRow label="Lifecycle" value={<StatusPill status={profile.status} />} />
        <SnapRow label="Lead score" value={
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 60, height: 4, background: TOKENS.bg3, borderRadius: 2, overflow: 'hidden' }}>
              <div style={{ width: (profile.status === 'customer' ? 92 : profile.status === 'signed-up' ? 68 : 34) + '%', height: '100%', background: TOKENS.accent }} />
            </div>
            <span style={{ fontFamily: TOKENS.mono, fontSize: 11 }}>
              {profile.status === 'customer' ? 92 : profile.status === 'signed-up' ? 68 : 34}
            </span>
          </div>
        } />
        <SnapRow label="Last activity" value={
          <span style={{ fontFamily: TOKENS.mono, fontSize: 11 }}>
            {relTime(profile.activities[0]?.date || profile.firstSessionDate, window.profileHelpers.now)}
          </span>
        } />
      </RailSection>

      <RailSection title="Upcoming">
        {(() => {
          const upcoming = profile.activities
            .filter(a => (a.type === 'calendly_booking' && a.eventStart > window.profileHelpers.now)
              || (a.type === 'webinar_registration' && a.webinarDate > window.profileHelpers.now))
            .sort((a, b) => (a.eventStart || a.webinarDate) - (b.eventStart || b.webinarDate));
          if (upcoming.length === 0) return <div style={{ fontSize: 11, color: TOKENS.textMute, fontFamily: TOKENS.mono }}>Nothing scheduled.</div>;
          return upcoming.map((u, i) => {
            const isCall = u.type === 'calendly_booking';
            const date = isCall ? u.eventStart : u.webinarDate;
            const color = isCall ? TOKENS.call : TOKENS.webinar;
            const bg = isCall ? TOKENS.callDim : TOKENS.webinarDim;
            return (
              <div key={i} style={{
                display: 'flex', gap: 10, alignItems: 'flex-start',
                padding: '8px 10px', borderRadius: 6,
                background: bg, border: `1px solid ${color}22`,
                marginBottom: 6,
              }}>
                <div style={{ color, marginTop: 2 }}>{isCall ? <Icon.calendar /> : <Icon.video />}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 11, color: TOKENS.text, marginBottom: 2 }}>
                    {isCall ? u.eventType : u.title}
                  </div>
                  <div style={{ fontSize: 10, fontFamily: TOKENS.mono, color: TOKENS.textMute }}>
                    {fmtDate(date)} · {relTime(date, window.profileHelpers.now)}
                  </div>
                </div>
              </div>
            );
          });
        })()}
      </RailSection>

      <RailSection title="Quick stats">
        <SnapRow label="First session" value={<span style={{ fontFamily: TOKENS.mono, fontSize: 11 }}>{fmtDate(profile.firstSessionDate)}</span>} />
        {profile.signupDate && (
          <SnapRow label="Signed up" value={<span style={{ fontFamily: TOKENS.mono, fontSize: 11 }}>{fmtDate(profile.signupDate)}</span>} />
        )}
        {profile.das && (
          <SnapRow label="Customer" value={<span style={{ fontFamily: TOKENS.mono, fontSize: 11 }}>{fmtDate(profile.das.memberSince)}</span>} />
        )}
        <SnapRow label="All client IDs" value={<span style={{ fontFamily: TOKENS.mono, fontSize: 10, color: TOKENS.textMute }}>1 match</span>} />
      </RailSection>

      <RailSection title="Attribution">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <ChannelBadge channel={profile.channel} />
        </div>
        <div style={{ fontSize: 11, fontFamily: TOKENS.mono, color: TOKENS.textMute, lineHeight: 1.6 }}>
          <div>source: {profile.source || '—'}</div>
          <div>medium: {profile.medium}</div>
          <div>campaign: {profile.campaign}</div>
        </div>
      </RailSection>
    </div>
  );
}

function RailSection({ title, children }) {
  return (
    <div>
      <div style={{
        fontSize: 10, fontFamily: TOKENS.mono, color: TOKENS.textMute,
        letterSpacing: '0.1em', marginBottom: 10,
      }}>{title.toUpperCase()}</div>
      {children}
    </div>
  );
}

function SnapRow({ label, value }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '5px 0', borderBottom: `1px solid ${TOKENS.border}`,
    }}>
      <span style={{ fontSize: 11, color: TOKENS.textMute, fontFamily: TOKENS.mono }}>{label}</span>
      {value}
    </div>
  );
}

function DetailRow({ label, value, mono }) {
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '160px 1fr', gap: 16,
      padding: '8px 16px', borderBottom: `1px solid ${TOKENS.border}`,
      alignItems: 'center',
    }}>
      <span style={{ fontSize: 11, fontFamily: TOKENS.mono, color: TOKENS.textMute, letterSpacing: '0.03em' }}>
        {label}
      </span>
      <span style={{ fontSize: 12, fontFamily: mono ? TOKENS.mono : TOKENS.sans, color: TOKENS.text }}>
        {value == null || value === '' ? <span style={{ color: TOKENS.textMute }}>—</span> : value}
      </span>
    </div>
  );
}

function DetailCardHeader({ children }) {
  return (
    <div style={{
      padding: '10px 16px', borderBottom: `1px solid ${TOKENS.border}`,
      fontSize: 12, fontWeight: 600, background: TOKENS.bg2,
    }}>{children}</div>
  );
}

function MetaChip({ icon, label }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
      <span style={{ color: TOKENS.textMute, display: 'inline-flex' }}>{icon}</span>
      <span>{label}</span>
    </span>
  );
}

function MiniStat({ label, value, suffix, color }) {
  return (
    <div style={{
      padding: '14px 18px',
      borderRight: `1px solid ${TOKENS.border}`,
    }}>
      <div style={{ fontSize: 9, fontFamily: TOKENS.mono, color: TOKENS.textMute, letterSpacing: '0.1em', marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontSize: 22, fontWeight: 500, fontFamily: TOKENS.mono, color: color || TOKENS.text, letterSpacing: '-0.02em' }}>
        {value}{suffix || ''}
      </div>
    </div>
  );
}

// ─────────── styles ───────────
const backBtn = {
  display: 'inline-flex', alignItems: 'center', gap: 6,
  background: TOKENS.surface, color: TOKENS.textDim,
  border: `1px solid ${TOKENS.border}`, borderRadius: 6,
  padding: '5px 10px', fontSize: 11, cursor: 'pointer',
  fontFamily: TOKENS.sans,
};
const smallGhost = {
  display: 'inline-flex', alignItems: 'center', gap: 5,
  background: 'transparent', color: TOKENS.textDim,
  border: `1px solid ${TOKENS.border}`, borderRadius: 5,
  padding: '5px 10px', fontSize: 11, cursor: 'pointer',
  fontFamily: TOKENS.sans,
};
const smallPrimary = {
  ...smallGhost,
  background: TOKENS.accentDim, color: TOKENS.accent,
  border: `1px solid ${TOKENS.accent}33`,
};
const composerChip = {
  background: 'transparent', color: TOKENS.textDim,
  border: `1px solid ${TOKENS.border}`, borderRadius: 4,
  padding: '3px 10px', fontSize: 11, cursor: 'pointer',
  fontFamily: TOKENS.sans,
};
const detailCard = {
  background: TOKENS.surface, border: `1px solid ${TOKENS.border}`,
  borderRadius: 8, overflow: 'hidden',
};

window.ProfileDetail = ProfileDetail;
