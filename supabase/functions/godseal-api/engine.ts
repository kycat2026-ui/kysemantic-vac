// GodSeal Sigil Engine — 純邏輯，不依賴任何執行環境（Deno / Node 都可測試）

export type VerificationStatus = "verified" | "pending" | "experimental";

export interface Sigil {
  id: number;
  name: string;
  chinese_name: string;
  core: string | null;
  attributes: string[];
  grammar_role: string | null;
  canonical_phrase: string | null;
  verification_status: VerificationStatus;
}

export interface AIPlan {
  intent: string;
  selected_sigil_ids: number[];
  incantation: string;
  translation: string;
  narrative: string;
  rationale: string;
}

export interface SequenceResult {
  sigil_ids: number[];
  sigils: Pick<Sigil, "id" | "name" | "chinese_name" | "grammar_role">[];
  status: "verified" | "experimental" | "invalid";
  warnings: string[];
}

/** 尚未從官方資料匯入的佔位符印，不提供給 AI 使用 */
export function isPlaceholder(s: Sigil): boolean {
  return s.name.startsWith("待匯入");
}

export function usableSigils(all: Sigil[]): Sigil[] {
  return all.filter((s) => !isPlaceholder(s));
}

export function buildSystemPrompt(): string {
  return [
    "你是 GodSeal AI 符印操作助手。",
    "只能使用 availableSigils 中提供的符印，用 id 指定，不得創造新符印。",
    "不得自行創造官方語法規則；你提出的組合一律視為實驗性。",
    "依使用者意圖選擇 1 到 6 枚符印並排列順序，同一枚不可重複。",
    "只輸出一個 JSON 物件，不要加 Markdown 或其他文字，格式：",
    '{"intent":"意圖摘要","selected_sigil_ids":[整數...],"incantation":"以符印名組成的神謎文","translation":"中文翻譯","narrative":"效果敘事（100字內）","rationale":"為何選這些符印"}',
  ].join("\n");
}

export function buildUserPrompt(task: string, sigils: Sigil[]): string {
  return JSON.stringify({
    task,
    availableSigils: sigils.map((s) => ({
      id: s.id,
      name: s.name,
      chinese: s.chinese_name,
      core: s.core,
      attributes: s.attributes,
      grammar_role: s.grammar_role,
      canonical_phrase: s.canonical_phrase,
    })),
  });
}

/** 把模型文字解析成 AIPlan；格式不符時拋出錯誤，絕不直接執行模型文字 */
export function parsePlan(text: string): AIPlan {
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start < 0 || end <= start) throw new Error("AI 回傳內容不是 JSON");
  let raw: unknown;
  try {
    raw = JSON.parse(text.slice(start, end + 1));
  } catch {
    throw new Error("AI 回傳的 JSON 無法解析");
  }
  if (typeof raw !== "object" || raw === null) throw new Error("AI 回傳格式錯誤");
  const o = raw as Record<string, unknown>;
  const ids = o.selected_sigil_ids;
  if (!Array.isArray(ids) || !ids.every((n) => Number.isInteger(n))) {
    throw new Error("selected_sigil_ids 必須是整數陣列");
  }
  const str = (k: string) => (typeof o[k] === "string" ? (o[k] as string).slice(0, 2000) : "");
  return {
    intent: str("intent"),
    selected_sigil_ids: ids as number[],
    incantation: str("incantation"),
    translation: str("translation"),
    narrative: str("narrative"),
    rationale: str("rationale"),
  };
}

/**
 * 驗證符印序列。即使每枚符印都已核實，組合語法仍需創作者核准，
 * 因此在 sigil_rules 有 verified 規則之前，最高只會是 experimental。
 */
export function validateSequence(
  ids: number[],
  all: Sigil[],
  verifiedSequences: number[][] = [],
): SequenceResult {
  const byId = new Map(all.map((s) => [s.id, s]));
  const warnings: string[] = [];
  const pick = (s: Sigil) => ({
    id: s.id,
    name: s.name,
    chinese_name: s.chinese_name,
    grammar_role: s.grammar_role,
  });

  if (ids.length === 0) {
    return { sigil_ids: ids, sigils: [], status: "invalid", warnings: ["沒有選擇任何符印"] };
  }
  if (ids.length > 6) {
    return { sigil_ids: ids, sigils: [], status: "invalid", warnings: ["一次最多 6 枚符印"] };
  }
  if (new Set(ids).size !== ids.length) {
    return { sigil_ids: ids, sigils: [], status: "invalid", warnings: ["同一枚符印不可重複"] };
  }
  const unknown = ids.filter((id) => !byId.has(id));
  if (unknown.length) {
    return {
      sigil_ids: ids,
      sigils: [],
      status: "invalid",
      warnings: [`不存在的符印 id：${unknown.join(", ")}`],
    };
  }
  const sigils = ids.map((id) => byId.get(id)!);
  const placeholders = sigils.filter(isPlaceholder);
  if (placeholders.length) {
    return {
      sigil_ids: ids,
      sigils: sigils.map(pick),
      status: "invalid",
      warnings: [`符印 ${placeholders.map((s) => s.id).join(", ")} 尚未匯入官方資料`],
    };
  }

  const unverified = sigils.filter((s) => s.verification_status !== "verified");
  if (unverified.length) {
    warnings.push(`含未核實符印：${unverified.map((s) => s.name).join("、")}`);
  }

  const key = ids.join(",");
  const approved = verifiedSequences.some((seq) => seq.join(",") === key);
  if (approved && unverified.length === 0) {
    return { sigil_ids: ids, sigils: sigils.map(pick), status: "verified", warnings };
  }
  warnings.push("此組合尚未經創作者核准，標記為實驗性");
  return { sigil_ids: ids, sigils: sigils.map(pick), status: "experimental", warnings };
}
