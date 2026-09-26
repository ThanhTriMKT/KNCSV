import { apiClient } from "./client";

export type JobType = "full_time" | "part_time" | "internship";
export type JobPostStatus = "PENDING" | "APPROVED" | "REJECTED" | "CLOSED";

export interface JobPostCreate {
  title: string;
  job_type: JobType;
  description: string;
  requirements?: string;
  benefits?: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
  deadline?: string;
  company_id?: string;
  company_name?: string;
}

export interface JobPostRead {
  id: string;
  title: string;
  job_type: JobType;
  description: string;
  requirements?: string | null;
  benefits?: string | null;
  location?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  deadline?: string | null;
  status: JobPostStatus;
  rejection_note?: string | null;
  created_by_id?: string | null;
  company_id?: string | null;
  company_name?: string | null;
  created_at: string;
  updated_at: string;
  application_count: number;
}

export interface JobPostListResult {
  items: JobPostRead[];
  total: number;
  limit: number;
  offset: number;
}

export interface JobApplicationRead {
  id: string;
  job_post_id: string;
  applicant_id: string;
  cover_letter?: string | null;
  cv_url?: string | null;
  status: string;
  note?: string | null;
  created_at: string;
  applicant_name?: string | null;
  applicant_email?: string | null;
}

export interface JobApplicationListResult {
  items: JobApplicationRead[];
  total: number;
}

export async function listJobs(params: {
  search?: string;
  job_type?: string;
  status?: string;
  limit?: number;
  offset?: number;
} = {}): Promise<JobPostListResult> {
  const searchParams: Record<string, string> = {};
  if (params.search) searchParams.search = params.search;
  if (params.job_type) searchParams.job_type = params.job_type;
  if (params.status) searchParams.status = params.status;
  if (params.limit !== undefined) searchParams.limit = String(params.limit);
  if (params.offset !== undefined) searchParams.offset = String(params.offset);

  return apiClient.get("jobs", { searchParams }).json<JobPostListResult>();
}

export async function getJobDetail(id: string): Promise<JobPostRead> {
  return apiClient.get(`jobs/${id}`).json<JobPostRead>();
}

export async function createJob(data: JobPostCreate): Promise<JobPostRead> {
  return apiClient.post("jobs", { json: data }).json<JobPostRead>();
}

export async function updateJob(id: string, data: Partial<JobPostCreate>): Promise<JobPostRead> {
  return apiClient.put(`jobs/${id}`, { json: data }).json<JobPostRead>();
}

export async function deleteJob(id: string): Promise<{ ok: boolean }> {
  return apiClient.delete(`jobs/${id}`).json<{ ok: boolean }>();
}

export async function approveJob(id: string, data: { status: "APPROVED" | "REJECTED"; rejection_note?: string }): Promise<JobPostRead> {
  return apiClient.post(`jobs/${id}/approve`, { json: data }).json<JobPostRead>();
}

export async function applyJob(jobId: string, data: { cover_letter?: string; cv_url?: string }): Promise<JobApplicationRead> {
  return apiClient.post(`jobs/${jobId}/apply`, { json: data }).json<JobApplicationRead>();
}

export async function getMyApplications(): Promise<JobApplicationListResult> {
  return apiClient.get("jobs/applications/me").json<JobApplicationListResult>();
}

export async function getJobApplications(jobId: string): Promise<JobApplicationListResult> {
  return apiClient.get(`jobs/${jobId}/applications`).json<JobApplicationListResult>();
}
