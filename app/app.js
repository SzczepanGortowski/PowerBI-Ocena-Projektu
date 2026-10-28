'use strict';
/* Panel „Standardy wizualizacji”. Gospodarz (okno.ps1): start → analiza → postep* → wynik | blad.
   Wynik zawiera znaleziska wszystkich reguł; wybór standardów i reguł filtruje widok i liczy ocenę od razu,
   bez ponownej analizy. Wybór odsyłany do gospodarza (akcja „wybor”) jest zapamiętywany. */

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const host = window.chrome && window.chrome.webview;

const WAGA = { blad: 'błąd', ostrzezenie: 'ostrzeżenie', info: 'info' };
const WAGI_MN = { blad: 'Błędy', ostrzezenie: 'Ostrzeżenia', info: 'Info' };
const KOLEJ = { blad: 0, ostrzezenie: 1, info: 2 };
const KOLOR = { blad: 'var(--waga-blad)', ostrzezenie: 'var(--waga-ostrzezenie)', info: 'var(--waga-info)' };
const PUNKTY = { blad: 10, ostrzezenie: 4, info: 1 };
const KROKI = [['raport', 'Raport'], ['model', 'Model'], ['reguly', 'Standardy']];
const UDZIAL = { raport: 30, model: 40, reguly: 30 };

const S = {
  ikony: {}, w: null, folder: '', zapisany: null, wyb: null, zakladka: 'problemy', waga: '', std: '', q: '',
  otwarte: new Set(), pelne: new Set(), otwarteStd: new Set(), kroki: {}, biegnie: false,
  wybrana: {}, zrzuty: {}, zrzutTrwa: new Set(),
};

/* ---------------------------------------------------------------- pomocnicze */
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const ik = (n) => `<span data-ikona="${n}">${S.ikony[n] || ''}</span>`;
function wypelnijIkony(root = document) {
  $$('[data-ikona]', root).forEach((e) => { const s = S.ikony[e.dataset.ikona]; if (s && !e.innerHTML) e.innerHTML = s; });
}
function wyslij(akcja, dane = {}) {
  const m = JSON.stringify({ akcja, ...dane });
  if (host) host.postMessage(m); else console.log('→ gospodarz', m);
}
function odm(n, a, b, c) {
  if (n === 1) return `1 ${a}`;
  if ([2, 3, 4].includes(n % 10) && ![12, 13, 14].includes(n % 100)) return `${n} ${b}`;
  return `${n} ${c}`;
}
const kolorOceny = (p) => (p == null ? 'var(--tekst3)' : p >= 85 ? 'var(--signal-good)' : p >= 60 ? 'var(--signal-warning)' : 'var(--signal-bad)');
const slowo = (p) => (p == null ? 'brak wyboru' : p >= 85 ? 'dobra' : p >= 60 ? 'do poprawy' : 'słaba');
const godz = (iso) => (iso ? iso.replace('T', ' ').slice(0, 16) : '—');
let tToast;
function toast(t) {
  const e = $('#toast'); e.textContent = t; e.hidden = false;
  clearTimeout(tToast); tToast = setTimeout(() => { e.hidden = true; }, 2400);
}

/* ---------------------------------------------------------------- wybór standardów i reguł */
function ustawWybor(w) {
  const z = S.zapisany;
  const znane = new Set(w.standardy.map((s) => s.id));
  const std = z && Array.isArray(z.standardy) ? z.standardy.filter((x) => znane.has(x)) : w.domyslne;
  const wyl = z && Array.isArray(z.wylaczone) ? z.wylaczone.filter((x) => w.reguly[x]) : [];
  S.wyb = { std: new Set(std), wyl: new Set(wyl) };
}
function zapiszWybor() {
  S.zapisany = { standardy: [...S.wyb.std], wylaczone: [...S.wyb.wyl] };
  wyslij('wybor', { wybor: S.zapisany });
}
const regula = (id) => S.w.reguly[id] || {};
const aktywna = (id) => {
  const r = S.w.reguly[id];
  return !!r && S.wyb.std.has(r.standard) && !S.wyb.wyl.has(id) && r.status !== 'błąd reguły';
};
const wybraneStd = () => S.w.standardy.filter((s) => S.wyb.std.has(s.id));
const nazwaStd = (id) => (S.w.standardy.find((s) => s.id === id) || {}).krotko || id;
const widoczne = () => S.w.problemy.filter((p) => aktywna(p.regula));

