const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface Notification {
  id: number;
  user_id: number;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  related_alert_id: number | null;
  created_at: string;
}

function authHeaders(token: string): Record<string, string> {
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

export async function fetchNotifications(
  token: string,
  limit = 20,
  offset = 0,
): Promise<Notification[]> {
  const res = await fetch(
    `${API_BASE}/api/notifications?limit=${limit}&offset=${offset}`,
    { headers: authHeaders(token) },
  );
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<Notification[]>;
}

export async function fetchUnreadCount(token: string): Promise<number> {
  const res = await fetch(`${API_BASE}/api/notifications/unread-count`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  const data = (await res.json()) as { unread_count: number };
  return data.unread_count;
}

export async function markNotificationAsRead(
  token: string,
  id: number,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/notifications/${id}/read`, {
    method: "POST",
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const err = (await res.json()) as { detail?: string };
    throw new Error(err.detail ?? `Failed to mark as read (${res.status})`);
  }
}

export async function markAllNotificationsAsRead(
  token: string,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/notifications/read-all`, {
    method: "POST",
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const err = (await res.json()) as { detail?: string };
    throw new Error(
      err.detail ?? `Failed to mark all as read (${res.status})`,
    );
  }
}
