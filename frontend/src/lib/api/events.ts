import { apiClient } from "./client";

export type EventType = "anniversary" | "talkshow" | "workshop" | "seminar" | "other";
export type RegistrationType = "attendee" | "speaker";
export type RegistrationStatus = "REGISTERED" | "ATTENDED" | "CANCELLED";

export interface EventCreate {
  title: string;
  event_type: EventType;
  description?: string;
  location?: string;
  is_online?: boolean;
  online_link?: string;
  start_time: string;
  end_time?: string;
  max_attendees?: number;
  max_speakers?: number;
  banner_url?: string;
  agenda?: string;
}

export interface EventRead {
  id: string;
  title: string;
  event_type: EventType;
  description?: string | null;
  location?: string | null;
  is_online: boolean;
  online_link?: string | null;
  start_time: string;
  end_time?: string | null;
  max_attendees?: number | null;
  max_speakers?: number | null;
  is_published: boolean;
  banner_url?: string | null;
  agenda?: string | null;
  created_at: string;
  attendee_count: number;
  speaker_count: number;
}

export interface EventListResult {
  items: EventRead[];
  total: number;
  limit: number;
  offset: number;
}

export interface EventRegistrationRead {
  id: string;
  event_id: string;
  user_id: string;
  registration_type: RegistrationType;
  status: RegistrationStatus;
  speaker_topic?: string | null;
  speaker_bio?: string | null;
  registered_at: string;
  user_name?: string | null;
  user_email?: string | null;
  user_role?: string | null;
}

export async function listEvents(params: {
  event_type?: string;
  upcoming?: boolean;
  limit?: number;
  offset?: number;
} = {}): Promise<EventListResult> {
  const searchParams: Record<string, string> = {};
  if (params.event_type) searchParams.event_type = params.event_type;
  if (params.upcoming !== undefined) searchParams.upcoming = String(params.upcoming);
  if (params.limit !== undefined) searchParams.limit = String(params.limit);
  if (params.offset !== undefined) searchParams.offset = String(params.offset);

  return apiClient.get("events", { searchParams }).json<EventListResult>();
}

export async function getEventDetail(id: string): Promise<EventRead> {
  return apiClient.get(`events/${id}`).json<EventRead>();
}

export async function createEvent(data: EventCreate): Promise<EventRead> {
  return apiClient.post("events", { json: data }).json<EventRead>();
}

export async function updateEvent(id: string, data: Partial<EventCreate> & { is_published?: boolean }): Promise<EventRead> {
  return apiClient.put(`events/${id}`, { json: data }).json<EventRead>();
}

export async function deleteEvent(id: string): Promise<{ ok: boolean }> {
  return apiClient.delete(`events/${id}`).json<{ ok: boolean }>();
}

export async function registerEvent(
  id: string,
  data: { registration_type?: RegistrationType; speaker_topic?: string; speaker_bio?: string } = {}
): Promise<EventRegistrationRead> {
  return apiClient.post(`events/${id}/register`, { json: data }).json<EventRegistrationRead>();
}

export async function cancelEventRegistration(id: string): Promise<{ ok: boolean }> {
  return apiClient.delete(`events/${id}/register`).json<{ ok: boolean }>();
}

export async function getEventRegistrations(id: string): Promise<EventRegistrationRead[]> {
  return apiClient.get(`events/${id}/registrations`).json<EventRegistrationRead[]>();
}

export async function updateAttendance(
  eventId: string,
  regId: string,
  status: "ATTENDED" | "CANCELLED"
): Promise<EventRegistrationRead> {
  return apiClient.put(`events/${eventId}/registrations/${regId}/attendance`, { json: { status } }).json<EventRegistrationRead>();
}