function ocenStandard(sid) {
  const st = S.w.standardy.find((s) => s.id === sid);
  if (!st || !st.reguly.some(aktywna)) return null;
  const per = {}, licz = { blad: 0, ostrzezenie: 0, info: 0 };
  S.w.problemy.forEach((p) => {
    if (p.standard !== sid || !aktywna(p.regula)) return;
    licz[p.waga] += 1;
    const k = `${p.regula}|${p.waga}`;
    per[k] = (per[k] || 0) + 1;
  });
  let kara = 0;
  Object.entries(per).forEach(([k, n]) => { const w = k.split('|')[1]; kara += Math.min(PUNKTY[w] * (1 + Math.log2(n)), 3 * PUNKTY[w]); });
  return { punkty: Math.max(0, Math.round(100 - kara)), liczniki: licz };
}
function oceny() {
  const o = {};
  wybraneStd().forEach((s) => { o[s.id] = ocenStandard(s.id); });
  const pk = Object.values(o).filter(Boolean).map((x) => x.punkty);
  return { oceny: o, ogolna: pk.length ? Math.round(pk.reduce((a, b) => a + b, 0) / pk.length) : null };
}

/* ---------------------------------------------------------------- komunikaty od gospodarza */
window.odbierz = function (m) {
  if (typeof m === 'string') m = JSON.parse(m);
  switch (m.typ) {
    case 'start':
      S.ikony = m.ikony || {}; S.zapisany = m.wybor || null; wypelnijIkony();
      if (m.raport) $('#r-nazwa').textContent = m.raport;
      tryb(m); break;
    case 'tryb': tryb(m); break;
    case 'analiza': rozpocznij(m); break;
    case 'postep': postep(m.dane || {}); break;
    case 'wynik': pokazWynik(m); break;
    case 'blad': blad(m.tekst); break;
    case 'zrzut': zrzut(m); break;
    case 'toast': toast(m.tekst); break;
    default: break;
  }
};
if (host) host.addEventListener('message', (e) => window.odbierz(e.data));

function tryb(m) {
  const b = document.body;
  if ('przypiety' in m) {
    b.classList.toggle('plywajacy', !m.przypiety);
    const p = $('#b-przypnij');
    p.title = m.przypiety ? 'Odepnij od Power BI (zwykłe okno)' : 'Przypnij do prawej krawędzi Power BI';
    p.innerHTML = ik(m.przypiety ? 'ic_locked' : 'ic_unlocked');
    $('#b-zwin').disabled = !m.przypiety;
  }
  if ('zwiniety' in m) b.classList.toggle('zwiniety', !!m.zwiniety);
  if ('szeroki' in m) b.classList.toggle('szeroki', !!m.szeroki);
}

function rozpocznij(m) {
  S.biegnie = true; S.kroki = {};
  document.body.classList.add('biegnie');
  $('#b-ponownie').disabled = true;
  $('#blad').hidden = true;
  $('#postep').hidden = false;
  if (m && m.raport) $('#r-nazwa').textContent = m.raport;
  rysujKroki();
}

function postep(d) {
  if (d.krok === 'blad') { blad(d.tekst); return; }
  if (d.krok === 'gotowe') { $('#postep-pasek').style.width = '100%'; return; }
  S.kroki[d.krok] = d;
  rysujKroki();
}

function rysujKroki() {
  let proc = 0;
  $('#kroki').innerHTML = KROKI.map(([k, n]) => {
    const d = S.kroki[k];
    const stan = d ? d.stan : 'czeka';
    if (d) proc += ['ok', 'uwaga', 'pominiety'].includes(stan) ? UDZIAL[k] : UDZIAL[k] * ((d.proc || 25) / 100);
    return `<li class="${stan}"><i class="znak"></i><div><b>${n}</b><span>${esc(d ? d.tekst : 'czeka')}</span></div></li>`;
  }).join('');
  $('#postep-pasek').style.width = `${Math.min(100, Math.round(proc))}%`;
}

