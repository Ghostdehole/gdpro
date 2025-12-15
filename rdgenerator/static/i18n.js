// static/i18n.js
let currentLang = localStorage.getItem('selectedLang') || 'zh';
let translations = {};

async function loadTranslations(lang) {
  try {
    const res = await fetch(`/locales/${lang}.json?_t=${Date.now()}`); 
    if (!res.ok) throw new Error(`Failed to load ${lang}.json`);
    return await res.json();
  } catch (e) {
    console.warn(`Fallback to English for ${lang}`, e);
    if (lang !== 'en') return loadTranslations('en');
    return {};
  }
}

function translatePage(pageKey) {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const text = translations[pageKey]?.[key] || translations.common?.[key] || key;
    if (el.tagName === 'INPUT' && (el.type === 'submit' || el.type === 'button')) {
      el.value = text;
    } else if (el.tagName === 'TITLE') {
      el.textContent = text;
    } else {
      el.textContent = text;
    }
  });

  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    el.placeholder = translations[pageKey]?.[key] || key;
  });
}

function switchLanguage(lang) {
  localStorage.setItem('selectedLang', lang);
  location.reload();
}


document.addEventListener('DOMContentLoaded', async () => {
  translations = await loadTranslations(currentLang);
  const pageKey = document.body.dataset.page;
  if (pageKey) translatePage(pageKey);

  if (!document.getElementById('lang-switcher')) {
    const switcher = document.createElement('div');
    switcher.id = 'lang-switcher';
    switcher.innerHTML = `
      <span data-i18n="common.language"></span>
      <a href="#" onclick="switchLanguage('zh');return false;" style="margin:0 5px;color:${currentLang==='zh'?'#4CAF50':'#ccc'}">中文</a> |
      <a href="#" onclick="switchLanguage('en');return false;" style="color:${currentLang==='en'?'#2196F3':'#ccc'}">English</a>
    `;
    Object.assign(switcher.style, {
      position: 'fixed',
      top: '10px',
      right: '10px',
      zIndex: '1000',
      background: 'rgba(0,0,0,0.7)',
      color: 'white',
      padding: '4px 8px',
      borderRadius: '4px',
      fontSize: '12px',
      fontFamily: 'Arial,sans-serif'
    });
    document.body.appendChild(switcher);
    translatePage('common');
  }
});
