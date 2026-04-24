// Mock data + helpers for the profiles prototype.
// Matches the BigQuery schema the user shared, expanded with activity
// timeline entries so the detail page has something to show.

const now = new Date('2026-04-23T14:00:00Z');

const CHANNELS = [
  'Direct', 'Organic Search', 'Paid Search', 'Affiliates', 'Referral',
  'Email', 'Calendly', 'WebinarGeek', 'Social',
];

const SOURCES_BY_CHANNEL = {
  'Direct': [''],
  'Organic Search': ['google', 'bing', 'duckduckgo'],
  'Paid Search': ['google', 'bing'],
  'Affiliates': ['daisycon', 'awin', 'tradetracker'],
  'Referral': ['brightpensioen.nl', 'findest.nl', 'consumentenbond.nl'],
  'Email': ['newsletter', 'lifecycle', 'transactional'],
  'Calendly': ['calendly'],
  'WebinarGeek': ['webinargeek'],
  'Social': ['linkedin', 'facebook', 'instagram'],
};

const FIRST_NAMES = [
  'Johan', 'Otis', 'Jurgen', 'Richard', 'Info', 'Marek', 'Dick',
  'Marieke', 'Matthijs', 'Mick', 'Joeri', 'Kalata', 'Dorien', 'Royale',
  'Sanne', 'Bas', 'Maartje', 'Hugo', 'Eva', 'Thijs', 'Lotte', 'Pieter',
  'Anouk', 'Bram', 'Ilse', 'Tim', 'Sophie', 'Daan', 'Fleur', 'Sven',
  'Marit', 'Jeroen', 'Femke', 'Koen', 'Saskia', 'Wouter', 'Linde',
];
const LAST_NAMES = [
  'Maessen', 'Hermsen', 'Plugge', 'Kleinsman', 'Horstman', 'Lange',
  'Verstegen', 'Alphen', 'Westenberg', 'de Vries', 'Jansen', 'Bakker',
  'Visser', 'Smit', 'Meijer', 'Boer', 'Mulder', 'Peters', 'Hendriks',
];
const CITIES = [
  ['Utrecht', 'Netherlands'], ['Amsterdam', 'Netherlands'],
  ['Rotterdam', 'Netherlands'], ['Eindhoven', 'Netherlands'],
  ['Nagerlingen', 'Netherlands'], ['Haaksbergen', 'Netherlands'],
  ['The Hague', 'Netherlands'], ['Madrid', 'Spain'],
  ['Palestine', 'Netherlands'], ['Maasnaar', 'Netherlands'],
  ['Groningen', 'Netherlands'], ['Leiden', 'Netherlands'],
  ['Nijmegen', 'Netherlands'], ['Tilburg', 'Netherlands'],
];
const FORMS = [
  'jaarruimte', 'inschrijven-start-individu', 'contact', 'brochure-aanvraag',
  'pensioenscan', 'nieuwsbrief', 'jaaroverzicht',
];
const WEBINARS = [
  'Algemene Ledenvergadering Bright Coöperatie 2026',
  'Pensioen Basics — Voor starters',
  'Zelfstandig en pensioen: de essentie',
  'Fiscaal voordeel met jaarruimte',
  'Beleggen voor je pensioen',
  'Pensioen na je 55e',
];
const CALENDLY_TYPES = [
  'Pensioen expert-gesprek met BrightPensioen',
  'Kennismakingsgesprek (15 min)',
  'Verdiepingsgesprek (30 min)',
  'Onboarding ondersteuning',
];

// Deterministic pseudo-random so the list is stable across renders.
function mulberry32(seed) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function pick(arr, rng) { return arr[Math.floor(rng() * arr.length)]; }
function daysAgo(d, n) {
  const x = new Date(d);
  x.setDate(x.getDate() - n);
  return x;
}
function fmtDate(d) {
  if (!d) return null;
  const x = typeof d === 'string' ? new Date(d) : d;
  return x.toISOString().slice(0, 10);
}
function fmtDateTime(d) {
  const x = typeof d === 'string' ? new Date(d) : d;
  const dd = x.toISOString().slice(0, 10);
  const tt = x.toISOString().slice(11, 16);
  return `${dd} ${tt}`;
}

function makeEmail(first, last, i) {
  const clean = (s) => s.toLowerCase().replace(/[^a-z]/g, '');
  const providers = ['gmail.com', 'hotmail.com', 'outlook.com', 'icloud.com', 'ziggo.nl', 'kpnmail.nl'];
  const p = providers[i % providers.length];
  const style = i % 3;
  if (style === 0) return `${clean(first)}.${clean(last)}@${p}`;
  if (style === 1) return `${clean(first)}${clean(last)}@${p}`;
  return `${clean(first[0])}${clean(last)}@${p}`;
}

