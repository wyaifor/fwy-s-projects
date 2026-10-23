const state={week:0,mode:'summary',card:0,flipped:false,quizAnswers:{},quizOnlyWrong:false};
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function currentWeek(){return STUDY_DATA.weeks[state.week]}
function lessonNumber(id){return id.replace('w','W').replace('-','.')}

function setup(){
  $('#lessonStat').textContent=STUDY_DATA.stats.lessons;
  $('#quizStat').textContent=STUDY_DATA.stats.quizzes;
  $('#weekNav').innerHTML=STUDY_DATA.weeks.map((w,i)=>`<button data-week="${i}">${w.id.toUpperCase()} · ${esc(w.title.split('·')[0])}<br><small>${w.lessons.length} 节</small></button>`).join('');
  $('#weekNav').addEventListener('click',e=>{const b=e.target.closest('[data-week]');if(!b)return;state.week=+b.dataset.week;state.card=0;state.flipped=false;state.quizOnlyWrong=false;render()});
  document.querySelector('.modes').addEventListener('click',e=>{const b=e.target.closest('[data-mode]');if(!b)return;state.mode=b.dataset.mode;state.card=0;state.flipped=false;render()});
  render();
}

function render(){
  const w=currentWeek();
  $('#weekLabel').textContent=w.id.toUpperCase();$('#weekTitle').textContent=w.title;$('#weekQuestion').textContent=w.question;
  $('#route').innerHTML=w.route.map(x=>`<span>${esc(x)}</span>`).join('');
  document.querySelectorAll('[data-week]').forEach((b,i)=>b.classList.toggle('active',i===state.week));
  document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===state.mode));
  ({summary:renderSummary,notes:renderNotes,map:renderMap,cards:renderCards,quiz:renderQuiz}[state.mode])();
  window.scrollTo({top:0,behavior:'smooth'});
}

function renderSummary(){
  const w=currentWeek();
  $('#content').innerHTML=`<div class="section-title"><div><p class="eyebrow">FIRST PASS</p><h3>这一周必须会什么</h3></div><p>${w.lessons.length} 个考点</p></div><div class="summary-grid">${w.lessons.map(l=>`<article class="summary-card"><div class="lesson-head"><span class="lesson-no">${lessonNumber(l.id)}</span><h4>${esc(l.title)}</h4></div><p>${esc(l.summary)}</p><p class="answer-line">考场结论：${esc(l.decision)}</p><p class="trigger">English trigger: ${esc(l.trigger)}</p></article>`).join('')}</div>`;
}

function renderNotes(){
  const w=currentWeek();
  $('#content').innerHTML=`<div class="section-title"><div><p class="eyebrow">STRUCTURED NOTES</p><h3>完整规则笔记</h3></div><p>定义 → 规则 → 代码 → 陷阱</p></div>${w.lessons.map(l=>`<article class="lesson-card" id="${l.id}"><div class="lesson-head"><span class="lesson-no">${lessonNumber(l.id)}</span><div><h4>${esc(l.title)}</h4><div class="trigger">题干触发词：${esc(l.trigger)}</div></div></div><p class="decision">${esc(l.decision)}</p><ul>${l.facts.map(f=>`<li>${esc(f)}</li>`).join('')}</ul>${l.code?`<pre class="code">${esc(l.code)}</pre>`:''}<div class="trap"><b>容易错：</b>${esc(l.trap)}</div><a class="full-link" href="index.html#${l.id}">打开本节完整图文讲解 →</a></article>`).join('')}`;
}

function renderMap(){
  const w=currentWeek();
  const groups=[[],[],[],[]];w.lessons.forEach((l,i)=>groups[Math.min(3,Math.floor(i*4/w.lessons.length))].push(l));
  $('#content').innerHTML=`<div class="section-title"><div><p class="eyebrow">CONCEPT MAP</p><h3>先看关系，再记细节</h3></div></div><div class="map-shell"><div class="mindmap"><div class="map-root">${w.id.toUpperCase()}<br>${esc(w.question)}</div><div class="map-branches">${groups.map((g,i)=>`<div class="map-branch"><b>${esc(w.route[i])}</b><div class="map-leaves">${g.map(l=>`<span title="${esc(l.decision)}">${esc(l.title)}</span>`).join('')}</div></div>`).join('')}</div></div></div>`;
}

