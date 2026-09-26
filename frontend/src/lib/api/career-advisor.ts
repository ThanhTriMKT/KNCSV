/**
 * Career Advisor API client — Trợ lý Hướng nghiệp DLU
 */

import { apiClient } from "./client";

export interface CareerTrack {
  id: string;
  name: string;
  icon: string;
  description: string;
  skills: {
    core: string[];
    specialized: string[];
    soft: string[];
  };
  roadmap: {
    year: string;
    focus: string;
    tasks: string[];
  }[];
  target_companies: string[];
  salary_range: Record<string, string>;
}

export interface InterviewCategory {
  category: string;
  icon: string;
  questions: {
    q: string;
    tip: string;
  }[];
}

export interface CVTemplate {
  id: string;
  name: string;
  target: string;
  sections: string[];
  tips: string[];
}

export interface CareerStats {
  total_alumni: number;
  total_companies: number;
  total_jobs: number;
  top_companies: { name: string; alumni_count: number }[];
  top_skills: string[];
}

export async function fetchCareerTracks(): Promise<CareerTrack[]> {
  return apiClient.get("career-advisor/tracks").json();
}

export async function fetchCareerTrack(id: string): Promise<CareerTrack> {
  return apiClient.get(`career-advisor/tracks/${id}`).json();
}

export async function fetchInterviewBank(
  category?: string,
): Promise<InterviewCategory[]> {
  const searchParams: Record<string, string> = {};
  if (category) searchParams.category = category;
  return apiClient.get("career-advisor/interview-bank", { searchParams }).json();
}

export async function fetchCVTemplates(): Promise<CVTemplate[]> {
  return apiClient.get("career-advisor/cv-templates").json();
}

export async function fetchCareerStats(): Promise<CareerStats> {
  return apiClient.get("career-advisor/stats").json();
}