function generateProfiles(count = 60) {
  const rng = mulberry32(7);
  const profiles = [];
  for (let i = 0; i < count; i++) {
    const first = pick(FIRST_NAMES, rng);
    const last = pick(LAST_NAMES, rng);
    const channel = pick(CHANNELS, rng);
    const source = pick(SOURCES_BY_CHANNEL[channel], rng);
    const [city, country] = pick(CITIES, rng);
    const daysBack = Math.floor(rng() * 400) + 1;
    const firstSession = daysAgo(now, daysBack);

    // Status distribution: 45% lead, 40% customer, 15% signed-up
    const r = rng();
    const status = r < 0.45 ? 'lead' : r < 0.85 ? 'customer' : 'signed-up';

    // Activity generation
    const activities = [];
    const addActivity = (type, date, data = {}) => {
      activities.push({ type, date: new Date(date), ...data });
    };

    // First session
    addActivity('first_session', firstSession, {
      channel, source, city, country,
      medium: channel === 'Paid Search' ? 'cpc' : channel === 'Organic Search' ? 'organic' : '(none)',
      campaign: channel === 'Paid Search' ? pick(['brand', 'jaarruimte-2026', 'pensioenscan', 'zzp-pensioen'], rng) : '(none)',
      device: pick(['desktop', 'mobile', 'tablet'], rng),
      browser: pick(['Chrome', 'Safari', 'Edge', 'Firefox'], rng),
      os: pick(['Windows', 'macOS', 'iOS', 'Android'], rng),
    });

    // Form submissions (0-3)
    const nForms = Math.floor(rng() * 4);
    const formDates = [];
    for (let f = 0; f < nForms; f++) {
      const d = daysAgo(firstSession, -Math.floor(rng() * Math.max(daysBack - 5, 5)));
      formDates.push(d);
      addActivity('form_submission', d, {
        form: pick(FORMS, rng),
      });
    }

    // Webinar registrations (0-2)
    const nWebinars = Math.floor(rng() * 3);
    for (let w = 0; w < nWebinars; w++) {
      const regDate = daysAgo(firstSession, -Math.floor(rng() * Math.max(daysBack - 2, 2)));
      const webDate = daysAgo(regDate, -Math.floor(rng() * 30) - 5);
      addActivity('webinar_registration', regDate, {
        title: pick(WEBINARS, rng),
        webinarDate: webDate,
      });
    }

    // Calendly (0-2)
    const nCall = rng() < 0.35 ? (rng() < 0.3 ? 2 : 1) : 0;
    for (let c = 0; c < nCall; c++) {
      const bookedAt = daysAgo(firstSession, -Math.floor(rng() * Math.max(daysBack - 2, 2)));
      const eventAt = daysAgo(bookedAt, -Math.floor(rng() * 14) - 2);
      addActivity('calendly_booking', bookedAt, {
        eventType: pick(CALENDLY_TYPES, rng),
        eventStart: eventAt,
        duration: pick(['15', '30', '45'], rng),
      });
    }

    // Signup
    let signupDate = null;
    if (status !== 'lead' || rng() < 0.25) {
      signupDate = daysAgo(firstSession, -Math.floor(rng() * Math.max(daysBack - 1, 1)));
      addActivity('signup', signupDate, {});
    }

    // DAS / customer
    let das = null;
    if (status === 'customer') {
      const memberSince = daysAgo(signupDate || firstSession, -Math.floor(rng() * 20) - 1);
      const payingSince = daysAgo(memberSince, -Math.floor(rng() * 30));
      const retirement = new Date(memberSince);
      retirement.setFullYear(retirement.getFullYear() + Math.floor(rng() * 30) + 10);
      das = {
        id: 250000 + Math.floor(rng() * 20000),
        participant: 'P0' + (300000000 + Math.floor(rng() * 99999999)),
        memberSince,
        payingSince,
        retirementDate: retirement,
        status: 1,
      };
      addActivity('customer', memberSince, { participant: das.participant });
      if (payingSince > memberSince) {
        addActivity('paying_started', payingSince, {});
      }
    }

    // A few extra engagement events for customers
    if (status === 'customer' && rng() < 0.6) {
      const nExtra = Math.floor(rng() * 3) + 1;
      for (let e = 0; e < nExtra; e++) {
        const d = daysAgo(now, Math.floor(rng() * 60));
        if (rng() < 0.5) {
          addActivity('webinar_registration', d, {
            title: pick(WEBINARS, rng),
            webinarDate: daysAgo(d, -Math.floor(rng() * 20) - 5),
          });
        } else {
          addActivity('form_submission', d, { form: pick(FORMS, rng) });
        }
      }
    }

    activities.sort((a, b) => b.date - a.date);

    const email = makeEmail(first, last, i);
    const firstForm = formDates.length ? pick(FORMS, rng) : null;
    profiles.push({
      email,
      firstName: first,
      lastName: last,
      status,
      profileDate: firstSession,
      firstSessionDate: firstSession,
      channel,
      source,
      city,
      country,
      device: activities[activities.length - 1]?.device || 'desktop',
      browser: activities[activities.length - 1]?.browser || 'Chrome',
      os: activities[activities.length - 1]?.os || 'Windows',
      medium: activities[activities.length - 1]?.medium || '(none)',
      campaign: activities[activities.length - 1]?.campaign || '(none)',
      formSubmissionsCount: nForms,
      firstForm,
      calendlyCount: nCall,
      webinarCount: activities.filter(a => a.type === 'webinar_registration').length,
      hasSignedUp: !!signupDate,
      hasBookedCall: nCall > 0,
      hasRegisteredWebinar: activities.some(a => a.type === 'webinar_registration'),
      signupDate,
      daysFirstToSignup: signupDate ? Math.round((signupDate - firstSession) / 86400000) : null,
      daysFirstToCustomer: das ? Math.round((das.memberSince - firstSession) / 86400000) : null,
      daysSignupToCustomer: das && signupDate ? Math.round((das.memberSince - signupDate) / 86400000) : null,
      das,
      activities,
      lastUpdated: now,
    });
  }
  return profiles;
}

