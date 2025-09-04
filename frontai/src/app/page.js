'use client';

import { useState } from 'react';

export default function Page() {
  const BACKEND = process.env.DJANGO_BASE_URL

  function parseToolCallFromAnswer(answer) {
    if (!answer) return { cleaned: '', toolCall: null };
    const match = answer.match(/<tool_call>\s*([\s\S]*?)\s*<\/tool_call>/i);
    if (!match) return { cleaned: answer, toolCall: null };
    let toolCall = null;
    try { toolCall = JSON.parse(match[1]); } catch (_) { toolCall = null; }
    const cleaned = answer.replace(match[0], '').trim();
    return { cleaned, toolCall };
  }

  // ---estados
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  // --- funciones
  async function send() {
    const t = text.trim();
    if (!t) return;
    setErr(null);
    setText('');
    setMessages(prev => [...prev, { role: 'user', content: t }]);
    setLoading(true);

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/assistant/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: t }),
      });
      const data = await res.json();

      if (!res.ok) {
        setErr(data?.error || 'Error del asistente');
      } else {
        const { cleaned, toolCall } = parseToolCallFromAnswer(data.answer || '');
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: cleaned || data.answer || '',
            toolResults: data.tool_results || [],
            toolCall: toolCall || null,
          },
        ]);
      }
    } catch (e) {
      setErr(e?.message || 'Fallo de red');
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }
  
  return (
    <main style={{ maxWidth: 900, margin: '40px auto', padding: '0 16px', fontFamily: 'system-ui, sans-serif' }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
        Asistente — Django (tools)
      </h1>
      <p style={{ color: '#666', marginBottom: 16 }}>
        Ejemplo: <i>“Consulta el saldo del cliente 1 y registra un pago de 50”.</i>
      </p>

      <div style={{ border: '1px solid #e5e7eb', borderRadius: 12, padding: 12, minHeight: 220, background: '#fff' }}>
        {messages.length === 0 && (
          <div style={{ color: '#9ca3af' }}>No hay mensajes aún. Envía tu primera solicitud.</div>
        )}

        {messages.map((m, i) => (
          <div key={i} style={{ margin: '10px 0' }}>
            <div
              style={{
                display: 'inline-block',
                padding: '10px 12px',
                borderRadius: 12,
                background: m.role === 'user' ? '#2563eb' : '#f3f4f6',
                color: m.role === 'user' ? '#fff' : '#000',
                whiteSpace: 'pre-wrap',
                maxWidth: 700,
              }}
            >
              <b>{m.role === 'user' ? 'Tú: ' : 'Asistente: '}</b>
              {m.content}
            </div>

            {m.role === 'assistant' && m.toolCall && (
              <div style={{ fontSize: 12, color: '#666', marginTop: 6 }}>
                <b>Acción detectada:</b> {m.toolCall.name}{' '}
                {m.toolCall.arguments ? `→ ${JSON.stringify(m.toolCall.arguments)}` : null}
              </div>
            )}

            {m.role === 'assistant' && m.toolResults && m.toolResults.length > 0 && (
              <div style={{ marginTop: 6 }}>
                <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>Resultados de herramientas:</div>
                {m.toolResults.map((tr, idx) => (
                  <div
                    key={idx}
                    style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 10, background: '#fafafa', marginTop: 4 }}
                  >
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{JSON.stringify(tr, null, 2)}</pre>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <input
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Escribe tu solicitud…"
          style={{
            flex: 1,
            padding: '10px 12px',
            border: '1px solid #e5e7eb',
            borderRadius: 10,
            outline: 'none',
          }}
        />
        <button
          onClick={send}
          disabled={loading}
          style={{
            padding: '10px 14px',
            borderRadius: 10,
            background: loading ? '#93c5fd' : '#2563eb',
            color: '#fff',
            border: 'none',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Enviando…' : 'Enviar'}
        </button>
      </div>

      {err && <div style={{ marginTop: 10, color: '#b91c1c' }}>{err}</div>}
    </main>
  );
}
