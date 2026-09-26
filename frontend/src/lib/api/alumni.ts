import { apiClient } from "./client";

export interface CompanyRead {
  id: string;
  name: string;
  industry: string | null;
  website: string | null;
  address: string | null;
  description: string | null;
  created_at: string;
}

export interface AlumniProfileRead {
  id: string;
  user_id: string | null;
  company_id: string | null;
  student_id: string;
  full_name: string;
  email: string;
  phone: string | null;
  graduation_year: number | null;
  major: string | null;
  gpa: number | null;
  current_job_title: string | null;
  company_name: string | null;
  work_location: string | null;
  job_field: string | null;
  bio: string | null;
  linkedin_url: string | null;
  skills: { items?: string[] } | null;
  achievements: string | null;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface ListAlumniParams {
  search?: string;
  query?: string;
  major?: string;
  graduation_year?: number;
  company?: string;
  is_verified?: boolean;
  limit?: number;
  offset?: number;
}

export type AlumniDirectoryCard = AlumniProfileRead & {
  anonymized_name?: string;
  current_job?: string;
  skills?: any;
  courses_taken?: string[];
};

export interface AlumniListResult {
  items: AlumniProfileRead[];
  total: number;
  limit: number;
  offset: number;
}

export interface ImportPreviewRecord {
  action: "create" | "update";
  student_id: string;
  full_name: string;
  email: string;
  graduation_year?: number;
  major?: string;
  phone?: string;
  current_job_title?: string;
  company_name?: string;
}

export interface ImportPreviewResult {
  session_id: string;
  filename: string;
  total_records: number;
  new_count: number;
  update_count: number;
  preview: ImportPreviewRecord[];
}

export async function listAlumni(params: ListAlumniParams = {}): Promise<AlumniListResult> {
  const searchParams: Record<string, string> = {};
  const s = params.search || params.query;
  if (s) searchParams.search = s;
  if (params.major) searchParams.major = params.major;
  if (params.graduation_year) searchParams.graduation_year = String(params.graduation_year);
  if (params.company) searchParams.company = params.company;
  if (params.is_verified !== undefined) searchParams.is_verified = String(params.is_verified);
  if (params.limit !== undefined) searchParams.limit = String(params.limit);
  if (params.offset !== undefined) searchParams.offset = String(params.offset);

  return apiClient.get("alumni", { searchParams }).json<AlumniListResult>();
}

export async function getAlumniDetail(id: string): Promise<AlumniProfileRead> {
  return apiClient.get(`alumni/${id}`).json<AlumniProfileRead>();
}

export async function getMyAlumniProfile(): Promise<AlumniProfileRead | null> {
  return apiClient.get("alumni/me/profile").json<AlumniProfileRead>().catch(() => null);
}

export async function updateMyAlumniProfile(data: Partial<AlumniProfileRead>): Promise<AlumniProfileRead> {
  return apiClient.put("alumni/me/profile", { json: data }).json<AlumniProfileRead>();
}

export async function updateAlumniProfileAdmin(id: string, data: Partial<AlumniProfileRead>): Promise<AlumniProfileRead> {
  return apiClient.put(`alumni/${id}`, { json: data }).json<AlumniProfileRead>();
}

export async function uploadAlumniImport(file: File): Promise<ImportPreviewResult> {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient.post("alumni/import/preview", { body: formData }).json<ImportPreviewResult>();
}

export async function confirmAlumniImport(sessionId: string): Promise<{ status: string; new_count: number; update_count: number }> {
  return apiClient.post("alumni/import/confirm", { json: { session_id: sessionId } }).json();
}

export async function listCompanies(): Promise<CompanyRead[]> {
  return apiClient.get("alumni/companies/list").json<CompanyRead[]>();
}
