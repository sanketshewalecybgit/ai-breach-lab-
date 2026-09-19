'use strict';
const csrf = document.querySelector('meta[name="csrf-token"]').content;
const element = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
};
const jsonPost = async (url, body) => {
  const response = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf}, body: JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok && !data.trace) throw new Error(data.error || 'The request could not be completed.');
  return data;
};
document.querySelectorAll('.reveal-hint').forEach(button => button.addEventListener('click', async () => {
  const box = button.closest('.hint-box');
  button.disabled = true;
  try {
    const data = await jsonPost(`/api/hints/${box.dataset.challenge}`, {});
    box.querySelector('.hint-list').replaceChildren(...data.hints.map(hint => element('li', hint)));
    box.querySelector('.hint-usage').textContent = `${data.hints_used} / 3 hints used · No score penalty`;
    button.textContent = data.hints_used === 3 ? 'All hints revealed' : `SHOW HINT ${data.hints_used + 1}`;
    button.disabled = data.hints_used === 3;
    box.querySelector('.hint-error').textContent = '';
  } catch (error) {
    box.querySelector('.hint-error').textContent = error.message;
    button.disabled = false;
  }
}));
const chatForm = document.getElementById('chat-form');
if (chatForm) {
  const input = document.getElementById('message');
  const conversation = document.getElementById('conversation');
  const ticket = new URLSearchParams(window.location.search).get('ticket');
  if (ticket && /^\d+$/.test(ticket)) input.value = `Summarize ticket ${ticket}.`;
  document.querySelectorAll('.prompt-starter').forEach(button => button.addEventListener('click', () => {
    input.value = button.dataset.prompt;
    input.focus();
  }));
  input.addEventListener('keydown', event => {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {event.preventDefault(); chatForm.requestSubmit();}
  });
  let busy = false;
  chatForm.addEventListener('submit', async event => {
    event.preventDefault();
    if (busy || !input.value.trim()) return;
    busy = true;
    const message = input.value.trim();
    const send = document.getElementById('send-button');
    send.disabled = true;
    send.textContent = 'Running local tools…';
    document.getElementById('chat-error').textContent = '';
    const userMessage = element('div', undefined, 'message user');
    userMessage.append(element('strong', 'You'), element('p', message));
    conversation.append(userMessage);
    try {
      const data = await jsonPost('/api/chat', {message});
      input.value = '';
      const answer = element('div', undefined, 'message assistant');
      answer.append(element('strong', 'NovaCart Assistant'), element('pre', data.response, 'response-text'));
      const trace = element('details', undefined, 'trace');
      trace.append(element('summary', 'AI Debug / Tool Trace'));
      const fields = element('dl');
      for (const [label, value] of [['User input', data.user_input], ['Authenticated user', data.authenticated_user], ['Mode', data.mode], ['Model decision (simulator rule)', data.model_decision]]) {
        fields.append(element('dt', label), element('dd', String(value)));
      }
      trace.append(fields);
      data.trace.forEach((call, index) => {
        trace.append(element('h4', `${index + 1}. Selected tool: ${call.tool}`));
        trace.append(element('p', `Source: ${call.source}\nModel decision: ${call.decision}\nAuthorization check: ${call.authorization}`));
        trace.append(element('strong', 'Tool arguments'), element('pre', JSON.stringify(call.arguments, null, 2)));
        trace.append(element('strong', 'Backend result'), element('pre', JSON.stringify(call.result, null, 2)));
        if (call.result.requires_approval) {
          const link = element('a', 'Open human approval panel →', 'btn btn-outline-success mt-2');
          link.href = '/chat';
          answer.append(link);
        }
      });
      if (!data.trace.length) trace.append(element('p', 'No tool executed.'));
      trace.append(element('strong', 'Final AI response'), element('pre', data.response));
      answer.append(trace);
      conversation.append(answer);
      conversation.scrollTop = conversation.scrollHeight;
      document.getElementById('solved-count').textContent = data.solved_count;
      const announcements = document.getElementById('success-announcements');
      data.newly_solved.forEach(solved => {
        const card = element('section', undefined, 'success-card mt-3');
        card.append(element('h2', `✓ ${solved.title}`));
        const evidence = element('dl', undefined, 'evidence-list');
        Object.entries(solved.evidence).forEach(([label, value]) => evidence.append(element('dt', label), element('dd', String(value))));
        card.append(evidence);
        const link = element('a', 'Review root cause and remediation →');
        link.href = `/lab/${solved.id}`;
        card.append(link);
        announcements.prepend(card);
      });
      if (data.solved_count === 7 && !document.getElementById('lab-complete')) {
        const complete = element('a', 'LAB SOLVED — View your results →', 'btn btn-success btn-lg mt-3');
        complete.id = 'lab-complete'; complete.href = '/solved'; announcements.prepend(complete);
      }
    } catch (error) {
      document.getElementById('chat-error').textContent = error.message;
    } finally {
      busy = false; send.disabled = false; send.textContent = 'Send message →'; input.focus();
    }
  });
}
