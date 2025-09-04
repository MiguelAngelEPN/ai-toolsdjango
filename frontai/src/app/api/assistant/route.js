export async function POST(req) {
  try {
    const body = await req.json();
    const url = `${process.env.BACKEND_URL}/api/assistant/`;

    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const data = await res.json();
    return new Response(JSON.stringify(data), {
      status: res.status,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: err?.message || 'Proxy error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