function blad(t) {
  S.biegnie = false;
  document.body.classList.remove('biegnie', 'laduje');
  $('#b-ponownie').disabled = false;
  const e = $('#blad');
  e.innerHTML = `<b>Sprawdzenie się nie udało</b>${esc(t)}<br><br>Kliknij ${ik('ic_refresh')} u góry, żeby spróbować ponownie.`;
  e.hidden = false;
}

/* ---------------------------------------------------------------- wynik */
function pokazWynik(m) {
  S.w = m.wynik; S.folder = m.folder || S.w.folder || '';
  S.biegnie = false; S.zrzuty = {}; S.wybrana = {};
  ustawWybor(S.w);
  document.body.classList.remove('biegnie', 'laduje');
  $('#b-ponownie').disabled = false;
  setTimeout(() => { if (!S.biegnie) $('#postep').hidden = true; }, 700);
  $('#wynik').hidden = false;
  rysujWszystko();
}

function rysujWszystko() {
  const w = S.w;
  if (!w) return;
  $('#r-nazwa').textContent = w.raport || 'Raport';
  const model = w.model && w.model.status === 'ok' ? 'model ✓' : 'bez modelu';
  const meta = [w.format, w.zapisano ? `zapisany ${godz(w.zapisano)}` : '', `sprawdzono ${godz(w.sprawdzono).slice(11)}`,
    `motyw ${w.motyw}`, model].filter(Boolean);
  $('#r-meta').textContent = meta.join(' · ');
  $('#banery').innerHTML = (w.ostrzezenia || []).map((o) => `<div class="baner">${ik('ic_notification_warning')}<div>${esc(o)}</div></div>`).join('')
    + (w.bledy_regul || []).map((b) => `<div class="baner">${ik('ic_notification_warning')}<div>Reguła się nie wykonała: ${esc(b.split('\n')[0])}</div></div>`).join('');
  rysujOceny();
  rysujMini();
  $('#z-problemy').textContent = widoczne().length;
  $('#z-strony').textContent = (w.strony || []).length || '';
  $('#z-standardy').textContent = `${S.wyb.std.size}/${w.standardy.length}`;
  rysujZakladke();
}

function pierscien(p) {
  const r = 44, c = 2 * Math.PI * r, d = p == null ? 0 : (c * p) / 100;
  return `<svg viewBox="0 0 104 104" width="104" height="104" aria-hidden="true">
    <circle cx="52" cy="52" r="${r}" fill="none" stroke="var(--linia)" stroke-width="10"/>
    <circle cx="52" cy="52" r="${r}" fill="none" stroke="${kolorOceny(p)}" stroke-width="10" stroke-linecap="round"
      stroke-dasharray="${d} ${c}" transform="rotate(-90 52 52)"/></svg>
    <div class="liczba"><b>${p == null ? '—' : p}</b><small>${slowo(p)}</small></div>`;
}

function rysujOceny() {
  const { oceny: oc, ogolna } = oceny();
  $('#pierscien').innerHTML = pierscien(ogolna);
  const st = wybraneStd();
  if (!st.length) {
    $('#kategorie').innerHTML = '<div class="brak-wyboru">Nie wybrano żadnego standardu. <button data-z-idz="standardy">Wybierz standardy</button></div>';
    return;
  }
  $('#kategorie').innerHTML = st.map((s) => {
    const o = oc[s.id];
    if (!o) {
      return `<div class="kat brak" data-kat="${s.id}"><span class="n">${esc(s.nazwa)}</span><span class="p">—</span><div class="bar"></div>
        <div class="licz">wszystkie reguły wyłączone</div></div>`;
    }
    const l = o.liczniki;
    return `<div class="kat" data-kat="${s.id}" title="Pokaż problemy: ${esc(s.nazwa)}"><span class="n">${esc(s.nazwa)}</span><span class="p">${o.punkty}</span>
      <div class="bar"><i style="width:${o.punkty}%;background:${kolorOceny(o.punkty)}"></i></div>
      <div class="licz">${['blad', 'ostrzezenie', 'info'].map((x) => `<span><i class="kropka" style="background:${KOLOR[x]}"></i>${l[x] || 0}</span>`).join('')}</div></div>`;
  }).join('');
}

