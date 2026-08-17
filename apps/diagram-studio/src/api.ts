const API = "/api/diagram";

export async function transcribeAudio(blob: Blob): Promise<string> {
  const form = new FormData();
  form.append("file", blob, "voice.webm");
  const res = await fetch(`${API}/transcribe`, { method: "POST", body: form });
  const json = await res.json();
  return json.data.text;
}

export async function generateDiagram(prompt: string, existingElements?: any[], history?: any[]) {
  const res = await fetch(`${API}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt,
      existing_elements: existingElements ?? null,
      history: history ?? null,
    }),
  });
  const json = await res.json();
  return json.data;
}

export async function voiceDiagram(
  blob: Blob,
  existingElements?: any[],
  history?: any[]
): Promise<{ scene: { elements: any[] }; explanation: string; prompt?: string }> {
  const form = new FormData();
  form.append("file", blob, "voice.webm");
  if (existingElements) {
    form.append("existing_elements", JSON.stringify(existingElements));
  }
  if (history) {
    form.append("history", JSON.stringify(history));
  }
  const res = await fetch(`${API}/voice-diagram`, { method: "POST", body: form });
  const json = await res.json();
  return json.data;
}

