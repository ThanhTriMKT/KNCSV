import { apiClient } from "./client";

export type QuestionType = "text" | "single_choice" | "multiple_choice" | "scale";
export type SurveyStatus = "DRAFT" | "ACTIVE" | "CLOSED";

export interface SurveyQuestionCreate {
  question_text: string;
  question_type: QuestionType;
  options?: { items?: string[] };
  is_required?: boolean;
  order_index?: number;
}

export interface SurveyQuestionRead {
  id: string;
  question_text: string;
  question_type: QuestionType;
  options?: { items?: string[] } | null;
  is_required: boolean;
  order_index: number;
}

export interface SurveyCreate {
  title: string;
  description?: string;
  target_graduation_year?: number;
  start_date?: string;
  end_date?: string;
  questions?: SurveyQuestionCreate[];
}

export interface SurveyRead {
  id: string;
  title: string;
  description?: string | null;
  status: SurveyStatus;
  target_graduation_year?: number | null;
  start_date?: string | null;
  end_date?: string | null;
  created_at: string;
  questions: SurveyQuestionRead[];
  response_count: number;
}

export interface SurveyListResult {
  items: SurveyRead[];
  total: number;
}

export interface SurveyAnswerCreate {
  question_id: string;
  answer_text?: string;
  answer_choices?: { selected?: string[] };
  answer_scale?: number;
}

export interface SurveyStats {
  survey_id: string;
  title: string;
  total_responses: number;
  questions: Array<{
    id: string;
    text: string;
    type: string;
    counts?: Record<string, number>;
    average?: number;
    text_samples?: string[];
  }>;
}

export async function listSurveys(): Promise<SurveyListResult> {
  return apiClient.get("surveys").json<SurveyListResult>();
}

export async function getSurveyDetail(id: string): Promise<SurveyRead> {
  return apiClient.get(`surveys/${id}`).json<SurveyRead>();
}

export async function createSurvey(data: SurveyCreate): Promise<SurveyRead> {
  return apiClient.post("surveys", { json: data }).json<SurveyRead>();
}

export async function updateSurvey(id: string, data: Partial<SurveyCreate> & { status?: SurveyStatus }): Promise<SurveyRead> {
  return apiClient.put(`surveys/${id}`, { json: data }).json<SurveyRead>();
}

export async function deleteSurvey(id: string): Promise<{ ok: boolean }> {
  return apiClient.delete(`surveys/${id}`).json<{ ok: boolean }>();
}

export async function submitSurveyResponse(id: string, answers: SurveyAnswerCreate[]): Promise<{ status: string }> {
  return apiClient.post(`surveys/${id}/respond`, { json: { answers } }).json();
}

export async function getSurveyStats(id: string): Promise<SurveyStats> {
  return apiClient.get(`surveys/${id}/stats`).json<SurveyStats>();
}