function rysujMini() {
  const p = oceny().ogolna;
  const e = $('#mini-ocena'); e.textContent = p == null ? '—' : p; e.style.background = kolorOceny(p);
  const licz = { blad: 0, ostrzezenie: 0, info: 0 };
  widoczne().forEach((x) => { licz[x.waga] += 1; });
  $('#mini-licz').innerHTML = ['blad', 'ostrzezenie', 'info'].map((x) => `<span><i class="kropka" style="background:${KOLOR[x]};margin:0"></i>${licz[x]}</span>`).join('');
}

/* ---------------------------------------------------------------- zakładki */
function idzDo(z) {
  S.zakladka = z;
  $$('#zakladki button').forEach((x) => x.classList.toggle('aktywna', x.dataset.z === z));
  rysujZakladke();
}
$$('#zakladki button').forEach((b) => b.addEventListener('click', () => idzDo(b.dataset.z)));
function rysujZakladke() {
  ['problemy', 'strony', 'standardy'].forEach((z) => { $(`#w-${z}`).hidden = z !== S.zakladka; });
  ({ problemy: rysujProblemy, strony: rysujStrony, standardy: rysujStandardy })[S.zakladka]();
  wypelnijIkony();
}

/* ---------------------------------------------------------------- problemy */
function rysujProblemy() {
  const wid = widoczne();
  if (S.std && !S.wyb.std.has(S.std)) S.std = '';
  const licz = { blad: 0, ostrzezenie: 0, info: 0 };
  wid.forEach((p) => { licz[p.waga] += 1; });
  $('#chipy-wagi').innerHTML = `<button class="chip" data-waga="" aria-pressed="${!S.waga}">Wszystkie ${wid.length}</button>`
    + ['blad', 'ostrzezenie', 'info'].map((x) => `<button class="chip" data-waga="${x}" aria-pressed="${S.waga === x}">
      <i class="kropka" style="background:${KOLOR[x]}"></i>${WAGI_MN[x]} ${licz[x]}</button>`).join('');
  $('#chipy-std').innerHTML = wybraneStd().map((s) => `<button class="chip" data-std="${s.id}" aria-pressed="${S.std === s.id}">
      ${esc(s.krotko)} ${wid.filter((p) => p.standard === s.id).length}</button>`).join('');

  const grupy = {};
  wid.forEach((p) => {
    if (S.waga && p.waga !== S.waga) return;
    if (S.std && p.standard !== S.std) return;
    if (S.q) {
      const r = regula(p.regula);
      if (!`${p.regula} ${r.tytul} ${p.strona} ${p.obiekt} ${p.opis}`.toLowerCase().includes(S.q)) return;
    }
    (grupy[p.regula] = grupy[p.regula] || []).push(p);
  });
  const ids = Object.keys(grupy).sort((a, b) => {
    const wa = Math.min(...grupy[a].map((p) => KOLEJ[p.waga])), wb = Math.min(...grupy[b].map((p) => KOLEJ[p.waga]));
    return wa - wb || grupy[b].length - grupy[a].length || a.localeCompare(b);
  });
  if (!S.wyb.std.size) {
    $('#lista-problemow').innerHTML = '<div class="pusto">Nie wybrano standardów.<br><button class="wiecej" data-z-idz="standardy">Wybierz standardy</button></div>';
    return;
  }
  if (!ids.length) {
    $('#lista-problemow').innerHTML = wid.length
      ? '<div class="pusto">Nic nie pasuje do filtrów.</div>'
      : `<div class="pusto">${ik('ic_quality')}<br><b>Brak problemów</b><br>Raport spełnia wszystkie wybrane standardy.</div>`;
    return;
  }
  $('#lista-problemow').innerHTML = ids.map((id) => {
    const r = regula(id);
    const lista = grupy[id].sort((a, b) => KOLEJ[a.waga] - KOLEJ[b.waga] || (a.strona || '').localeCompare(b.strona || ''));
    const najg = lista[0].waga;
    const pelna = S.pelne.has(id);
    const wyst = (pelna ? lista : lista.slice(0, 25)).map((p) => `<div class="wystapienie"><i class="kropka" style="background:${KOLOR[p.waga]}"></i><div>
      <div class="gdzie">${esc([p.strona, p.obiekt].filter(Boolean).join(' › '))}</div><div class="co">${esc(p.opis)}</div></div></div>`).join('');
    return `<article class="regula ${S.otwarte.has(id) ? 'otwarta' : ''}" data-id="${id}" style="--kolor:${KOLOR[najg]}">
      <div class="glowa"><div><span class="waga">${WAGA[najg]}</span> <span class="id">${id}</span><span class="etykieta-std">${esc(nazwaStd(r.standard))}</span>
      <div class="tytul">${esc(r.tytul)}</div></div><span class="ile">${lista.length}</span></div>
      <div class="cialo"><div class="opis"><p><b>Dlaczego.</b> ${esc(r.dlaczego)}</p><p><b>Jak naprawić.</b> ${esc(r.jak)}</p>
      ${r.zrodlo ? `<p style="color:var(--tekst3)">Źródło: ${esc(r.zrodlo)}</p>` : ''}</div>${wyst}
      ${!pelna && lista.length > 25 ? `<button class="wiecej" data-wiecej="${id}">Pokaż wszystkie (${lista.length})</button>` : ''}</div></article>`;
  }).join('');
}

