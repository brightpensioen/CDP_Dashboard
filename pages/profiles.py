import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pathlib import Path
from utils.data_loader import load_profiles, load_profile_sessions

_COMPONENT_DIR = Path(__file__).parent.parent / 'components' / 'profile_table'
_profile_table = components.declare_component('profile_table', path=str(_COMPONENT_DIR))
from components.ui import (
    T, CHANNEL_META, STATUS_META, ACTIVITY_META,
    inject_global_css, status_badge_html, channel_badge_html,
    avatar_html, engagement_badges_html, kpi_card_html,
    section_label_html, detail_row_html,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _fmt(val, fmt='%Y-%m-%d') -> str:
    if val is None or (not isinstance(val, str) and pd.isna(val)):
        return '—'
    try:
        return pd.to_datetime(val).strftime(fmt)
    except Exception:
        return str(val)[:10]


def _int(val) -> int:
    try:
        return int(val) if pd.notna(val) else 0
    except Exception:
        return 0


def _to_list(v) -> list | None:
    """
    Coerce a BQ ARRAY<RECORD> value to a plain Python list.
    BigQuery may return these as numpy ndarrays, not Python lists,
    so isinstance(v, list) would wrongly return False.
    Returns None when the value is clearly not an array (str, scalar, None).
    """
    if v is None:
        return None
    if isinstance(v, (str, bytes, dict)):
        return None
    if isinstance(v, (list, tuple)):
        return list(v)
    # numpy ndarray or any other iterable
    try:
        lst = list(v)
        return lst
    except Exception:
        return None


def _process_tab_sessions(sessions_raw: pd.DataFrame):
    """
    Convert tab_sessions rows into (sessions_df, pages_by_session) matching the
    shape that build_activities() and _activity_body() expect.
    Derives landing/exit pages, duration, and per-page detail from the inline events array.
    """
    sessions_list = []
    pages_by_session: dict = {}

    for _, s in sessions_raw.iterrows():
        events = _to_list(s.get('events')) or []
        page_events = [e for e in events if isinstance(e, dict) and e.get('page_path')]

        landing   = page_events[0].get('page_path') if page_events else None
        exit_page = page_events[-1].get('page_path') if page_events else None

        ts_list = []
        for e in events:
            if isinstance(e, dict) and e.get('event_timestamp'):
                try:
                    ts_list.append(pd.to_datetime(e['event_timestamp'], utc=True))
                except Exception:
                    pass
        duration_s = (max(ts_list) - min(ts_list)).total_seconds() if len(ts_list) >= 2 else None

        sessions_list.append({
            'session_id':                  s.get('session_id'),
            'session_start_timestamp_utc': s.get('session_start_timestamp_utc'),
            'session_duration_s':          duration_s,
            'landing_page_path':           landing,
            'exit_page_path':              exit_page,
            'source':                      s.get('source'),
            'medium':                      s.get('medium'),
            'campaign':                    s.get('campaign'),
            'channel':                     s.get('default_channel_grouping'),
            'device_category':             s.get('device_category'),
            'browser':                     s.get('browser'),
            'city':                        s.get('city'),
            'country':                     s.get('country'),
            'is_engaged_session':          None,
            'session_type':                str(s.get('session_type') or 'website'),
        })

        sid = s.get('session_id')
        if sid is not None and pd.notna(sid):
            page_list = []
            for i, e in enumerate(page_events):
                next_e = page_events[i + 1] if i + 1 < len(page_events) else None
                page_dur = None
                if next_e and e.get('event_timestamp') and next_e.get('event_timestamp'):
                    try:
                        t0 = pd.to_datetime(e['event_timestamp'], utc=True)
                        t1 = pd.to_datetime(next_e['event_timestamp'], utc=True)
                        page_dur = int((t1 - t0).total_seconds())
                    except Exception:
                        pass
                page_list.append({
                    'num':        i + 1,
                    'path':       e.get('page_path') or '',
                    'title':      e.get('page_title') or '',
                    'duration_s': page_dur,
                })
            pages_by_session[int(sid)] = page_list

    sessions_df = pd.DataFrame(sessions_list) if sessions_list else pd.DataFrame()
    return sessions_df, pages_by_session


def _list_or_int(row, list_col: str, count_col: str = '', date_col: str = '') -> int:
    """Return count from a BQ ARRAY column (list/ndarray), a count column, or presence of a date."""
    lst = _to_list(row.get(list_col))
    if lst is not None:
        return len(lst)
    if count_col:
        c = _int(row.get(count_col, 0))
        if c:
            return c
    # last resort: if a date exists, at least 1 event happened
    if date_col:
        try:
            if pd.notna(row.get(date_col)):
                return 1
        except Exception:
            pass
    return 0


def _str(val) -> str:
    if val is None or (not isinstance(val, str) and pd.isna(val)):
        return ''
    return str(val).strip()


# ── SVG icons ─────────────────────────────────────────────────────────────────

_SVG = {
    'globe':    '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="5.5"/><path d="M2.5 8H13.5M8 2.5C10 4.5 10.5 7 10.5 8S10 11.5 8 13.5C6 11.5 5.5 9 5.5 8S6 4.5 8 2.5"/></svg>',
    'form':     '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="2.5" width="10" height="11" rx="1.5"/><path d="M5.5 6H10.5M5.5 8.5H10.5M5.5 11H8.5" stroke-linecap="round"/></svg>',
    'video':    '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="4" width="9" height="8" rx="1.5"/><path d="M11 7L14 5V11L11 9Z"/></svg>',
    'calendar': '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/><path d="M2.5 6.5H13.5M5.5 2V5M10.5 2V5" stroke-linecap="round"/></svg>',
    'user':     '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="5.5" r="2.5"/><path d="M3 13.5C3.5 10.5 6 9.5 8 9.5S12.5 10.5 13 13.5" stroke-linecap="round"/></svg>',
    'euro':     '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 4.5C11 3.5 9.5 3 8 3C5.5 3 3.5 5 3.5 8S5.5 13 8 13C9.5 13 11 12.5 12 11.5"/><path d="M2.5 7H8M2.5 9H7.5"/></svg>',
    'screen':   '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1.5" y="2.5" width="13" height="9" rx="1.5"/><path d="M5.5 13.5H10.5M8 11.5V13.5" stroke-linecap="round"/></svg>',
}

_TYPE_ICON = {
    'first_session':   _SVG['globe'],
    'session_website': _SVG['globe'],
    'session_portal':  _SVG['screen'],
    'form_submission': _SVG['form'],
    'webinar_registration': _SVG['video'],
    'calendly_booking': _SVG['calendar'],
    'signup': _SVG['user'],
    'customer': _SVG['euro'],
    'paying_started': _SVG['euro'],
}

_TYPE_TITLE = {
    'first_session':        'First session started',
    'session_website':      'Website session',
    'session_portal':       'Portal session',
    'form_submission':      'Form submission',
    'webinar_registration': 'Webinar registration',
    'calendly_booking':     'Call booked',
    'signup':               'Created account',
    'customer':             'Became paying customer',
    'paying_started':       'First payment received',
}


# ── activity builder ──────────────────────────────────────────────────────────

def build_activities(row: pd.Series, sessions_df=None, pages_by_session=None) -> list:
    acts = []
    has_real_sessions = sessions_df is not None and not sessions_df.empty

    # ── first session (fallback when no GA4 sessions loaded) ──────────────────
    if not has_real_sessions and pd.notna(row.get('first_session_date')):
        acts.append({
            'type':     'first_session',
            'date':     pd.to_datetime(row['first_session_date'], utc=True),
            'channel':  _str(row.get('initial_channel')),
            'source':   _str(row.get('initial_source')),
            'medium':   _str(row.get('initial_medium')),
            'campaign': _str(row.get('initial_campaign')),
            'device':   _str(row.get('initial_device_category')),
            'browser':  _str(row.get('initial_browser')),
            'os':       _str(row.get('initial_operating_system')),
            'city':     _str(row.get('initial_city')),
            'country':  _str(row.get('initial_country')),
        })

    # ── GA4 sessions (when loaded on demand) ──────────────────────────────────
    if has_real_sessions:
        _pbs = pages_by_session or {}
        for _, s in sessions_df.iterrows():
            if pd.isna(s.get('session_start_timestamp_utc')):
                continue
            sid = int(s['session_id']) if pd.notna(s.get('session_id')) else None
            stype = _str(s.get('session_type')) or 'website'
            acts.append({
                'type':      'session_portal' if stype == 'portal' else 'session_website',
                'date':      s['session_start_timestamp_utc'],
                'session_id': sid,
                'duration_s': s.get('session_duration_s'),
                'landing':   s.get('landing_page_path'),
                'exit':      s.get('exit_page_path'),
                'source':    s.get('source'),
                'medium':    s.get('medium'),
                'campaign':  s.get('campaign'),
                'channel':   s.get('channel'),
                'device':    s.get('device_category'),
                'browser':   s.get('browser'),
                'city':      s.get('city'),
                'country':   s.get('country'),
                'engaged':   s.get('is_engaged_session'),
                'pages':     _pbs.get(sid, []) if sid is not None else [],
            })

    # ── form submissions ───────────────────────────────────────────────────────
    # form_submissions is a BQ ARRAY<RECORD> (may be ndarray, list, or None)
    form_list = _to_list(row.get('form_submissions'))
    if form_list:
        for sub in form_list:
            if not isinstance(sub, dict):
                continue
            sub_date = sub.get('SubmissionDate')
            if sub_date is None:
                continue
            acts.append({
                'type':  'form_submission',
                'date':  pd.to_datetime(sub_date, utc=True),
                'form':  sub.get('FormName') or _str(row.get('first_form')) or 'Form',
                'label': 'Form submission',
            })
    else:
        # fall back to summary date columns
        first_sub = row.get('first_submission_date')
        last_sub  = row.get('last_submission_date')
        form_name = _str(row.get('first_form')) or 'Form'
        if pd.notna(first_sub):
            acts.append({'type': 'form_submission', 'date': pd.to_datetime(first_sub, utc=True),
                         'form': form_name, 'label': 'First form submission'})
        if pd.notna(last_sub):
            last_dt = pd.to_datetime(last_sub, utc=True)
            if not pd.notna(first_sub) or last_dt != pd.to_datetime(first_sub, utc=True):
                acts.append({'type': 'form_submission', 'date': last_dt,
                             'form': form_name, 'label': 'Last form submission'})

    # ── webinar registrations ──────────────────────────────────────────────────
    # webinar_registrations is a BQ ARRAY<RECORD> (may be ndarray, list, or None)
    webinar_list = _to_list(row.get('webinar_registrations'))
    if webinar_list:
        for reg in webinar_list:
            if not isinstance(reg, dict):
                continue
            reg_date = reg.get('RegistrationDate')
            if reg_date is None:
                continue
            acts.append({
                'type':         'webinar_registration',
                'date':         pd.to_datetime(reg_date, utc=True),
                'title':        reg.get('WebinarTitle', ''),
                'webinar_date': reg.get('WebinarDate'),
                'label':        'Webinar registration',
            })
    else:
        # fall back to summary columns (actual BQ column names)
        wc = _int(row.get('webinar_registration_count', row.get('webinar_count', 0)))
        if wc > 0:
            title = _str(row.get('first_webinar_title'))
            for date_col, lbl in [
                ('first_webinar_registration_date', 'First webinar registration'),
                ('last_webinar_registration_date',  f'Last of {wc} webinar registrations'),
            ]:
                d = row.get(date_col)
                if pd.notna(d):
                    acts.append({
                        'type':  'webinar_registration',
                        'date':  pd.to_datetime(d, utc=True),
                        'title': title,
                        'label': lbl if wc > 1 else 'Webinar registration',
                        'count': wc,
                    })
            # de-duplicate if only 1 registration
            wa = [a for a in acts if a['type'] == 'webinar_registration']
            if len(wa) == 2 and wa[0]['date'] == wa[1]['date']:
                acts = [a for a in acts if a['type'] != 'webinar_registration']
                acts.append(wa[0])

    # ── calendly bookings ──────────────────────────────────────────────────────
    # calendly_bookings is a BQ ARRAY<RECORD> (may be ndarray, list, or None)
    cal_list = _to_list(row.get('calendly_bookings'))
    if cal_list:
        for booking in cal_list:
            if not isinstance(booking, dict):
                continue
            # Support both old and new field name conventions
            book_date = (booking.get('BookedAt') or booking.get('BookingDate')
                         or booking.get('StartDate') or booking.get('CreatedAt'))
            if book_date is None:
                continue
            acts.append({
                'type':       'calendly_booking',
                'date':       pd.to_datetime(book_date, utc=True),
                'event_type': (booking.get('EventTypeName') or booking.get('EventType') or ''),
                'start_time': booking.get('EventStartTime'),
                'duration':   booking.get('EventDuration') or booking.get('Duration') or booking.get('duration'),
                'label':      'Call booked',
            })
    else:
        # fall back to summary columns (actual BQ column names)
        cc = _int(row.get('calendly_booking_count', row.get('calendly_count', 0)))
        if cc > 0:
            event_type = _str(row.get('first_calendly_event_type'))
            for date_col, lbl in [
                ('first_calendly_booking_date', 'First call booked'),
                ('last_calendly_booking_date',  f'Last of {cc} calls booked'),
            ]:
                d = row.get(date_col)
                if pd.notna(d):
                    acts.append({
                        'type':       'calendly_booking',
                        'date':       pd.to_datetime(d, utc=True),
                        'event_type': event_type,
                        'label':      lbl if cc > 1 else 'Call booked',
                        'count':      cc,
                    })
            ca = [a for a in acts if a['type'] == 'calendly_booking']
            if len(ca) == 2 and ca[0]['date'] == ca[1]['date']:
                acts = [a for a in acts if a['type'] != 'calendly_booking']
                acts.append(ca[0])

    # ── milestone events ───────────────────────────────────────────────────────
    if row.get('has_signed_up') and pd.notna(row.get('signup_date')):
        acts.append({'type': 'signup', 'date': pd.to_datetime(row['signup_date'], utc=True)})

    if pd.notna(row.get('das_member_since')):
        acts.append({
            'type':        'customer',
            'date':        pd.to_datetime(row['das_member_since'], utc=True),
            'participant': _str(row.get('das_participant_number')),
        })

    if pd.notna(row.get('das_paying_since')):
        acts.append({'type': 'paying_started', 'date': pd.to_datetime(row['das_paying_since'], utc=True)})

    acts.sort(key=lambda a: a['date'], reverse=True)
    return acts


# ── timeline HTML ─────────────────────────────────────────────────────────────

def _activity_body(a: dict) -> str:
    def kv(label, value):
        return (f'<div style="display:flex;gap:8px;font-size:11px;font-family:Inter,sans-serif;">'
                f'<span style="color:{T["textMute"]};min-width:80px;">{label}</span>'
                f'<span style="color:{T["textDim"]};">{value or "—"}</span></div>')

    t = a['type']
    if t == 'first_session':
        return (
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:2px 20px;margin-top:4px;">'
            + kv('channel',  a.get('channel'))
            + kv('device',   ' · '.join(filter(None, [a.get('device'), a.get('browser')])))
            + kv('source',   a.get('source') or '(none)')
            + kv('location', ', '.join(filter(None, [a.get('city'), a.get('country')])))
            + kv('medium',   a.get('medium') or '(none)')
            + kv('campaign', a.get('campaign') or '(none)')
            + '</div>'
        )
    if t == 'form_submission':
        body = f'<div style="margin-top:4px;">{kv("form", a.get("form"))}</div>'
        if a.get('count', 1) > 1:
            body += f'<div style="margin-top:2px;">{kv("total", str(a["count"]) + " submissions")}</div>'
        return body
    if t == 'webinar_registration':
        parts = []
        if a.get('title'):
            parts.append(kv('webinar', a['title']))
        if a.get('webinar_date'):
            try:
                wd = pd.to_datetime(a['webinar_date'], utc=True).strftime('%d %b %Y %H:%M')
                parts.append(kv('scheduled', wd + ' UTC'))
            except Exception:
                pass
        return f'<div style="margin-top:4px;">{"".join(parts)}</div>' if parts else ''
    if t == 'calendly_booking':
        parts = []
        if a.get('event_type'):
            parts.append(kv('event', a['event_type']))
        if a.get('start_time'):
            try:
                st_str = pd.to_datetime(a['start_time'], utc=True).strftime('%d %b %Y %H:%M UTC')
                parts.append(kv('scheduled', st_str))
            except Exception:
                pass
        if a.get('duration'):
            parts.append(kv('duration', f"{a['duration']} min"))
        return f'<div style="margin-top:4px;">{"".join(parts)}</div>' if parts else ''
    if t == 'customer':
        return f'<div style="margin-top:4px;">{kv("participant", a.get("participant"))}</div>'
    if t in ('session_website', 'session_portal'):
        dur = a.get('duration_s')
        dur_str = f'{int(dur // 60)}m {int(dur % 60)}s' if (dur is not None and pd.notna(dur)) else '—'
        engaged = 'Yes' if a.get('engaged') else 'No'
        loc = ', '.join(filter(None, [_str(a.get('city')), _str(a.get('country'))])) or '—'
        device = ' · '.join(filter(None, [_str(a.get('device')), _str(a.get('browser'))])) or '—'
        body = (
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:2px 20px;margin-top:4px;">'
            + kv('landing',  a.get('landing') or '—')
            + kv('exit',     a.get('exit') or '—')
            + kv('channel',  a.get('channel') or '—')
            + kv('source',   a.get('source') or '(direct)')
            + kv('duration', dur_str)
            + kv('engaged',  engaged)
            + kv('device',   device)
            + kv('location', loc)
            + '</div>'
        )
        pages = a.get('pages') or []
        if pages:
            page_rows = ''
            for p in pages:
                num   = p.get('num') or ''
                path  = p.get('path') or '—'
                title = p.get('title') or ''
                dur   = p.get('duration_s')
                if dur is not None:
                    dur = int(dur)
                    dur_str = f'{dur // 60}m {dur % 60:02d}s' if dur >= 60 else f'{dur}s'
                else:
                    dur_str = ''
                page_rows += (
                    f'<div style="display:flex;gap:8px;align-items:center;padding:4px 0;'
                    f'border-bottom:1px solid {T["border"]};">'
                    f'<span style="font-size:10px;color:{T["textMute"]};min-width:18px;text-align:right;flex-shrink:0;">{num}</span>'
                    f'<div style="flex:1;min-width:0;">'
                    f'<div style="font-size:11px;color:{T["textDim"]};font-family:Inter,sans-serif;'
                    f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{path}</div>'
                    + (f'<div style="font-size:10px;color:{T["textMute"]};font-family:Inter,sans-serif;'
                       f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{title}</div>' if title else '')
                    + f'</div>'
                    + (f'<span style="font-size:10px;color:{T["textMute"]};font-family:Inter,sans-serif;'
                       f'flex-shrink:0;white-space:nowrap;">{dur_str}</span>' if dur_str else '')
                    + f'</div>'
                )
            body += (
                f'<details style="margin-top:8px;">'
                f'<summary style="cursor:pointer;font-size:11px;font-family:Inter,sans-serif;'
                f'color:{T["textMute"]};letter-spacing:0.02em;list-style:none;'
                f'display:flex;align-items:center;gap:4px;">'
                f'<span style="font-size:9px;">▶</span> {len(pages)} pages visited'
                f'</summary>'
                f'<div style="margin-top:6px;max-height:220px;overflow-y:auto;'
                f'border:1px solid {T["border"]};border-radius:4px;padding:4px 8px;">'
                + page_rows +
                f'</div></details>'
            )
        return body
    return ''


def render_timeline_html(activities: list) -> str:
    if not activities:
        return f'<div style="padding:40px;text-align:center;color:{T["textMute"]};font-size:12px;font-family:Inter,sans-serif;">No activities recorded.</div>'

    from collections import OrderedDict
    groups: dict = OrderedDict()
    for a in activities:
        day = a['date'].strftime('%Y-%m-%d')
        groups.setdefault(day, []).append(a)

    html = '<div style="position:relative;">'
    html += f'<div style="position:absolute;left:11px;top:8px;bottom:8px;width:1px;background:{T["border"]};"></div>'

    today = pd.Timestamp.now().date()

    for day, events in groups.items():
        d = pd.to_datetime(day).date()
        diff = (today - d).days
        if diff == 0:     rel = 'Today'
        elif diff == 1:   rel = 'Yesterday'
        elif diff < 0:    rel = f'in {-diff}d'
        elif diff < 30:   rel = f'{diff}d ago'
        elif diff < 365:  rel = f'{diff // 30}mo ago'
        else:             rel = f'{diff // 365}y ago'

        try:
            formatted = pd.to_datetime(day).strftime('%a, %d %b %Y')
        except Exception:
            formatted = str(day)

        html += (
            f'<div style="margin-bottom:24px;">'
            f'<div style="display:flex;align-items:center;gap:10px;padding-left:32px;margin-bottom:8px;">'
            f'<span style="font-size:11px;font-family:Inter,sans-serif;color:{T["textDim"]};font-weight:500;">{formatted}</span>'
            f'<span style="font-size:10px;font-family:Inter,sans-serif;color:{T["textMute"]};">{rel}</span>'
            f'</div>'
        )

        for ev in events:
            meta  = ACTIVITY_META.get(ev['type'], ACTIVITY_META['first_session'])
            icon  = _TYPE_ICON.get(ev['type'], _SVG['globe'])
            title = ev.get('label') or _TYPE_TITLE.get(ev['type'], ev['type'])
            time_str = ev['date'].strftime('%H:%M')
            body  = _activity_body(ev)

            html += (
                f'<div style="display:flex;gap:10px;margin-bottom:8px;position:relative;">'
                f'<div style="width:22px;height:22px;border-radius:50%;background:{meta["bg"]};color:{meta["color"]};'
                f'border:1px solid {meta["color"]}44;display:flex;align-items:center;justify-content:center;'
                f'flex-shrink:0;z-index:1;margin-top:2px;">{icon}</div>'
                f'<div style="flex:1;min-width:0;background:{T["surface"]};border:1px solid {T["border"]};'
                f'border-radius:6px;padding:10px 14px;border-left:2px solid {meta["color"]}88;">'
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:3px;">'
                f'<span style="font-size:12px;font-weight:500;color:{T["text"]};">{title}</span>'
                f'<span style="font-size:9px;padding:1px 6px;border-radius:2px;background:{meta["bg"]};'
                f'color:{meta["color"]};font-family:Inter,sans-serif;letter-spacing:0.05em;text-transform:uppercase;">{meta["label"]}</span>'
                f'<div style="flex:1;"></div>'
                f'<span style="font-size:10px;font-family:Inter,sans-serif;color:{T["textMute"]};">{time_str}</span>'
                f'</div>{body}</div></div>'
            )

        html += '</div>'

    html += (
        f'<div style="display:flex;align-items:center;gap:12px;color:{T["textMute"]};font-size:11px;font-family:Inter,sans-serif;">'
        f'<div style="width:22px;height:22px;border-radius:50%;background:{T["bg"]};'
        f'border:1px dashed {T["borderHi"]};display:flex;align-items:center;justify-content:center;'
        f'font-size:10px;color:{T["textMute"]};">✦</div>'
        f'<span>Profile begins</span></div>'
    )
    html += '</div>'
    return html


# ── right rail ────────────────────────────────────────────────────────────────

def render_right_rail(row: pd.Series) -> None:
    first = _fmt(row.get('first_session_date'))
    signup_d = _fmt(row.get('signup_date'))
    customer_d = _fmt(row.get('das_member_since'))
    channel  = _str(row.get('initial_channel')) or 'Direct'
    source   = _str(row.get('initial_source'))
    medium   = _str(row.get('initial_medium'))
    campaign = _str(row.get('initial_campaign'))
    status   = _str(row.get('status')) or 'lead'
    kortingspartner = _str(row.get('signup_kortingspartner'))
    referrer        = _str(row.get('signup_referrer'))
    referrer_other  = _str(row.get('signup_referrer_other'))

    def _snap_row(label, value, last=False):
        border = '' if last else f'border-bottom:1px solid {T["border"]};'
        return (
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:8px 14px;{border}">'
            f'<span style="font-size:11px;color:{T["textMute"]};font-family:Inter,sans-serif;">{label}</span>'
            f'<span style="font-size:11px;font-family:Inter,sans-serif;color:{T["textDim"]};">{value}</span>'
            f'</div>'
        )

    is_customer = (status == 'customer')

    _snap_items = [
        ('Lifecycle', status_badge_html(status), False, True),   # (label, value_html, last, raw_html)
    ]
    if is_customer or kortingspartner:
        _snap_items.append(('Kortingspartner', kortingspartner or '—', False, False))
    if is_customer or referrer:
        _snap_items.append(('Referrer', referrer or '—', False, False))
    if is_customer or referrer_other:
        _snap_items.append(('Referrer (other)', referrer_other or '—', False, False))
    _snap_items.append(('First session', first, True, False))

    snap_rows = ''
    for i, item in enumerate(_snap_items):
        label, value, _, raw = item
        is_last = (i == len(_snap_items) - 1)
        border = '' if is_last else f'border-bottom:1px solid {T["border"]};'
        if raw:
            snap_rows += (
                f'<div style="display:flex;align-items:center;justify-content:space-between;'
                f'padding:8px 14px;{border}">'
                f'<span style="font-size:11px;color:{T["textMute"]};font-family:Inter,sans-serif;">{label}</span>'
                f'{value}</div>'
            )
        else:
            snap_rows += (
                f'<div style="display:flex;align-items:center;justify-content:space-between;'
                f'padding:8px 14px;{border}">'
                f'<span style="font-size:11px;color:{T["textMute"]};font-family:Inter,sans-serif;">{label}</span>'
                f'<span style="font-size:11px;font-family:Inter,sans-serif;color:{T["textDim"]};">{value}</span>'
                f'</div>'
            )
    st.markdown(section_label_html('Snapshot'), unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:{T["surface"]};border:1px solid {T["border"]};border-radius:8px;overflow:hidden;margin-bottom:16px;">'
        f'{snap_rows}</div>',
        unsafe_allow_html=True,
    )

    # Timeline quick-stats
    tl_rows = ''
    if signup_d != '—':
        tl_rows += (
            f'<div style="display:flex;align-items:center;justify-content:space-between;padding:8px 14px;border-bottom:1px solid {T["border"]};">'
            f'<span style="font-size:11px;color:{T["textMute"]};font-family:Inter,sans-serif;">Signed up</span>'
            f'<span style="font-size:11px;font-family:Inter,sans-serif;color:{T["textDim"]};">{signup_d}</span></div>'
        )
    if customer_d != '—':
        tl_rows += (
            f'<div style="display:flex;align-items:center;justify-content:space-between;padding:8px 14px;">'
            f'<span style="font-size:11px;color:{T["textMute"]};font-family:Inter,sans-serif;">Became customer</span>'
            f'<span style="font-size:11px;font-family:Inter,sans-serif;color:{T["customer"]};">{customer_d}</span></div>'
        )
    if tl_rows:
        st.markdown(section_label_html('Timeline'), unsafe_allow_html=True)
        st.markdown(
            f'<div style="background:{T["surface"]};border:1px solid {T["border"]};border-radius:8px;overflow:hidden;margin-bottom:16px;">'
            f'{tl_rows}</div>',
            unsafe_allow_html=True,
        )

    # Attribution
    st.markdown(section_label_html('Attribution'), unsafe_allow_html=True)
    st.markdown(f"""
<div style="background:{T['surface']};border:1px solid {T['border']};border-radius:8px;padding:12px 14px;margin-bottom:16px;">
  <div style="margin-bottom:10px;">{channel_badge_html(channel)}</div>
  <div style="font-size:11px;font-family:Inter,sans-serif;color:{T['textMute']};line-height:1.8;">
    <div>source: {source or '—'}</div>
    <div>medium: {medium or '—'}</div>
    <div>campaign: {campaign or '—'}</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── detail tabs ───────────────────────────────────────────────────────────────

def _engagement_bucket(title: str, icon_svg: str, color: str, items_html: str, count: int) -> str:
    """Render one engagement bucket card."""
    header = (
        f'<div style="padding:10px 14px;border-bottom:1px solid {T["border"]};background:{T["bg2"]};'
        f'display:flex;align-items:center;gap:8px;">'
        f'<span style="color:{color};display:inline-flex;">{icon_svg}</span>'
        f'<span style="font-size:12px;font-weight:600;font-family:Inter,sans-serif;color:{T["text"]};">{title}</span>'
        f'<span style="font-size:11px;font-family:Inter,sans-serif;color:{T["textMute"]};">{count}</span>'
        f'</div>'
    )
    return (
        f'<div style="background:{T["surface"]};border:1px solid {T["border"]};'
        f'border-radius:8px;overflow:hidden;margin-bottom:16px;">'
        f'{header}{items_html}</div>'
    )


def _item_row(main: str, sub: str, is_last: bool) -> str:
    border = '' if is_last else f'border-bottom:1px solid {T["border"]};'
    return (
        f'<div style="padding:10px 14px;{border}">'
        f'<div style="font-size:12px;font-family:Inter,sans-serif;color:{T["text"]};margin-bottom:2px;">{main}</div>'
        f'<div style="font-size:11px;font-family:Inter,sans-serif;color:{T["textMute"]};">{sub}</div>'
        f'</div>'
    )


def _empty_row(msg: str) -> str:
    return f'<div style="padding:20px;color:{T["textMute"]};font-size:12px;font-family:Inter,sans-serif;">{msg}</div>'


def render_engagements_tab(row: pd.Series) -> None:
    # ── Form submissions ───────────────────────────────────────────────────────
    form_list = _to_list(row.get('form_submissions'))
    if form_list:
        rows_html = ''
        items = [f for f in form_list if isinstance(f, dict)]
        items.sort(key=lambda x: pd.to_datetime(x.get('SubmissionDate'), errors='coerce', utc=True),
                   reverse=False)
        for i, f in enumerate(items):
            name = f.get('FormName') or _str(row.get('first_form')) or '—'
            try:
                dt = pd.to_datetime(f.get('SubmissionDate'), utc=True).strftime('%d %b %Y %H:%M UTC')
            except Exception:
                dt = '—'
            rows_html += _item_row(name, dt, i == len(items) - 1)
        count = len(items)
    else:
        first_d = _fmt(row.get('first_submission_date'), '%d %b %Y')
        last_d  = _fmt(row.get('last_submission_date'),  '%d %b %Y')
        form_name = _str(row.get('first_form')) or '—'
        if first_d != '—':
            count = _int(row.get('form_submission_count', 1))
            if last_d != '—' and last_d != first_d:
                # Show first and last as separate rows
                rows_html  = _item_row(form_name, first_d, False)
                rows_html += _item_row(form_name, last_d,  True)
            else:
                rows_html = _item_row(form_name, first_d, True)
                count = max(count, 1)
        else:
            rows_html = _empty_row('No forms submitted yet.')
            count = 0

    st.markdown(
        _engagement_bucket('Form submissions', _SVG['form'], T['form'], rows_html, count),
        unsafe_allow_html=True,
    )

    # ── Webinar registrations ──────────────────────────────────────────────────
    webinar_list = _to_list(row.get('webinar_registrations'))
    if webinar_list:
        rows_html = ''
        items = [w for w in webinar_list if isinstance(w, dict)]
        items.sort(key=lambda x: pd.to_datetime(x.get('RegistrationDate'), errors='coerce', utc=True),
                   reverse=False)
        for i, w in enumerate(items):
            title = w.get('WebinarTitle') or '—'
            try:
                reg_dt = pd.to_datetime(w.get('RegistrationDate'), utc=True).strftime('%d %b %Y %H:%M')
            except Exception:
                reg_dt = '—'
            try:
                web_dt = pd.to_datetime(w.get('WebinarDate'), utc=True).strftime('%d %b %Y')
                sub = f'Registered {reg_dt} UTC · Scheduled {web_dt}'
            except Exception:
                sub = f'Registered {reg_dt} UTC'
            rows_html += _item_row(title, sub, i == len(items) - 1)
        count = len(items)
    else:
        wc = _int(row.get('webinar_registration_count', 0))
        if wc > 0:
            title = _str(row.get('first_webinar_title')) or '—'
            d = _fmt(row.get('first_webinar_registration_date'), '%d %b %Y')
            rows_html = _item_row(title, f'Registered {d}', True)
            count = wc
        else:
            rows_html = _empty_row('No webinar registrations yet.')
            count = 0

    st.markdown(
        _engagement_bucket('Webinar registrations', _SVG['video'], T['webinar'], rows_html, count),
        unsafe_allow_html=True,
    )

    # ── Calendly bookings ──────────────────────────────────────────────────────
    cal_list = _to_list(row.get('calendly_bookings'))
    if cal_list:
        rows_html = ''
        items = [c for c in cal_list if isinstance(c, dict)]
        items.sort(key=lambda x: pd.to_datetime(
            x.get('BookedAt') or x.get('BookingDate') or x.get('StartDate') or x.get('CreatedAt'),
            errors='coerce', utc=True), reverse=False)
        for i, c in enumerate(items):
            event_type = c.get('EventTypeName') or c.get('EventType') or c.get('event_type') or '—'
            # Show meeting start time if available, otherwise fall back to booking date
            start = c.get('EventStartTime') or c.get('BookedAt') or c.get('BookingDate') or c.get('StartDate') or c.get('CreatedAt')
            booked = c.get('BookedAt') or c.get('BookingDate')
            try:
                start_str = pd.to_datetime(start, utc=True).strftime('%d %b %Y %H:%M UTC')
            except Exception:
                start_str = '—'
            try:
                booked_str = pd.to_datetime(booked, utc=True).strftime('%d %b %Y')
            except Exception:
                booked_str = None
            duration = c.get('EventDuration') or c.get('Duration') or c.get('duration')
            sub = start_str
            if duration:
                sub += f' · {duration} min'
            if booked_str and c.get('EventStartTime'):
                sub += f' · booked {booked_str}'
            rows_html += _item_row(event_type, sub, i == len(items) - 1)
        count = len(items)
    else:
        cc = _int(row.get('calendly_booking_count', 0))
        if cc > 0:
            event_type = _str(row.get('first_calendly_event_type')) or '—'
            d = _fmt(row.get('first_calendly_booking_date'), '%d %b %Y')
            rows_html = _item_row(event_type, f'Scheduled {d}', True)
            count = cc
        else:
            rows_html = _empty_row('No calls booked yet.')
            count = 0

    st.markdown(
        _engagement_bucket('Calendly bookings', _SVG['calendar'], T['call'], rows_html, count),
        unsafe_allow_html=True,
    )


def render_acquisition_tab(row: pd.Series) -> None:
    fields = [
        ('Channel',  _str(row.get('initial_channel')) or '—'),
        ('Source',   _str(row.get('initial_source')) or '(none)'),
        ('Medium',   _str(row.get('initial_medium')) or '(none)'),
        ('Campaign', _str(row.get('initial_campaign')) or '(none)'),
        ('Country',  _str(row.get('initial_country')) or '—'),
        ('City',     _str(row.get('initial_city')) or '—'),
        ('Device',   _str(row.get('initial_device_category')) or '—'),
        ('Browser',  _str(row.get('initial_browser')) or '—'),
        ('OS',       _str(row.get('initial_operating_system')) or '—'),
    ]
    html = (
        f'<div style="background:{T["surface"]};border:1px solid {T["border"]};border-radius:8px;overflow:hidden;">'
        f'<div style="padding:10px 16px;border-bottom:1px solid {T["border"]};font-size:12px;font-weight:600;'
        f'background:{T["bg2"]};color:{T["text"]};">Acquisition</div>'
    )
    for label, value in fields:
        html += detail_row_html(label, value)
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_das_tab(row: pd.Series) -> None:
    if not pd.notna(row.get('das_participant_number')):
        st.markdown(
            f'<div style="padding:20px;color:{T["textMute"]};font-size:12px;font-family:Inter,sans-serif;">This profile is not yet a DAS member.</div>',
            unsafe_allow_html=True,
        )
        return
    fields = [
        ('DAS ID',          _str(row.get('das_id'))),
        ('Participant #',   _str(row.get('das_participant_number'))),
        ('First name',      _str(row.get('das_first_name'))),
        ('Last name',       _str(row.get('das_last_name'))),
        ('Member since',    _fmt(row.get('das_member_since'))),
        ('Paying since',    _fmt(row.get('das_paying_since'))),
        ('Retirement date', _fmt(row.get('das_retirement_date'))),
        ('Cancellation',    _fmt(row.get('das_cancellation_date'))),
        ('Status',          'Active' if row.get('das_status') == 1 else _str(row.get('das_status')) or '—'),
    ]
    html = (
        f'<div style="background:{T["surface"]};border:1px solid {T["border"]};border-radius:8px;overflow:hidden;">'
        f'<div style="padding:10px 16px;border-bottom:1px solid {T["border"]};font-size:12px;font-weight:600;'
        f'background:{T["bg2"]};color:{T["text"]};">DAS / Member</div>'
    )
    for label, value in fields:
        html += detail_row_html(label, value)
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_raw_tab(row: pd.Series) -> None:
    import json

    def _serialize(v):
        try:
            if pd.isna(v):
                return None
        except Exception:
            pass
        if hasattr(v, 'isoformat'):
            return v.isoformat()
        return v

    data = {k: _serialize(v) for k, v in row.items()}
    st.code(json.dumps(data, indent=2, default=str), language='json')


# ── detail view ───────────────────────────────────────────────────────────────

def render_detail(row: pd.Series) -> None:
    fn = _str(row.get('das_first_name'))
    ln = _str(row.get('das_last_name'))
    name   = f'{fn} {ln}'.strip() or row['Email'].split('@')[0].replace('.', ' ').title()
    email  = row['Email']
    status = _str(row.get('status')) or 'lead'

    # ── load sessions lazily for this profile ─────────────────────────────────
    try:
        sessions_raw = load_profile_sessions(email)
    except Exception:
        sessions_raw = pd.DataFrame()
    sessions_df, pages_by_session = (
        _process_tab_sessions(sessions_raw) if not sessions_raw.empty
        else (pd.DataFrame(), {})
    )

    if st.button('← Profiles', key='back_btn'):
        st.session_state.profile_email = None
        st.rerun()

    st.markdown(f"""
<div style="display:flex;align-items:center;gap:8px;padding:8px 0 16px 0;
     border-bottom:1px solid {T['border']};margin-bottom:0;">
  <span style="font-size:10px;font-family:Inter,sans-serif;color:{T['textMute']};letter-spacing:0.1em;">PROFILE DETAIL</span>
  <span style="color:{T['border']};">·</span>
  <span style="font-family:Inter,sans-serif;font-size:12px;color:{T['textDim']};">{email}</span>
</div>
""", unsafe_allow_html=True)

    # Header
    das_badge = ''
    if pd.notna(row.get('das_participant_number')):
        das_badge = (
            f'<span style="font-size:10px;font-family:Inter,sans-serif;padding:2px 7px;border-radius:3px;'
            f'background:rgba(154,163,173,0.08);color:{T["textDim"]};letter-spacing:0.05em;'
            f'border:1px solid {T["border"]};">DAS #{_str(row.get("das_participant_number"))}</span>'
        )

    city    = _str(row.get('initial_city'))
    country = _str(row.get('initial_country'))
    location   = ', '.join(filter(None, [city, country])) or '—'
    first_seen = _fmt(row.get('first_session_date'))
    member_since = _fmt(row.get('das_member_since'))
    device_str = ' · '.join(filter(None, [
        _str(row.get('initial_device_category')),
        _str(row.get('initial_browser')),
        _str(row.get('initial_operating_system')),
    ])) or '—'

    meta_chips = []
    if location != '—':
        meta_chips.append(f'<span style="display:inline-flex;align-items:center;gap:5px;">{_SVG["globe"]} {location}</span>')
    if first_seen != '—':
        meta_chips.append(f'<span style="display:inline-flex;align-items:center;gap:5px;">{_SVG["calendar"]} First seen {first_seen}</span>')
    if member_since != '—':
        meta_chips.append(f'<span style="display:inline-flex;align-items:center;gap:5px;">{_SVG["euro"]} Member since {member_since}</span>')
    if device_str != '—':
        meta_chips.append(f'<span style="display:inline-flex;align-items:center;gap:5px;">{_SVG["user"]} {device_str}</span>')

    st.markdown(f"""
<div style="display:flex;gap:20px;align-items:flex-start;padding:24px 0;border-bottom:1px solid {T['border']};">
  {avatar_html(name, 64)}
  <div style="flex:1;min-width:0;">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;flex-wrap:wrap;">
      <h1 style="font-size:22px;font-weight:600;letter-spacing:-0.01em;color:{T['text']};">{name}</h1>
      {status_badge_html(status)} {das_badge}
    </div>
    <div style="font-family:Inter,sans-serif;font-size:12px;color:{T['textDim']};margin-bottom:10px;">{email}</div>
    <div style="display:flex;gap:20px;font-size:11px;font-family:Inter,sans-serif;color:{T['textMute']};flex-wrap:wrap;">
      {''.join(meta_chips)}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # KPI strip
    now_ts = pd.Timestamp.now(tz='UTC')
    first_ts = pd.to_datetime(row.get('first_session_date'), errors='coerce', utc=True)
    days_active = int((now_ts - first_ts).days) if pd.notna(first_ts) else 0
    forms    = _list_or_int(row, 'form_submissions',       'form_submission_count',      'first_submission_date')
    webinars = _list_or_int(row, 'webinar_registrations', 'webinar_registration_count', 'first_webinar_registration_date')
    calls    = _list_or_int(row, 'calendly_bookings',     'calendly_booking_count',     'first_calendly_booking_date')
    d_cus = row.get('days_first_session_to_customer')
    cus_str = f'{int(d_cus)}d' if pd.notna(d_cus) else '—'
    cus_col = T['signed'] if (pd.notna(d_cus) and d_cus < 0) else T['text']

    ms = f'padding:14px 18px;border-right:1px solid {T["border"]};'
    ml = f'font-size:9px;font-family:Inter,sans-serif;color:{T["textMute"]};letter-spacing:0.1em;margin-bottom:6px;text-transform:uppercase;'
    mv = f'font-size:22px;font-weight:500;font-family:Inter,sans-serif;letter-spacing:-0.02em;'

    st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(5,1fr);
     border-top:1px solid {T['border']};border-bottom:1px solid {T['border']};margin-bottom:0;">
  <div style="{ms}"><div style="{ml}">Days active</div><div style="{mv}color:{T['text']};">{days_active}d</div></div>
  <div style="{ms}"><div style="{ml}">Form submissions</div><div style="{mv}color:{T['form']};">{forms}</div></div>
  <div style="{ms}"><div style="{ml}">Webinar reg.</div><div style="{mv}color:{T['webinar']};">{webinars}</div></div>
  <div style="{ms}"><div style="{ml}">Calls booked</div><div style="{mv}color:{T['call']};">{calls}</div></div>
  <div style="padding:14px 18px;"><div style="{ml}">&rarr; Customer</div><div style="{mv}color:{cus_col};">{cus_str}</div></div>
</div>
""", unsafe_allow_html=True)

    activities  = build_activities(row, sessions_df=sessions_df, pages_by_session=pages_by_session)
    session_count = sum(1 for a in activities if a['type'] in ('session_website', 'session_portal'))
    eng_count   = sum(1 for a in activities if a['type'] in ('form_submission', 'webinar_registration', 'calendly_booking'))

    col_main, col_rail = st.columns([2, 1], gap='large')

    with col_main:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            f'Activity timeline ({len(activities)})' + (f' · {session_count} sessions' if session_count else ''),
            f'Engagements ({eng_count})',
            'Acquisition',
            'DAS / Member' + (' ✓' if pd.notna(row.get('das_participant_number')) else ''),
            'Raw data',
        ])
        with tab1:
            st.markdown(render_timeline_html(activities), unsafe_allow_html=True)
        with tab2:
            render_engagements_tab(row)
        with tab3:
            render_acquisition_tab(row)
        with tab4:
            render_das_tab(row)
        with tab5:
            render_raw_tab(row)

    with col_rail:
        render_right_rail(row)


# ── list view ─────────────────────────────────────────────────────────────────

def render_list(df: pd.DataFrame) -> None:
    st.markdown(f"""
<div style="display:flex;align-items:baseline;gap:14px;margin-bottom:18px;">
  <h1 style="font-size:20px;font-weight:600;letter-spacing:-0.01em;color:{T['text']};">Profiles</h1>
  <span style="font-size:11px;font-family:Inter,sans-serif;color:{T['textMute']};letter-spacing:0.05em;">tab_profiles</span>
</div>
""", unsafe_allow_html=True)

    totals = {
        'all':      len(df),
        'customer': int((df['status'] == 'customer').sum()),
        'lead':     int((df['status'] == 'lead').sum()),
    }
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(kpi_card_html('Profiles',  f"{totals['all']:,}"),                   unsafe_allow_html=True)
    with c2: st.markdown(kpi_card_html('Customers', f"{totals['customer']:,}", color=T['customer']), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card_html('Leads',     f"{totals['lead']:,}",     color=T['lead']),     unsafe_allow_html=True)

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

    # ── Source mix / channel filter ───────────────────────────────────────────
    src_counts = df['initial_channel'].fillna('Direct').value_counts().to_dict()

    # Build ordered list of channels that actually have data
    ch_with_counts = [(ch, src_counts.get(ch, 0)) for ch in CHANNEL_META if src_counts.get(ch, 0) > 0]
    # pill label → channel name mapping
    pill_label_map: dict[str, str] = {}
    pill_options: list[str] = []
    for ch, cnt in ch_with_counts:
        label = f'{ch}  ({cnt})'
        pill_label_map[label] = ch
        pill_options.append(label)

    # Inject CSS so pills match the dark theme
    st.markdown(f"""
<style>
[data-testid="stPillsButton"] {{
    background:{T['bg2']} !important;
    border:1px solid {T['border']} !important;
    color:{T['textDim']} !important;
    font-size:11px !important;
    font-family:Inter,sans-serif !important;
    border-radius:4px !important;
    transition:border-color .15s,background .15s !important;
}}
[data-testid="stPillsButton"]:hover {{
    border-color:{T['borderHi']} !important;
    color:{T['text']} !important;
}}
[data-testid="stPillsButton"][aria-pressed="true"] {{
    background:{T['accent']}26 !important;
    border-color:{T['accent']} !important;
    color:{T['text']} !important;
}}
</style>
""", unsafe_allow_html=True)

    lbl_col, pills_col = st.columns([1, 11])
    with lbl_col:
        st.markdown(
            f'<div style="font-size:10px;font-family:Inter,sans-serif;color:{T["textMute"]};'
            f'letter-spacing:0.1em;padding-top:10px;white-space:nowrap;">SOURCE MIX</div>',
            unsafe_allow_html=True,
        )
    with pills_col:
        selected_pill = st.pills(
            'Channel filter', options=pill_options,
            selection_mode='single', default=None,
            label_visibility='collapsed', key='channel_pills',
        )

    selected_channel = pill_label_map.get(selected_pill) if selected_pill else None

    col_search, col_status, _ = st.columns([3, 5, 2])
    with col_search:
        query = st.text_input('Search', placeholder='Search email, name, channel…', label_visibility='collapsed', key='profile_search')
    with col_status:
        status_filter = st.radio('Status filter', ['All', 'Customers Full journey', 'Customers Retroactive', 'Leads'], horizontal=True, label_visibility='collapsed', key='profile_status')

    # Filter
    filtered = df.copy()
    if query:
        q = query.lower()
        idx = filtered.index
        fn_s = filtered.get('das_first_name',  pd.Series([''] * len(filtered), index=idx)).fillna('')
        ln_s = filtered.get('das_last_name',   pd.Series([''] * len(filtered), index=idx)).fillna('')
        mask = (
            filtered['Email'].str.lower().str.contains(q, na=False) |
            fn_s.str.lower().str.contains(q, na=False) |
            ln_s.str.lower().str.contains(q, na=False) |
            filtered['initial_channel'].fillna('').str.lower().str.contains(q, na=False)
        )
        filtered = filtered[mask]

    if status_filter == 'Customers Full journey':
        filtered = filtered[(filtered['status'] == 'customer') & (filtered['days_first_session_to_customer'].fillna(-1) >= 0)]
    elif status_filter == 'Customers Retroactive':
        filtered = filtered[(filtered['status'] == 'customer') & (filtered['days_first_session_to_customer'].fillna(0) < 0)]
    elif status_filter == 'Leads':
        filtered = filtered[filtered['status'] == 'lead']

    if selected_channel:
        filtered = filtered[filtered['initial_channel'].fillna('Direct') == selected_channel]

    # ── Pagination ────────────────────────────────────────────────────────────
    PAGE_SIZE    = 100
    total_filtered = len(filtered)
    total_pages  = max(1, (total_filtered + PAGE_SIZE - 1) // PAGE_SIZE)

    # Reset to page 0 whenever any filter changes
    filter_sig = f'{query}|{status_filter}|{selected_channel or ""}'
    if st.session_state.get('_profile_filter_sig') != filter_sig:
        st.session_state['_profile_filter_sig'] = filter_sig
        st.session_state['profile_page'] = 0

    page = max(0, min(st.session_state.get('profile_page', 0), total_pages - 1))
    start_row    = page * PAGE_SIZE
    end_row      = min(start_row + PAGE_SIZE, total_filtered)

    st.markdown(
        f'<div style="font-size:11px;font-family:Inter,sans-serif;color:{T["textMute"]};'
        f'text-align:right;margin-bottom:8px;">'
        f'{start_row + 1}–{end_row} of {total_filtered:,}'
        f'{"" if total_filtered == len(df) else f"  (total: {len(df):,})"}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Table — rendered in a declare_component iframe for reliable click→Python communication
    grid = '2fr 100px 96px 180px 130px 120px 88px 110px 28px'
    display_rows = filtered.iloc[start_row:end_row]

    th = (f'font-size:10px;font-family:Inter,sans-serif;color:{T["textMute"]};'
          f'letter-spacing:0.08em;text-transform:uppercase;')

    table_html = (
        # Hover style for rows
        f'<style>.cdp-row:hover{{background:{T["surfaceHi"]} !important;}}</style>'
        # Header
        f'<div style="display:grid;grid-template-columns:{grid};padding:8px 14px;gap:12px;'
        f'align-items:center;background:{T["surface"]};border:1px solid {T["border"]};border-radius:8px 8px 0 0;">'
        f'<div style="{th}">Email</div>'
        f'<div style="{th}">Status</div>'
        f'<div style="{th}">Profile date</div>'
        f'<div style="{th}">Channel / Source</div>'
        f'<div style="{th}">Location</div>'
        f'<div style="{th}">Engagement</div>'
        f'<div style="{th};text-align:right;">&rarr; Customer</div>'
        f'<div style="{th}">Name</div>'
        f'<div></div>'
        f'</div>'
        # Body wrapper
        f'<div style="background:{T["bg2"]};border:1px solid {T["border"]};'
        f'border-top:none;border-radius:0 0 8px 8px;overflow:hidden;">'
    )

    rs = (f'display:grid;grid-template-columns:{grid};gap:12px;padding:10px 14px;'
          f'border-bottom:1px solid {T["border"]};align-items:center;cursor:pointer;')

    for _, r in display_rows.iterrows():
        email = r['Email']
        fn    = _str(r.get('das_first_name'))
        ln    = _str(r.get('das_last_name'))
        name  = f'{fn} {ln}'.strip() or email.split('@')[0].replace('.', ' ').title()
        ch    = _str(r.get('initial_channel')) or 'Direct'
        src   = _str(r.get('initial_source'))
        loc   = ', '.join(filter(None, [_str(r.get('initial_city')), _str(r.get('initial_country'))]))[:22] or '—'
        d_cus = r.get('days_first_session_to_customer')
        cus_s = f'{int(d_cus)}d' if pd.notna(d_cus) else '—'
        cus_c = T['signed'] if (pd.notna(d_cus) and d_cus < 0) else T['textDim']
        src_span = (f'<span style="font-size:11px;color:{T["textMute"]};font-family:Inter,sans-serif;">{src}</span>'
                    if src else '')

        safe_email = email.replace('"', '&quot;')
        table_html += (
            f'<div class="cdp-row" data-email="{safe_email}" style="{rs}">'
            f'<div style="display:flex;align-items:center;gap:10px;min-width:0;">'
            f'{avatar_html(name, 22)}'
            f'<span style="font-family:Inter,sans-serif;font-size:12px;color:{T["text"]};'
            f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{email}</span>'
            f'</div>'
            f'<div>{status_badge_html(r.get("status", "lead"))}</div>'
            f'<div style="font-size:11px;font-family:Inter,sans-serif;color:{T["textDim"]};">{_fmt(r.get("profile_date"))}</div>'
            f'<div style="display:flex;align-items:center;gap:6px;min-width:0;overflow:hidden;">'
            f'{channel_badge_html(ch)}{src_span}</div>'
            f'<div style="font-size:11px;font-family:Inter,sans-serif;color:{T["textDim"]};'
            f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{loc}</div>'
            f'<div>{engagement_badges_html(_list_or_int(r, "form_submissions", date_col="first_submission_date"), _list_or_int(r, "webinar_registrations", "webinar_registration_count", "first_webinar_registration_date"), _list_or_int(r, "calendly_bookings", "calendly_booking_count", "first_calendly_booking_date"))}</div>'
            f'<div style="font-size:11px;font-family:Inter,sans-serif;color:{cus_c};text-align:right;">{cus_s}</div>'
            f'<div style="font-size:12px;color:{T["textDim"]};">{name}</div>'
            f'<div style="color:{T["textMute"]};text-align:right;font-size:14px;">›</div>'
            f'</div>'
        )

    table_html += '</div>'

    clicked_email = _profile_table(html=table_html, key='profile_table')
    if clicked_email:
        st.session_state.profile_email = clicked_email
        st.rerun()

    # ── Pagination controls ───────────────────────────────────────────────────
    if total_pages > 1:
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        pc_prev, pc_info, pc_next = st.columns([1, 4, 1])
        with pc_prev:
            if st.button('← Prev', disabled=(page == 0), key='pg_prev', use_container_width=True):
                st.session_state['profile_page'] = page - 1
                st.rerun()
        with pc_info:
            st.markdown(
                f'<div style="text-align:center;font-size:11px;font-family:Inter,sans-serif;'
                f'color:{T["textMute"]};padding-top:8px;">'
                f'Page {page + 1} of {total_pages}'
                f'</div>',
                unsafe_allow_html=True,
            )
        with pc_next:
            if st.button('Next →', disabled=(page >= total_pages - 1), key='pg_next', use_container_width=True):
                st.session_state['profile_page'] = page + 1
                st.rerun()


# ── entry point ───────────────────────────────────────────────────────────────

def render():
    inject_global_css()

    if 'profile_email' not in st.session_state:
        st.session_state.profile_email = None
    if 'profile_page' not in st.session_state:
        st.session_state['profile_page'] = 0

    with st.spinner(''):
        df = load_profiles()

    if df is None or df.empty:
        st.error('No profile data available.')
        return

    # Safe defaults for engagement counts / dates regardless of exact column names in BQ
    for col in ('webinar_registration_count', 'calendly_booking_count'):
        if col not in df.columns:
            df[col] = 0
    for col in (
        'first_webinar_registration_date', 'last_webinar_registration_date',
        'first_calendly_booking_date',     'last_calendly_booking_date',
    ):
        if col not in df.columns:
            df[col] = pd.NaT

    if st.session_state.profile_email:
        mask = df['Email'] == st.session_state.profile_email
        if mask.any():
            render_detail(df[mask].iloc[0])
            return
        st.session_state.profile_email = None

    render_list(df)
