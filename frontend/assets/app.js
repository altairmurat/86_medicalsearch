const API = '/api';
const $ = id => document.getElementById(id);
const money = n => new Intl.NumberFormat('ru-RU').format(n) + ' ₸';
let map, markers;

async function getJSON(url, options={}) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

function initMap(){
  map = L.map('mapBox').setView([48.0, 67.0], 5);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19, attribution:'&copy; OpenStreetMap'}).addTo(map);
  markers = L.layerGroup().addTo(map);
}

function updateMap(rows){
  markers.clearLayers();
  const seen = new Set();
  const points = [];
  rows.forEach(r => {
    if(!r.lat || !r.lon) return;
    const key = `${r.clinic_id}-${r.service}`;
    if(seen.has(key)) return;
    seen.add(key);
    const marker = L.circleMarker([r.lat, r.lon], {radius: 8, weight: 2, fillOpacity: .85});
    marker.bindPopup(`<b>${r.clinic_name}</b><br>${r.service}<br><b>${money(r.price_kzt)}</b><br>${r.address || ''}`);
    marker.addTo(markers);
    points.push([r.lat, r.lon]);
  });
  if(points.length === 1) map.setView(points[0], 13);
  else if(points.length > 1) map.fitBounds(points, {padding:[30,30]});
}

async function loadInitial(){
  const [stats, filters, services] = await Promise.all([getJSON(`${API}/stats`), getJSON(`${API}/filters`), getJSON(`${API}/services`)]);
  $('stats').innerHTML = `
    <div class="stat"><b>${stats.clinics}</b><span>клиник и источников</span></div>
    <div class="stat"><b>${stats.services}</b><span>нормализованных услуг</span></div>
    <div class="stat"><b>${stats.prices}</b><span>ценовых предложений</span></div>
    <div class="stat"><b>${stats.cities}</b><span>городов</span></div>`;
  filters.cities.forEach(c => $('city').insertAdjacentHTML('beforeend', `<option value="${c}">${c}</option>`));
  filters.categories.forEach(c => $('category').insertAdjacentHTML('beforeend', `<option value="${c}">${c}</option>`));
  $('serviceChips').innerHTML = services.map(s=>`<button class="chip" data-name="${s.name.replaceAll('"','&quot;')}">${s.name}<small>${s.category}</small></button>`).join('');
  document.querySelectorAll('.chip').forEach(ch => ch.onclick = () => { $('q').value = ch.dataset.name; search(); location.hash = '#search'; });
}

async function updateSuggest(){
  const q = $('q').value.trim();
  const data = await getJSON(`${API}/suggest?q=${encodeURIComponent(q)}`);
  $('normalized').textContent = q ? `Понимаем как: ${data.normalized}` : '';
  $('suggestions').innerHTML = data.suggestions.map(s=>`<option value="${s}"></option>`).join('');
}

function renderResults(rows){
  $('resultCount').textContent = `${rows.length} найдено`;
  if(!rows.length){
    $('results').innerHTML = `<div class="card empty"><b>Ничего не найдено</b><p>Попробуй другой город, категорию или напиши услугу проще: «оак», «узи», «терапевт».</p></div>`;
    updateMap([]);
    return;
  }
  const best = Math.min(...rows.map(r=>r.price_kzt));
  $('results').innerHTML = rows.map(r => `
    <article class="card ${r.price_kzt===best?'best':''}">
      <div class="cardTop">
        <div><div class="clinicName">${r.clinic_name}</div><div class="service">${r.service}</div></div>
        <div class="price">${money(r.price_kzt)}</div>
      </div>
      <div class="meta">
        <span>📍 ${r.city}</span><span>${r.address || 'адрес не указан'}</span><span>⭐ ${Number(r.rating).toFixed(1)}</span>
        <span>${r.category}</span><span>${r.online_booking ? 'online-запись' : 'по телефону'}</span><a href="${r.source_url}" target="_blank">источник</a>
      </div>
    </article>`).join('');
  updateMap(rows);
}

async function search(){
  const params = new URLSearchParams({
    q: $('q').value.trim(), city: $('city').value, category: $('category').value,
    sort: $('sort').value, limit: '1500', max_price: $('maxPrice').value || '1000000'
  });
  const data = await getJSON(`${API}/search?${params}`);
  $('normalized').textContent = data.query ? `Понимаем как: ${data.normalized}` : '';
  renderResults(data.results);
}

async function askAI(){
  const message = $('aiMessage').value.trim();
  if(!message){ alert('Напиши симптомы или вопрос'); return; }
  $('aiBtn').disabled = true; $('aiBtn').textContent = 'AI думает...';
  $('aiAnswer').classList.remove('hidden');
  $('aiAnswer').innerHTML = '<p>Ищу подходящие услуги...</p>';
  try{
    const data = await getJSON(`${API}/ai/recommend`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message})});
    $('aiAnswer').innerHTML = `<p>${data.reply}</p><div class="aiServices">${data.recommended_services.map(s=>`<button class="aiService" data-name="${s}">${s}</button>`).join('')}</div><small>Режим: ${data.mode}</small>`;
    document.querySelectorAll('.aiService').forEach(btn => btn.onclick = () => { $('q').value = btn.dataset.name; search(); location.hash = '#search'; });
  }catch(e){ $('aiAnswer').innerHTML = `<p>Ошибка AI: ${e.message}</p>`; }
  $('aiBtn').disabled = false; $('aiBtn').textContent = 'Получить рекомендации';
}

window.addEventListener('DOMContentLoaded', async () => {
  initMap();
  await loadInitial();
  await search();
  $('searchBtn').onclick = search;
  ['city','category','sort','maxPrice'].forEach(id => $(id).onchange = search);
  $('q').addEventListener('input', updateSuggest);
  $('q').addEventListener('keydown', e => { if(e.key === 'Enter') search(); });
  $('aiBtn').onclick = askAI;
});