/* ---------------------------------------------------------------- strony */
function makieta(s) {
  const el = [`<rect x="0" y="0" width="${s.w}" height="${s.h}" fill="var(--neutral-white2)"/>`];
  const zrz = S.zrzuty[s.nazwa];
  if (zrz) el.push(`<image href="${zrz}" x="0" y="0" width="${s.w}" height="${s.h}" preserveAspectRatio="none"/>`);
  else if (s.obszar) {
    const [x0, y0, x1, y1] = s.obszar;
    el.push(`<rect x="${x0}" y="${y0}" width="${x1 - x0}" height="${y1 - y0}" fill="var(--neutral-white1)" stroke="var(--neutral-white4)" stroke-dasharray="8 5" stroke-width="2"/>`);
  }
  s.wizualizacje.filter((v) => !v.ukryta).forEach((v) => {
    const pr = v.problemy.filter((p) => aktywna(p.regula));
    const waga = pr.length ? pr.reduce((a, p) => (KOLEJ[p.waga] < KOLEJ[a] ? p.waga : a), 'info') : null;
    const kol = waga ? KOLOR[waga] : 'var(--neutral-black5)';
    const wyp = zrz ? 'transparent' : (v.chrom ? 'var(--neutral-white3)' : 'var(--neutral-white1)');
    const gr = waga ? 4 : (zrz ? 0 : 2);
    const roz = Math.max(18, Math.min(26, v.h / 5));
    const wyb = S.wybrana[s.nazwa] === v.nazwa ? ' wybrana' : '';
    const tytul = [v.etykieta, ...pr.slice(0, 6).map((p) => `${p.regula}: ${p.opis}`)].join('\n');
    el.push(`<g class="wiz${wyb}" data-strona="${esc(s.nazwa)}" data-nazwa="${esc(v.nazwa)}"><title>${esc(tytul)}</title>
      <rect x="${v.x}" y="${v.y}" width="${Math.max(v.w, 1)}" height="${Math.max(v.h, 1)}" rx="6" fill="${wyp}" stroke="${kol}" stroke-width="${gr}"/>
      ${zrz ? '' : `<text x="${v.x + 8}" y="${v.y + roz + 6}" font-size="${roz}" fill="var(--neutral-black3)">${esc(v.typ)}${pr.length ? ` · ${pr.length}` : ''}</text>`}</g>`);
  });
  return `<svg class="makieta" viewBox="0 0 ${s.w} ${s.h}" role="img" aria-label="Układ strony ${esc(s.tytul)}">${el.join('')}</svg>`;
}

function wpisy(lista) {
  return lista.map((p) => `<div class="wystapienie"><i class="kropka" style="background:${KOLOR[p.waga]}"></i><div>
    <div class="gdzie">${p.regula} · ${esc(regula(p.regula).tytul)}</div><div class="co">${esc(p.opis)}</div></div></div>`).join('');
}

