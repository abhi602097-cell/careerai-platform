// src/services/api.js
// ─────────────────────────────────────────────────────────────
// Central API service — all backend calls go through here.
// Base URL points to Flask backend on port 5000.
// ─────────────────────────────────────────────────────────────

const BASE_URL = import.meta?.env?.VITE_API_URL || "http://localhost:5000/api/v1";

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body) opts.body = JSON.stringify(body);
  const res  = await fetch(`${BASE_URL}${path}`, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "API error");
  return data.data;
}

export const api = {
  health:              ()          => request("GET",  "/health"),
  predict:             (student)   => request("POST", "/predict", student),
  getCareers:          ()          => request("GET",  "/careers"),
  getCareer:           (name)      => request("GET",  `/careers/${encodeURIComponent(name)}`),
  compareCareers:      (names)     => request("POST", "/careers/compare", { careers: names }),
  getCareerRoadmap:    (name)      => request("GET",  `/careers/${encodeURIComponent(name)}/roadmap`),
  getScholarships:     (filters)   => request("GET",  `/scholarships?${new URLSearchParams(filters)}`),
  getScholarship:      (id)        => request("GET",  `/scholarships/${id}`),
  getResources:        (career, t) => request("GET",  `/resources/${encodeURIComponent(career)}${t ? `?type=${t}` : ""}`),
  getResourcesBySkill: (skill)     => request("GET",  `/resources/skill/${encodeURIComponent(skill)}`),
  getGlobalXAI:        ()          => request("GET",  "/xai/global"),
};
