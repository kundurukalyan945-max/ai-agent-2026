"use strict";

const crypto = require("node:crypto");
const { Pool } = require("pg");

const COOKIE_NAME = "career_agent_session";
const SESSION_HOURS = 12;
const HAPPENSTANCE_BASE = "https://api.happenstance.ai/v1";
const SEARCH_COST_CREDITS = 2;
let pool;
let schemaPromise;

const SCHEMA = [
  "CREATE TABLE IF NOT EXISTS candidate_profile (profile_key TEXT PRIMARY KEY, payload_json TEXT NOT NULL, updated_at TEXT NOT NULL)",
  "CREATE TABLE IF NOT EXISTS jobs (job_id TEXT PRIMARY KEY, dedupe_key TEXT NOT NULL UNIQUE, title TEXT NOT NULL, company TEXT NOT NULL, location TEXT NOT NULL DEFAULT '', work_mode TEXT NOT NULL DEFAULT '', url TEXT NOT NULL DEFAULT '', source TEXT NOT NULL DEFAULT 'manual', description TEXT NOT NULL DEFAULT '', date_posted TEXT NOT NULL DEFAULT '', payload_json TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
  "CREATE TABLE IF NOT EXISTS approvals (approval_id TEXT PRIMARY KEY, action_type TEXT NOT NULL, title TEXT NOT NULL, company TEXT NOT NULL DEFAULT '', role TEXT NOT NULL DEFAULT '', payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', reviewer_note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, decided_at TEXT NOT NULL DEFAULT '')",
  "CREATE TABLE IF NOT EXISTS audit_events (event_id TEXT PRIMARY KEY, entity_type TEXT NOT NULL, entity_id TEXT NOT NULL, event_type TEXT NOT NULL, detail_json TEXT NOT NULL, created_at TEXT NOT NULL)",
  "CREATE INDEX IF NOT EXISTS idx_jobs_updated ON jobs(updated_at DESC)",
  "CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status, created_at DESC)",
  "CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_events(created_at DESC)"
];