function rysujStrony() {
  const st = S.w.strony || [];
  if (!st.length) { $('#w-strony').innerHTML = '<div class="pusto">Raport nie ma stron do oceny.</div>'; return; }
  $('#w-strony').innerHTML = st.map((s) => {
    const n = s.wizualizacje.filter((v) => !v.ukryta && !v.chrom).length;
    const prStr = s.problemy_strony.filter((p) => aktywna(p.regula));
    const prWiz = s.wizualizacje.flatMap((v) => v.problemy.filter((p) => aktywna(p.regula)));
    const licz = { blad: 0, ostrzezenie: 0, info: 0 };
    [...prStr, ...prWiz].forEach((p) => { licz[p.waga] += 1; });
    const wyb = s.wizualizacje.find((v) => v.nazwa === S.wybrana[s.nazwa]);
    const szcz = wyb ? `<div class="szczegoly-wiz"><b>${esc(wyb.etykieta)}</b>${wpisy(wyb.problemy.filter((p) => aktywna(p.regula)))
      || '<div class="gdzie" style="padding:6px 0">Bez uwag w wybranych standardach.</div>'}</div>` : '';
    const trwa = S.zrzutTrwa.has(s.nazwa);
    return `<article class="strona"><div class="glowa"><h3>${esc(s.tytul)}</h3>${s.ukryta ? '<span class="tag">ukryta</span>' : ''}
      <div class="licz">${['blad', 'ostrzezenie', 'info'].map((x) => `<span><i class="kropka" style="background:${KOLOR[x]}"></i>${licz[x]}</span>`).join('')}</div>
      <div class="meta">${odm(n, 'wizualizacja', 'wizualizacje', 'wizualizacji')} · ${s.w}×${s.h} · kliknij prostokąt, żeby zobaczyć uwagi</div></div>
      ${makieta(s)}
      <div class="akcje"><button data-zrzut="${esc(s.nazwa)}" ${trwa ? 'disabled' : ''}>${ik('ic_camera')}${trwa ? 'Robię zrzut…' : (S.zrzuty[s.nazwa] ? 'Odśwież zrzut' : 'Pokaż prawdziwy wygląd')}</button></div>
      ${szcz}${prStr.length ? `<div class="uwagi-strony"><b>Uwagi do strony</b>${wpisy(prStr)}</div>` : ''}</article>`;
  }).join('');
  wypelnijIkony($('#w-strony'));
}

function zrzut(m) {
  S.zrzutTrwa.delete(m.strona);
  if (m.dane) S.zrzuty[m.strona] = m.dane; else toast(m.blad || 'Nie udało się zrobić zrzutu strony');
  if (S.zakladka === 'strony') rysujStrony();
}

/* ---------------------------------------------------------------- standardy (wybór) */
function rowneZbiory(a, b) { return a.size === b.size && [...a].every((x) => b.has(x)); }

