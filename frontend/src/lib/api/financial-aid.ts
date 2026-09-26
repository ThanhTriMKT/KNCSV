import { apiClient } from "./client";

export type ContributionStatus = "PLEDGED" | "CONFIRMED";
export type AidApplicationStatus = "PENDING" | "APPROVED" | "REJECTED" | "DISBURSED";

export interface FinancialContributionCreate {
  amount: number;
  message?: string;
  is_anonymous?: boolean;
}

export interface FinancialContributionRead {
  id: string;
  contributor_id: string | null;
  amount: number;
  message: string | null;
  is_anonymous: boolean;
  status: ContributionStatus;
  confirmed_at: string | null;
  created_at: string;
  contributor_name: string | null;
}

export interface ContributionListResult {
  items: FinancialContributionRead[];
  total: number;
  total_amount: number;
}

export interface AidApplicationCreate {
  title: string;
  reason: string;
  amount_requested?: number;
  supporting_documents?: { files?: string[] };
}

export interface AidApplicationReview {
  status: "APPROVED" | "REJECTED" | "DISBURSED";
  amount_approved?: number;
  review_note?: string;
}

export interface AidApplicationRead {
  id: string;
  applicant_id: string;
  title: string;
  reason: string;
  amount_requested: number | null;
  amount_approved: number | null;
  supporting_documents: { files?: string[] } | null;
  status: AidApplicationStatus;
  review_note: string | null;
  disbursed_at: string | null;
  created_at: string;
  updated_at: string;
  applicant_name: string | null;
  applicant_email: string | null;
  applicant_student_id: string | null;
}

export interface AidApplicationListResult {
  items: AidApplicationRead[];
  total: number;
}

export async function listContributions(): Promise<ContributionListResult> {
  return apiClient.get("financial-aid/contributions").json<ContributionListResult>();
}

export async function createContribution(data: FinancialContributionCreate): Promise<FinancialContributionRead> {
  return apiClient.post("financial-aid/contributions", { json: data }).json<FinancialContributionRead>();
}

export async function confirmContribution(id: string): Promise<FinancialContributionRead> {
  return apiClient.put(`financial-aid/contributions/${id}/confirm`).json<FinancialContributionRead>();
}

export async function listAidApplications(params: {
  status?: string;
  limit?: number;
  offset?: number;
} = {}): Promise<AidApplicationListResult> {
  const searchParams: Record<string, string> = {};
  if (params.status) searchParams.status = params.status;
  if (params.limit !== undefined) searchParams.limit = String(params.limit);
  if (params.offset !== undefined) searchParams.offset = String(params.offset);

  return apiClient.get("financial-aid/applications", { searchParams }).json<AidApplicationListResult>();
}

export async function createAidApplication(data: AidApplicationCreate): Promise<AidApplicationRead> {
  return apiClient.post("financial-aid/applications", { json: data }).json<AidApplicationRead>();
}

export async function getMyAidApplications(): Promise<AidApplicationListResult> {
  return apiClient.get("financial-aid/applications/me").json<AidApplicationListResult>();
}

export async function reviewAidApplication(id: string, data: AidApplicationReview): Promise<AidApplicationRead> {
  return apiClient.put(`financial-aid/applications/${id}/review`, { json: data }).json<AidApplicationRead>();
}