function now() { return new Date().toISOString(); }
function safeString(value, max = 12000) {
  return String(value == null ? "" : value).trim().slice(0, max);
}
function jsonResponse(res, status, body) {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store, max-age=0");
  res.end(JSON.stringify(body));
}
function getPool() {
  const dsn = process.env.CAREER_DATABASE_URL;
  if (!dsn) {
    const error = new Error("CAREER_DATABASE_URL is not configured in Vercel environment variables.");
    error.statusCode = 503;
    throw error;
  }
  if (!pool) {
    pool = new Pool({
      connectionString: dsn,
      max: 3,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 10000,
      allowExitOnIdle: true
    });
    pool.on("error", () => {});
  }
  return pool;
}
async function ensureSchema() {
  if (!schemaPromise) {
    schemaPromise = (async () => {
      const db = getPool();
      for (const statement of SCHEMA) await db.query(statement);
    })().catch((error) => {
      schemaPromise = null;
      throw error;
    });
  }
  await schemaPromise;
}
function pythonJson(value) {
  if (value === null) return "null";
  if (typeof value === "string" || typeof value === "boolean" || typeof value === "number") return JSON.stringify(value);
  if (Array.isArray(value)) return "[" + value.map(pythonJson).join(", ") + "]";
  if (typeof value === "object") {
    return "{" + Object.keys(value).sort().map((key) => JSON.stringify(key) + ": " + pythonJson(value[key])).join(", ") + "}";
  }
  return "null";
}
function sha256(value) {
  return crypto.createHash("sha256").update(value, "utf8").digest("hex");
}
function parseCookies(req) {
  const raw = req.headers.cookie || "";
  const out = {};
  raw.split(";").forEach((part) => {
    const at = part.indexOf("=");
    if (at > 0) out[part.slice(0, at).trim()] = decodeURIComponent(part.slice(at + 1).trim());
  });
  return out;
}
function sessionSecret() {
  const secret = process.env.APP_ACCESS_PASSWORD || "";
  if (secret.length < 12) {
    const error = new Error("APP_ACCESS_PASSWORD must be configured as a strong passphrase in Vercel environment variables.");
    error.statusCode = 503;
    throw error;
  }
  return secret;
}
function signSession(expiry) {
  const payload = Buffer.from(String(expiry)).toString("base64url");
  const signature = crypto.createHmac("sha256", sessionSecret()).update(payload).digest("base64url");
  return payload + "." + signature;
}
function validSession(req) {
  try {
    const token = parseCookies(req)[COOKIE_NAME] || "";
    const parts = token.split(".");
    if (parts.length !== 2) return false;
    const expected = crypto.createHmac("sha256", sessionSecret()).update(parts[0]).digest();
    const actual = Buffer.from(parts[1], "base64url");
    if (actual.length !== expected.length || !crypto.timingSafeEqual(actual, expected)) return false;
    const expiry = Number(Buffer.from(parts[0], "base64url").toString("utf8"));
    return Number.isFinite(expiry) && expiry > Date.now();
  } catch (_) {
    return false;
  }
}
function setSessionCookie(res, token) {
  const secure = process.env.NODE_ENV === "production" || process.env.VERCEL === "1" ? "; Secure" : "";
  res.setHeader("Set-Cookie", COOKIE_NAME + "=" + encodeURIComponent(token) +
    "; HttpOnly; Path=/; SameSite=Strict; Max-Age=" + (SESSION_HOURS * 3600) + secure);
}
function clearSessionCookie(res) {
  res.setHeader("Set-Cookie", COOKIE_NAME + "=; HttpOnly; Path=/; SameSite=Strict; Max-Age=0; Secure");
}
function readBody(req) {
  if (req.body && typeof req.body === "object") return req.body;
  if (typeof req.body === "string") {
    try { return JSON.parse(req.body); } catch (_) { return {}; }
  }
  return {};
}
async function audit(db, entityType, entityId, eventType, detail = {}) {
  await db.query(
    "INSERT INTO audit_events(event_id, entity_type, entity_id, event_type, detail_json, created_at) VALUES($1,$2,$3,$4,$5,$6)",
    [crypto.randomUUID(), entityType, entityId, eventType, pythonJson(detail), now()]
  );
}
async function getProfile(db) {
  const result = await db.query("SELECT payload_json FROM candidate_profile WHERE profile_key='default'");
  return result.rows[0] ? JSON.parse(result.rows[0].payload_json) : {};
}
async function saveProfile(db, profile) {
  const clean = profile && typeof profile === "object" && !Array.isArray(profile) ? profile : {};
  const serialized = pythonJson(clean);
  await db.query(
    "INSERT INTO candidate_profile(profile_key,payload_json,updated_at) VALUES('default',$1,$2) ON CONFLICT(profile_key) DO UPDATE SET payload_json=EXCLUDED.payload_json,updated_at=EXCLUDED.updated_at",
    [serialized, now()]
  );
  await audit(db, "profile", "default", "profile_saved", { fields: Object.keys(clean).sort() });
}
function normalizeJob(input) {
  const job = {
    title: safeString(input.title, 300) || "Untitled role",
    company: safeString(input.company, 300) || "Unknown company",
    location: safeString(input.location, 300),
    work_mode: safeString(input.work_mode || input.workMode, 100),
    url: safeString(input.url || input.job_url, 2000),
    source: safeString(input.source, 100) || "manual",
    description: safeString(input.description, 12000),
    date_posted: safeString(input.date_posted || input.datePosted, 100),
    status: safeString(input.status, 40) || "saved"
  };
  return job;
}
function jobDedupeKey(job) {
  if (job.url) return "url:" + job.url.toLowerCase().replace(/\/+$/, "");
  return "fields:" + sha256([job.company, job.title, job.location].join("|").toLowerCase());
}
async function upsertJob(db, input) {
  const job = normalizeJob(input);
  const key = jobDedupeKey(job);
  const jobId = crypto.randomUUID();
  const time = now();
  const result = await db.query(
    "INSERT INTO jobs(job_id,dedupe_key,title,company,location,work_mode,url,source,description,date_posted,payload_json,created_at,updated_at) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13) ON CONFLICT(dedupe_key) DO UPDATE SET title=EXCLUDED.title,company=EXCLUDED.company,location=EXCLUDED.location,work_mode=EXCLUDED.work_mode,url=EXCLUDED.url,source=EXCLUDED.source,description=EXCLUDED.description,date_posted=EXCLUDED.date_posted,payload_json=EXCLUDED.payload_json,updated_at=EXCLUDED.updated_at RETURNING job_id",
    [jobId,key,job.title,job.company,job.location,job.work_mode,job.url,job.source,job.description,job.date_posted,pythonJson(job),time,time]
  );
  const returnedId = result.rows[0].job_id;
  await audit(db, "job", returnedId, "job_saved", { source: job.source, status: job.status });
  return returnedId;
}
function detectSkills(text) {
  const aliases = {
    python:["python"], sql:["sql"], pandas:["pandas"], numpy:["numpy"],
    "scikit-learn":["scikit-learn","sklearn"], pytorch:["pytorch","torch"],
    tensorflow:["tensorflow"], fastapi:["fastapi"], flask:["flask"],
    "rest api":["rest api","restful api","api development"], git:["git","github"],
    docker:["docker"], linux:["linux"], llm:["llm","large language model"],
    "generative ai":["generative ai","genai","gen ai"], langchain:["langchain"],
    rag:["rag","retrieval augmented generation"], streamlit:["streamlit"],
    "machine learning":["machine learning","ml engineer","ml/ai"],
    "deep learning":["deep learning"], javascript:["javascript"], react:["react"],
    java:["java"], aws:["aws","amazon web services"], azure:["azure"],
    kubernetes:["kubernetes","k8s"], pytest:["pytest"], opencv:["opencv"],
    matplotlib:["matplotlib"], "computer vision":["computer vision"],
    "jupyter notebook":["jupyter notebook","jupyter"], "prompt engineering":["prompt engineering"]
  };
  const normalized = String(text || "").toLowerCase();
  return new Set(Object.entries(aliases)
    .filter(([, terms]) => terms.some((term) => normalized.includes(term)))
    .map(([skill]) => skill));
}
function scoreJob(job, profile) {
  const description = [job.title, job.description, job.company].join(" ").toLowerCase();
  const candidate = [profile.skills, profile.experience, profile.projects, profile.project, profile.education].join(" ").toLowerCase();
  const candidateSkills = detectSkills(candidate);
  const requiredSkills = detectSkills(description);
  const matched = [...requiredSkills].filter((skill) => candidateSkills.has(skill)).sort();
  const gaps = [...requiredSkills].filter((skill) => !candidateSkills.has(skill)).sort();
  const skillPoints = requiredSkills.size ? 50 * matched.length / requiredSkills.size : 25;
  const targets = Array.isArray(profile.target_roles) ? profile.target_roles :
    (Array.isArray(profile.targetRoles) ? profile.targetRoles : [profile.targetRole || profile.target_roles || "AI/ML Engineer"]);
  const targetLocations = Array.isArray(profile.target_locations) ? profile.target_locations :
    (Array.isArray(profile.targetLocations) ? profile.targetLocations : [profile.targetLocation || "Bengaluru", "Hyderabad"]);
  const words = (value) => new Set(String(value || "").toLowerCase().match(/[a-z0-9]+/g) || []);
  const titleWords = words(job.title);
  let roleFit = 0;
  for (const target of targets.filter(Boolean)) {
    const targetWords = words(target);
    const overlap = [...targetWords].filter((word) => titleWords.has(word)).length / Math.max(1, targetWords.size);
    roleFit = Math.max(roleFit, overlap);
  }
  const location = String(job.location || "").toLowerCase();
  const locationFit = !location || !targetLocations.length ? 7 :
    (targetLocations.some((place) => location.includes(String(place).toLowerCase())) ? 15 : 3);
  const score = Math.round(Math.min(100, skillPoints + 20 * roleFit + locationFit + 10));
  return {
    score,
    matched_skills: matched,
    skill_gaps: gaps,
    reasons: [
      requiredSkills.size ? matched.length + " of " + requiredSkills.size + " detected skills overlap" : "No explicit skills detected in job text",
      locationFit === 15 ? "Target location matches" : "Location match is uncertain or outside target cities",
      roleFit ? "Target-role title overlap: " + Math.round(roleFit * 100) + "%" : "Role title has limited overlap with saved target roles"
    ],
    note: "Heuristic fit indicator only. Verify experience requirements and the employer's official listing."
  };
}
async function listJobs(db, profile) {
  const result = await db.query("SELECT * FROM jobs ORDER BY updated_at DESC LIMIT 300");
  return result.rows.map((row) => {
    const payload = JSON.parse(row.payload_json || "{}");
    return {
      job_id: row.job_id, title: row.title, company: row.company,
      location: row.location, work_mode: row.work_mode, url: row.url,
      source: row.source, description: row.description, date_posted: row.date_posted,
      status: payload.status || "saved", payload, fit: scoreJob(payload, profile)
    };
  });
}
async function updateJobStatus(db, jobId, status) {
  const allowed = new Set(["saved","shortlisted","preparing","applied","interview","rejected","archived"]);
  if (!allowed.has(status)) throw new Error("Unsupported job pipeline status.");
  const result = await db.query("SELECT payload_json FROM jobs WHERE job_id=$1", [jobId]);
  if (!result.rows[0]) return false;
  const payload = JSON.parse(result.rows[0].payload_json || "{}");
  payload.status = status;
  await db.query("UPDATE jobs SET payload_json=$1,updated_at=$2 WHERE job_id=$3", [pythonJson(payload), now(), jobId]);
  await audit(db, "job", jobId, "pipeline_status_changed", { status });
  return true;
}
async function listApprovals(db) {
  const result = await db.query("SELECT * FROM approvals ORDER BY created_at DESC LIMIT 150");
  return result.rows.map((row) => {
    const payload = JSON.parse(row.payload_json || "{}");
    return {
      approval_id: row.approval_id, action_type: row.action_type, title: row.title,
      company: row.company, role: row.role, payload, status: row.status,
      reviewer_note: row.reviewer_note, created_at: row.created_at,
      decided_at: row.decided_at,
      payload_integrity_ok: sha256(pythonJson(payload)) === row.payload_sha256
    };
  });
}
async function createApproval(db, input) {
  const payload = input.payload && typeof input.payload === "object" ? input.payload : {};
  const payloadJson = pythonJson(payload);
  const id = crypto.randomUUID();
  await db.query(
    "INSERT INTO approvals(approval_id,action_type,title,company,role,payload_json,payload_sha256,status,reviewer_note,created_at,decided_at) VALUES($1,$2,$3,$4,$5,$6,$7,'pending','',$8,'')",
    [id, safeString(input.action_type, 80) || "draft", safeString(input.title, 300) || "Untitled draft",
      safeString(input.company, 300), safeString(input.role, 300), payloadJson, sha256(payloadJson), now()]
  );
  await audit(db, "approval", id, "draft_created", { action_type: input.action_type || "draft", payload_sha256: sha256(payloadJson) });
  return id;
}
async function decideApproval(db, id, decision, note) {
  if (!["approved","rejected"].includes(decision)) throw new Error("Decision must be approved or rejected.");
  const client = await db.connect();
  try {
    await client.query("BEGIN");
    const found = await client.query("SELECT * FROM approvals WHERE approval_id=$1 FOR UPDATE", [id]);
    const row = found.rows[0];
    if (!row || row.status !== "pending") {
      await client.query("ROLLBACK");
      return false;
    }
    if (sha256(row.payload_json) !== row.payload_sha256) throw new Error("Draft integrity check failed. Do not approve this item.");
    await client.query("UPDATE approvals SET status=$1,reviewer_note=$2,decided_at=$3 WHERE approval_id=$4 AND status='pending'",
      [decision, safeString(note, 2000), now(), id]);
    await client.query(
      "INSERT INTO audit_events(event_id,entity_type,entity_id,event_type,detail_json,created_at) VALUES($1,'approval',$2,$3,$4,$5)",
      [crypto.randomUUID(), id, decision, pythonJson({ payload_sha256: row.payload_sha256, execution: "not_performed" }), now()]
    );
    await client.query("COMMIT");
    return true;
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
}
async function listAudit(db) {
  const result = await db.query("SELECT * FROM audit_events ORDER BY created_at DESC LIMIT 100");
  return result.rows.map((row) => ({
    event_id: row.event_id, entity_type: row.entity_type, entity_id: row.entity_id,
    event_type: row.event_type, detail: JSON.parse(row.detail_json || "{}"), created_at: row.created_at
  }));
}
async function groq(messages, systemPrompt, maxTokens = 2400) {
  const key = process.env.GROQ_API_KEY;
  if (!key) {
    const error = new Error("GROQ_API_KEY is not configured in Vercel environment variables.");
    error.statusCode = 503;
    throw error;
  }
  const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + key },
    body: JSON.stringify({
      model: process.env.GROQ_MODEL || "llama-3.3-70b-versatile",
      messages: [{ role: "system", content: systemPrompt }, ...messages],
      temperature: 0.35,
      max_tokens: maxTokens
    }),
    signal: AbortSignal.timeout(45000)
  });
  if (!response.ok) {
    const error = new Error(response.status === 429 ? "Groq rate limit reached. Try again later." : "Groq could not generate this draft.");
    error.statusCode = response.status === 429 ? 429 : 502;
    throw error;
  }
  const data = await response.json();
  const text = data && data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content;
  if (!text) throw new Error("Groq returned an empty response.");
  return String(text);
}
async function generatePacket(db, jobId) {
  const jobResult = await db.query("SELECT * FROM jobs WHERE job_id=$1", [jobId]);
  if (!jobResult.rows[0]) throw new Error("Job not found.");
  const job = jobResult.rows[0];
  const profile = await getProfile(db);
  const jobData = JSON.parse(job.payload_json || "{}");
  const fit = scoreJob(jobData, profile);
  const prompt = [
    "Candidate profile:",
    pythonJson(profile),
    "",
    "Job listing:",
    "Title: " + job.title,
    "Company: " + job.company,
    "Location: " + job.location,
    "URL: " + job.url,
    "Description:",
    job.description || "No full description supplied.",
    "",
    "Fit assessment:",
    pythonJson(fit),
    "",
    "Prepare a job-specific pack with these sections:",
    "1. Fit summary and important gaps (do not overstate suitability).",
    "2. Three truthful resume/project bullet rewrites using only evidence in the candidate profile.",
    "3. A concise cover-letter draft with placeholders where required facts are missing.",
    "4. Five likely interview topics and preparation pointers.",
    "5. A short checklist of facts to verify on the employer's official job page.",
    "Never invent employment, skills, metrics, qualifications or relationships."
  ].join("\n");
  const draft = await groq([{ role: "user", content: prompt }], "You are a precise job-application preparation assistant. Use only supplied facts. Clearly mark missing details as placeholders. Do not claim that any application has been submitted.", 2800);
  await audit(db, "job", jobId, "preparation_pack_generated", { fit_score: fit.score });
  return { draft, fit, job: { job_id: job.job_id, title: job.title, company: job.company, url: job.url } };
}
async function happenstanceRequest(path, method = "GET", payload) {
  const key = process.env.HAPPENSTANCE_API_KEY;
  if (!key) {
    const error = new Error("HAPPENSTANCE_API_KEY is not configured in Vercel environment variables.");
    error.statusCode = 503;
    throw error;
  }
  const response = await fetch(HAPPENSTANCE_BASE + path, {
    method,
    headers: { Authorization: "Bearer " + key, "Content-Type": "application/json", Accept: "application/json" },
    body: payload ? JSON.stringify(payload) : undefined,
    signal: AbortSignal.timeout(30000)
  });
  if (!response.ok) {
    const status = response.status;
    const messages = {
      401: "Happenstance rejected the API key. Check the Vercel environment variable.",
      402: "Happenstance reports insufficient credits. Check your account usage.",
      429: "Happenstance has too many searches running. Wait and try again.",
      500: "Happenstance is temporarily unavailable. Retry later.",
      502: "Happenstance is temporarily unavailable. Retry later.",
      503: "Happenstance is temporarily unavailable. Retry later."
    };
    const error = new Error(messages[status] || "Happenstance request failed (" + status + ").");
    error.statusCode = status === 401 || status === 402 || status === 429 ? status : 502;
    throw error;
  }
  return response.json();
}
function flattenPeople(data) {
  const mutuals = Array.isArray(data.mutuals) ? data.mutuals : [];
  const people = Array.isArray(data.results) ? data.results : (Array.isArray(data.people) ? data.people : []);
  return people.map((person) => {
    const social = person && person.socials && typeof person.socials === "object" ? person.socials : {};
    const names = [];
    for (const item of (Array.isArray(person.mutuals) ? person.mutuals : [])) {
      if (item && typeof item.index === "number" && mutuals[item.index] && mutuals[item.index].name) names.push(String(mutuals[item.index].name));
      else if (item && item.name) names.push(String(item.name));
    }
    return {
      name: safeString(person.name, 200) || "Unknown person",
      title: safeString(person.current_title, 300),
      company: safeString(person.current_company, 300),
      summary: safeString(person.summary, 1000),
      linkedin_url: safeString(social.linkedin_url, 1000),
      happenstance_url: safeString(social.happenstance_url, 1000),
      mutuals: names.slice(0, 10)
    };
  }).slice(0, 30);
}
async function draftIntro(db, person) {
  const profile = await getProfile(db);
  const clean = {
    name: safeString(person.name, 200),
    title: safeString(person.title, 300),
    company: safeString(person.company, 300),
    summary: safeString(person.summary, 1000),
    mutuals: Array.isArray(person.mutuals) ? person.mutuals.map((item) => safeString(item, 100)).filter(Boolean).slice(0, 5) : [],
    linkedin_url: safeString(person.linkedin_url, 1000)
  };
  if (!clean.name || !clean.company) throw new Error("The selected person's name and company are required.");
  const prompt = "Draft a short, respectful LinkedIn connection or warm-introduction request for this candidate. Candidate profile: " +
    pythonJson(profile) + "\nPerson found in Happenstance: " + pythonJson(clean) +
    "\nUse only facts supplied. Do not claim a relationship or that the person is hiring. If a mutual connection exists, refer to it cautiously as a possible introduction path. Ask for advice or a brief conversation, not a job. Return one editable draft.";
  const draft = await groq([{ role: "user", content: prompt }], "You write concise, honest professional networking drafts. Never send messages.", 900);
  const approvalId = await createApproval(db, {
    action_type: "network_intro_draft",
    title: "Introduction draft for " + clean.name,
    company: clean.company,
    role: clean.title,
    payload: { recipient: clean, draft, execution: "not_performed" }
  });
  await audit(db, "network_person", clean.name, "intro_draft_created", { approval_id: approvalId });
  return { approval_id: approvalId, draft };
}
async function handleAction(req, res, body) {
  const action = safeString(body.action, 80);
  if (action === "login") {
    const expected = process.env.APP_ACCESS_PASSWORD || "";
    const supplied = String(body.password || "");
    if (expected.length < 12) {
      jsonResponse(res, 503, { error: "APP_ACCESS_PASSWORD is not configured in Vercel environment variables." });
      return;
    }
    const a = Buffer.from(expected);
    const b = Buffer.from(supplied);
    if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) {
      jsonResponse(res, 401, { error: "Incorrect password." });
      return;
    }
    setSessionCookie(res, signSession(Date.now() + SESSION_HOURS * 3600 * 1000));
    jsonResponse(res, 200, { ok: true, expires_in_hours: SESSION_HOURS });
    return;
  }
  if (action === "logout") {
    clearSessionCookie(res);
    jsonResponse(res, 200, { ok: true });
    return;
  }
  if (!validSession(req)) {
    jsonResponse(res, 401, { error: "Unlock the Career Agent to continue." });
    return;
  }
  if (action === "session") {
    jsonResponse(res, 200, { authenticated: true });
    return;
  }
  if (action === "health") {
    jsonResponse(res, 200, {
      database_configured: !!process.env.CAREER_DATABASE_URL,
      groq_configured: !!process.env.GROQ_API_KEY,
      happenstance_configured: !!process.env.HAPPENSTANCE_API_KEY
    });
    return;
  }

  const db = getPool();
  await ensureSchema();

  if (action === "profile.get") {
    jsonResponse(res, 200, { profile: await getProfile(db) });
  } else if (action === "profile.save") {
    await saveProfile(db, body.profile);
    jsonResponse(res, 200, { ok: true });
  } else if (action === "jobs.list") {
    const profile = await getProfile(db);
    jsonResponse(res, 200, { jobs: await listJobs(db, profile) });
  } else if (action === "jobs.add") {
    const id = await upsertJob(db, body.job || {});
    jsonResponse(res, 200, { job_id: id });
  } else if (action === "jobs.import") {
    const incoming = Array.isArray(body.jobs) ? body.jobs.slice(0, 250) : [];
    const ids = [];
    for (const item of incoming) ids.push(await upsertJob(db, item));
    jsonResponse(res, 200, { imported: ids.length, job_ids: ids });
  } else if (action === "jobs.status") {
    const ok = await updateJobStatus(db, safeString(body.job_id, 80), safeString(body.status, 40));
    jsonResponse(res, ok ? 200 : 404, { ok });
  } else if (action === "packet.generate") {
    const packet = await generatePacket(db, safeString(body.job_id, 80));
    const approvalId = await createApproval(db, {
      action_type: "application_pack_review",
      title: "Application preparation pack — " + packet.job.title,
      company: packet.job.company,
      role: packet.job.title,
      payload: { job: packet.job, fit: packet.fit, draft: packet.draft, execution: "not_performed" }
    });
    jsonResponse(res, 200, { ...packet, approval_id: approvalId });
  } else if (action === "approvals.create") {
    const id = await createApproval(db, body);
    jsonResponse(res, 200, { approval_id: id });
  } else if (action === "approvals.list") {
    jsonResponse(res, 200, { approvals: await listApprovals(db) });
  } else if (action === "approvals.decide") {
    const ok = await decideApproval(db, safeString(body.approval_id, 80), safeString(body.decision, 20), safeString(body.reviewer_note, 2000));
    jsonResponse(res, ok ? 200 : 409, { ok });
  } else if (action === "audit.list") {
    jsonResponse(res, 200, { events: await listAudit(db) });
  } else if (action === "happenstance.usage") {
    jsonResponse(res, 200, await happenstanceRequest("/usage"));
  } else if (action === "happenstance.search") {
    if (body.acknowledged !== true) {
      jsonResponse(res, 400, { error: "Confirm that this new search costs 2 Happenstance credits." });
      return;
    }
    const query = safeString(body.text, 1000);
    if (!query) {
      jsonResponse(res, 400, { error: "Enter a people-search query." });
      return;
    }
    const result = await happenstanceRequest("/search", "POST", {
      text: query,
      include_my_connections: body.include_my_connections !== false,
      include_friends_connections: body.include_friends_connections === true
    });
    await audit(db, "happenstance_search", safeString(result.id, 120), "search_started", { credit_cost: SEARCH_COST_CREDITS });
    jsonResponse(res, 200, { search: result, credit_cost: SEARCH_COST_CREDITS });
  } else if (action === "happenstance.results") {
    const searchId = safeString(body.search_id, 120);
    if (!/^[a-zA-Z0-9_-]+$/.test(searchId)) {
      jsonResponse(res, 400, { error: "Invalid Happenstance search ID." });
      return;
    }
    const pageId = safeString(body.page_id, 120);
    const query = pageId ? "?page_id=" + encodeURIComponent(pageId) : "";
    const result = await happenstanceRequest("/search/" + encodeURIComponent(searchId) + query);
    jsonResponse(res, 200, { search: result, people: flattenPeople(result) });
  } else if (action === "happenstance.findMore") {
    const searchId = safeString(body.search_id, 120);
    if (!/^[a-zA-Z0-9_-]+$/.test(searchId)) {
      jsonResponse(res, 400, { error: "Invalid Happenstance search ID." });
      return;
    }
    const result = await happenstanceRequest("/search/" + encodeURIComponent(searchId) + "/find-more", "POST", {});
    jsonResponse(res, 200, { page: result });
  } else if (action === "happenstance.intro") {
    jsonResponse(res, 200, await draftIntro(db, body.person || {}));
  } else {
    jsonResponse(res, 400, { error: "Unknown Career Agent action." });
  }
}

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    jsonResponse(res, 405, { error: "Use POST for this endpoint." });
    return;
  }
  const body = readBody(req);
  try {
    await handleAction(req, res, body);
  } catch (error) {
    const status = Number(error.statusCode) || 500;
    if (status >= 500) console.error("Career Agent API failure:", error && error.name ? error.name : "Error");
    jsonResponse(res, status, {
      error: status === 500 ? "The Career Agent could not complete that request. Check the deployment logs." : safeString(error.message, 500)
    });
  }
};

module.exports.config = { maxDuration: 60 };