function rysujStandardy() {
  const w = S.w;
  $('#profile').innerHTML = Object.entries(w.profile).map(([k, p]) =>
    `<button class="chip" data-profil="${k}" aria-pressed="${rowneZbiory(S.wyb.std, new Set(p.standardy))}">${esc(p.nazwa)}</button>`).join('');
  const per = {};
  w.problemy.forEach((p) => { per[p.regula] = (per[p.regula] || 0) + 1; });
  $('#lista-standardow').innerHTML = w.standardy.map((s) => {
    const wl = S.wyb.std.has(s.id);
    const o = wl ? ocenStandard(s.id) : null;
    const zUwagami = s.reguly.filter((r) => per[r] && !S.wyb.wyl.has(r)).length;
    const wyl = s.reguly.filter((r) => S.wyb.wyl.has(r)).length;
    const opis = [odm(s.reguly.length, 'reguła', 'reguły', 'reguł'), zUwagami ? `${zUwagami} z uwagami` : 'bez uwag',
      wyl ? `${wyl} wyłączone` : ''].filter(Boolean).join(' · ');
    const reg = s.reguly.map((rid) => {
      const r = w.reguly[rid];
      const off = S.wyb.wyl.has(rid);
      const n = per[rid] || 0;
      const st = r.status === 'błąd reguły' ? '<span class="st uwaga">błąd reguły</span>'
        : off ? '<span class="st">wyłączona</span>'
          : n ? `<span class="st zle">${n}×</span>` : '<span class="st dobrze">zgodne</span>';
      return `<label class="r-wiersz ${off ? 'wyl' : ''} ${wl ? '' : 'nieaktywny'}" title="${esc(r.dlaczego)}">
        <input type="checkbox" data-reg="${rid}" ${off ? '' : 'checked'} ${wl ? '' : 'disabled'}>
        <code>${rid}</code><span class="t">${esc(r.tytul)} <small style="color:var(--tekst3)">· ${WAGA[r.waga]}</small></span>${st}</label>`;
    }).join('');
    return `<article class="std ${wl ? 'wl' : ''} ${S.otwarteStd.has(s.id) ? 'otwarty' : ''}" data-std="${s.id}">
      <div class="std-glowa">
        <label class="przel" title="${wl ? 'Wyłącz' : 'Włącz'} standard"><input type="checkbox" data-std-wl="${s.id}" ${wl ? 'checked' : ''}><i></i></label>
        <div class="std-tekst" data-std-rozwin="${s.id}"><b>${esc(s.nazwa)}</b><span>${opis}</span></div>
        <span class="std-ocena" style="color:${kolorOceny(o ? o.punkty : null)}">${o ? o.punkty : ''}</span>
        <button class="ik-rozwin" data-std-rozwin="${s.id}" title="Reguły standardu">${ik('ic_chevron_bottom')}</button>
      </div>
      <div class="std-cialo"><div class="std-opis"><p>${esc(s.opis)}</p><p class="zr">Źródło: ${esc(s.zrodlo)}</p></div>${reg}</div></article>`;
  }).join('');
  wypelnijIkony($('#w-standardy'));
}

function zmienWybor() {
  zapiszWybor();
  rysujWszystko();
}

/* ---------------------------------------------------------------- lista zadań (Markdown) */
function markdown() {
  const w = S.w;
  const { oceny: oc, ogolna } = oceny();
  const st = wybraneStd();
  const lin = [`# Standardy wizualizacji — „${w.raport}” (${godz(w.sprawdzono)})`, '',
    `Plik: \`${w.sciezka}\`  `, `Ocena (wybrane standardy): **${ogolna ?? '—'}/100**  `,
    `Standardy: ${st.map((s) => `${s.nazwa} ${oc[s.id] ? oc[s.id].punkty : '—'}`).join(', ')}`,
    S.wyb.wyl.size ? `Wyłączone reguły: ${[...S.wyb.wyl].join(', ')}` : '', '',
    'Poprawki w Power BI Desktop albo w plikach PBIR (np. z pomocą asystenta AI); po zmianach zapisz raport i sprawdź ponownie.', ''];
  const pogr = {};
  widoczne().forEach((p) => { (pogr[p.regula] = pogr[p.regula] || []).push(p); });
  const ids = Object.keys(pogr).sort((a, b) => Math.min(...pogr[a].map((p) => KOLEJ[p.waga])) - Math.min(...pogr[b].map((p) => KOLEJ[p.waga])) || a.localeCompare(b));
  if (!ids.length) lin.push('Brak problemów w wybranych standardach.');
  ids.forEach((id) => {
    const r = regula(id);
    lin.push(`## ${id} · ${r.tytul} (${pogr[id].length}) — ${(S.w.standardy.find((s) => s.id === r.standard) || {}).nazwa}`);
    lin.push(`Jak naprawić: ${r.jak}`);
    pogr[id].slice(0, 40).forEach((p) => lin.push(`- [${WAGA[p.waga]}] ${[p.strona, p.obiekt].filter(Boolean).join(' › ')}: ${p.opis}`));
    if (pogr[id].length > 40) lin.push(`- … i ${pogr[id].length - 40} kolejnych (wynik.json)`);
    lin.push('');
  });
  return lin.filter((x, i, a) => !(x === '' && a[i - 1] === '')).join('\n');
}

