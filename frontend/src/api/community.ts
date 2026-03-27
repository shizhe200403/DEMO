import http from "./http";

export async function listPosts() {
  const { data } = await http.get("/posts/");
  return data;
}

export async function createPost(payload: Record<string, unknown>) {
  const { data } = await http.post("/posts/", payload);
  return data;
}

export async function updatePost(postId: number, payload: Record<string, unknown>) {
  const { data } = await http.put(`/posts/${postId}/`, payload);
  return data;
}

export async function deletePost(postId: number) {
  const { data } = await http.delete(`/posts/${postId}/`);
  return data;
}

export async function createComment(postId: number, payload: Record<string, unknown>) {
  const { data } = await http.post(`/posts/${postId}/comments/`, payload);
  return data;
}

export async function reportPost(postId: number, payload: Record<string, unknown>) {
  const { data } = await http.post(`/posts/${postId}/report/`, payload);
  return data;
}