function renderCards(){
  const cards=currentWeek().lessons;const l=cards[state.card];
  const inside=state.flipped?`<div><p class="hint">ANSWER · 点击翻回问题</p><h3>${esc(l.decision)}</h3><p>${esc(l.facts.join('；'))}</p><div class="trap"><b>陷阱：</b>${esc(l.trap)}</div></div>`:`<div><p class="hint">QUESTION · 先在脑中回答，再点击翻面</p><h3>${lessonNumber(l.id)} ${esc(l.title)}</h3><p>看到这些英文时，你应该想到什么？</p><p><b>${esc(l.trigger)}</b></p></div>`;
  $('#content').innerHTML=`<div class="section-title"><div><p class="eyebrow">ACTIVE RECALL</p><h3>闪卡主动回忆</h3></div><p>不会的卡不要只看，要说出答案</p></div><div class="flashcard-shell"><p class="card-progress">${state.card+1} / ${cards.length}</p><button class="flashcard" id="flashcard">${inside}</button><div class="card-actions"><button id="prevCard">← 上一张</button><button id="shuffleCard">随机一张</button><button id="nextCard">下一张 →</button></div></div>`;
  $('#flashcard').onclick=()=>{state.flipped=!state.flipped;renderCards()};
  $('#prevCard').onclick=()=>{state.card=(state.card-1+cards.length)%cards.length;state.flipped=false;renderCards()};
  $('#nextCard').onclick=()=>{state.card=(state.card+1)%cards.length;state.flipped=false;renderCards()};
  $('#shuffleCard').onclick=()=>{state.card=Math.floor(Math.random()*cards.length);state.flipped=false;renderCards()};
}

function renderQuiz(){
  const allItems=currentWeek().lessons.flatMap(l=>l.quizzes.map((q,i)=>({...q,key:`${l.id}-${i}`,lesson:l.title,id:l.id})));
  const items=state.quizOnlyWrong?allItems.filter(q=>state.quizAnswers[q.key]==='wrong'):allItems;
  const answered=allItems.filter(q=>state.quizAnswers[q.key]).length;const correct=allItems.filter(q=>state.quizAnswers[q.key]==='correct').length;
  const body=items.length?items.map((q,qi)=>`<article class="quiz-card"><p class="trigger">${lessonNumber(q.id)} · ${esc(q.lesson)}</p><h3>${qi+1}. ${esc(q.question)}</h3>${q.choices.map((c,ci)=>`<button class="quiz-option" data-key="${q.key}" data-choice="${ci}">${esc(c.text)}</button>`).join('')}<div class="quiz-explain" id="ex-${q.key}"><b>答案解析：</b>${esc(q.explanation)}</div></article>`).join(''):`<article class="quiz-card"><h3>目前没有错题</h3><p>完成本周测验后，答错的题会自动进入这里。</p></article>`;
  $('#content').innerHTML=`<div class="section-title"><div><p class="eyebrow">EXAM CHECK</p><h3>${state.quizOnlyWrong?'本周错题重练':'本周全部自测'}</h3></div><p>先作答，再看解析</p></div><div class="scorebox"><span>已答 ${answered}/${allItems.length}</span><b>正确 ${correct}</b></div>${body}<div class="quiz-actions"><button id="wrongQuiz">${state.quizOnlyWrong?'返回全部题目':'只练错题'}</button><button id="resetQuiz">清空本周答案</button></div>`;
  document.querySelectorAll('.quiz-option').forEach(b=>b.onclick=()=>answerQuiz(allItems,b));
  $('#wrongQuiz').onclick=()=>{state.quizOnlyWrong=!state.quizOnlyWrong;renderQuiz()};
  $('#resetQuiz').onclick=()=>{allItems.forEach(q=>delete state.quizAnswers[q.key]);state.quizOnlyWrong=false;renderQuiz()};
}

function answerQuiz(items,button){
  const q=items.find(x=>x.key===button.dataset.key);const chosen=q.choices[+button.dataset.choice];
  document.querySelectorAll(`[data-key="${q.key}"]`).forEach((b,i)=>{b.disabled=true;if(q.choices[i].correct)b.classList.add('correct');else if(b===button)b.classList.add('wrong')});
  $(`#ex-${q.key}`).classList.add('show');state.quizAnswers[q.key]=chosen.correct?'correct':'wrong';
  const all=currentWeek().lessons.flatMap(l=>l.quizzes.map((q,i)=>`${l.id}-${i}`));
  const answered=all.filter(k=>state.quizAnswers[k]).length,correct=all.filter(k=>state.quizAnswers[k]==='correct').length;
  document.querySelector('.scorebox').innerHTML=`<span>已答 ${answered}/${all.length}</span><b>正确 ${correct}</b>`;
}

setup();