/* ---------------------------------------------------------------- zdarzenia */
document.addEventListener('click', (e) => {
  const t = e.target;
  const idz = t.closest('[data-z-idz]');
  if (idz) { idzDo(idz.dataset.zIdz); return; }
  const kat = t.closest('#kategorie .kat');
  if (kat && kat.dataset.kat) { S.std = kat.dataset.kat; S.waga = ''; idzDo('problemy'); return; }
  const chipW = t.closest('#chipy-wagi .chip');
  if (chipW) { S.waga = chipW.dataset.waga; rysujProblemy(); wypelnijIkony(); return; }
  const chipS = t.closest('#chipy-std .chip');
  if (chipS) { S.std = S.std === chipS.dataset.std ? '' : chipS.dataset.std; rysujProblemy(); wypelnijIkony(); return; }
  const wiecej = t.closest('[data-wiecej]');
  if (wiecej) { S.pelne.add(wiecej.dataset.wiecej); rysujProblemy(); wypelnijIkony(); return; }
  const glowa = t.closest('.regula > .glowa');
  if (glowa) {
    const art = glowa.parentElement, id = art.dataset.id;
    if (S.otwarte.has(id)) S.otwarte.delete(id); else S.otwarte.add(id);
    art.classList.toggle('otwarta');
    return;
  }
  const wiz = t.closest('.makieta .wiz');
  if (wiz) { S.wybrana[wiz.dataset.strona] = wiz.dataset.nazwa; rysujStrony(); return; }
  const zrz = t.closest('[data-zrzut]');
  if (zrz) { S.zrzutTrwa.add(zrz.dataset.zrzut); wyslij('zrzut', { strona: zrz.dataset.zrzut }); rysujStrony(); return; }
  const prof = t.closest('[data-profil]');
  if (prof) {
    S.wyb.std = new Set(S.w.profile[prof.dataset.profil].standardy);
    zmienWybor();
    toast(`Profil: ${S.w.profile[prof.dataset.profil].nazwa}`);
    return;
  }
  const rozw = t.closest('[data-std-rozwin]');
  if (rozw) {
    const id = rozw.dataset.stdRozwin;
    if (S.otwarteStd.has(id)) S.otwarteStd.delete(id); else S.otwarteStd.add(id);
    rysujStandardy();
  }
});
document.addEventListener('change', (e) => {
  const t = e.target;
  if (t.dataset.stdWl) {
    if (t.checked) S.wyb.std.add(t.dataset.stdWl); else S.wyb.std.delete(t.dataset.stdWl);
    zmienWybor();
  } else if (t.dataset.reg) {
    if (t.checked) S.wyb.wyl.delete(t.dataset.reg); else S.wyb.wyl.add(t.dataset.reg);
    zmienWybor();
  }
});
$('#szukaj').addEventListener('input', (e) => { S.q = e.target.value.trim().toLowerCase(); rysujProblemy(); wypelnijIkony(); });

$('#b-ponownie').addEventListener('click', () => wyslij('ponownie'));
$('#b-szerzej').addEventListener('click', () => wyslij('szerzej'));
$('#b-zwin').addEventListener('click', () => wyslij('zwin'));
$('#b-przypnij').addEventListener('click', () => wyslij('przypnij'));
$('#b-zamknij').addEventListener('click', () => wyslij('zamknij'));
$('#pasek-zwiniety').addEventListener('click', () => wyslij('rozwin'));
$('#b-kopiuj').addEventListener('click', () => {
  if (!S.w) return;
  wyslij('kopiuj', { tekst: markdown() });
  toast('Skopiowano listę zadań (Markdown)');
});
$('#b-folder').addEventListener('click', () => wyslij('otworz', { sciezka: S.folder }));
$('#naglowek').addEventListener('mousedown', (e) => {
  if (e.button === 0 && !e.target.closest('button') && document.body.classList.contains('plywajacy')) wyslij('przeciagnij');
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'F5') { e.preventDefault(); wyslij('ponownie'); }
  if (e.ctrlKey && e.key.toLowerCase() === 'f') { e.preventDefault(); idzDo('problemy'); $('#szukaj').focus(); }
});
document.addEventListener('contextmenu', (e) => { if (!e.target.closest('input')) e.preventDefault(); });

wyslij('gotowy');