const PROFILES = generateProfiles(60);

// Seed a known profile matching the user's sample data so we can demo
// a recognisable detail view.
PROFILES.unshift({
  email: 'jlamaessen@gmail.com',
  firstName: 'Johan',
  lastName: 'Maessen',
  status: 'customer',
  profileDate: new Date('2025-10-28'),
  firstSessionDate: new Date('2025-10-28'),
  channel: 'Direct',
  source: '',
  city: 'Utrecht',
  country: 'Netherlands',
  device: 'desktop',
  browser: 'Edge',
  os: 'Windows',
  medium: '(none)',
  campaign: '(none)',
  formSubmissionsCount: 0,
  firstForm: null,
  calendlyCount: 0,
  webinarCount: 1,
  hasSignedUp: false,
  hasBookedCall: false,
  hasRegisteredWebinar: true,
  signupDate: null,
  daysFirstToSignup: null,
  daysFirstToCustomer: -1117,
  daysSignupToCustomer: null,
  das: {
    id: 262067,
    participant: 'P0373155103',
    memberSince: new Date('2022-10-07T11:59:22Z'),
    payingSince: new Date('2022-10-31T00:00:00Z'),
    retirementDate: new Date('2053-06-19T00:00:00Z'),
    status: 1,
  },
  activities: [
    { type: 'webinar_registration', date: new Date('2026-04-23T13:41:58Z'),
      title: 'Algemene Ledenvergadering Bright Coöperatie 2026',
      webinarDate: new Date('2026-05-20T18:00:00Z') },
    { type: 'paying_started', date: new Date('2022-10-31T00:00:00Z') },
    { type: 'customer', date: new Date('2022-10-07T11:59:22Z'), participant: 'P0373155103' },
    { type: 'first_session', date: new Date('2022-10-07T10:00:00Z'),
      channel: 'Direct', source: '', medium: '(none)', campaign: '(none)',
      device: 'desktop', browser: 'Edge', os: 'Windows',
      city: 'Utrecht', country: 'Netherlands' },
  ],
  lastUpdated: now,
});

PROFILES.splice(1, 0, {
  email: 'otishermsen@hotmail.com',
  firstName: 'Otis',
  lastName: 'Hermsen',
  status: 'lead',
  profileDate: new Date('2026-02-16'),
  firstSessionDate: new Date('2026-02-16'),
  channel: 'Organic Search',
  source: 'google',
  city: 'Amsterdam',
  country: 'Netherlands',
  device: 'desktop',
  browser: 'Chrome',
  os: 'Windows',
  medium: 'organic',
  campaign: '(organic)',
  formSubmissionsCount: 0,
  firstForm: null,
  calendlyCount: 1,
  webinarCount: 0,
  hasSignedUp: false,
  hasBookedCall: true,
  hasRegisteredWebinar: false,
  signupDate: null,
  daysFirstToSignup: null,
  daysFirstToCustomer: null,
  daysSignupToCustomer: null,
  das: null,
  activities: [
    { type: 'calendly_booking', date: new Date('2026-04-23T13:21:23Z'),
      eventType: 'Pensioen expert-gesprek met BrightPensioen',
      eventStart: new Date('2026-04-30T08:00:00Z'),
      duration: '15' },
    { type: 'first_session', date: new Date('2026-02-16T09:30:00Z'),
      channel: 'Organic Search', source: 'google', medium: 'organic',
      campaign: '(organic)', device: 'desktop', browser: 'Chrome',
      os: 'Windows', city: 'Amsterdam', country: 'Netherlands' },
  ],
  lastUpdated: now,
});

window.PROFILES = PROFILES;
window.profileHelpers = { fmtDate, fmtDateTime, daysAgo, now };
