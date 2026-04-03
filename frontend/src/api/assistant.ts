import http from "./http";

export async function listConversations() {
  const { data } = await http.get("/assistant/conversations/");
  return data;
}

export async function createConversation() {
  const { data } = await http.post("/assistant/conversations/");
  return data;
}

export async function getConversation(id: number) {
  const { data } = await http.get(`/assistant/conversations/${id}/`);
  return data;
}

export async function deleteConversation(id: number) {
  const { data } = await http.delete(`/assistant/conversations/${id}/`);
  return data;
}

export async function analyzeFoodImage(file: File) {
  const formData = new FormData();
  formData.append("image", file);
  const { data } = await http.post("/assistant/food-image/analyze/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    timeout: 30000,
  });
  return data;
}

export async function chatSSE(
  conversationId: number,
  message: string,
  onChunk: (text: string) => void,
  onDone: () => void,
  onError: (err: string) => void,
  pageContext: string = "",
) {
  const token = localStorage.getItem("access_token");
  const baseUrl = import.meta.env.VITE_API_BASE_URL || "/api/v1";
  let response: Response;
  try {
    response = await fetch(`${baseUrl}/assistant/conversations/${conversationId}/chat/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message, page_context: pageContext }),
    });
  } catch (e) {
    onError("网络连接失败，请检查网络后重试");
    return;
  }

  if (!response.ok) {
    if (response.status === 429) {
      onError("QUOTA_EXCEEDED");
    } else {
      onError(`请求失败 (${response.status})`);
    }
    return;
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const payload = line.slice(6).trim();
      if (payload === "[DONE]") {
        onDone();
        return;
      }
      try {
        const parsed = JSON.parse(payload);
        if (parsed.content) onChunk(parsed.content);
      } catch {
        // ignore malformed lines
      }
    }
  }
  onDone();
}
