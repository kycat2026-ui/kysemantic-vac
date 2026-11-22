export function decodePointer(scope: string): string[] | null {
  if (!scope.startsWith("/") || scope === "/" || scope.length > 512) return null;
  const parts = scope.slice(1).split("/");
  const decoded: string[] = [];
  for (const part of parts) {
    if (/~(?![01])/.test(part)) return null;
    decoded.push(part.replace(/~1/g, "/").replace(/~0/g, "~"));
  }
  if (decoded.some((p) => p.length === 0 || p === "__proto__" || p === "prototype" || p === "constructor")) return null;
  return decoded;
}

export function selectAuthorizedFields(content: unknown, scopes: string[]): Record<string, unknown> | null {
  if (!content || typeof content !== "object" || Array.isArray(content)) return null;
  const paths = scopes.map(decodePointer);
  if (paths.some((p) => p === null)) return null;
  // Overlapping scopes are rejected to avoid ambiguous output merging.
  for (let i = 0; i < paths.length; i++) {
    for (let j = i + 1; j < paths.length; j++) {
      const a = paths[i]!, b = paths[j]!;
      const min = Math.min(a.length, b.length);
      if (a.slice(0, min).every((part, k) => part === b[k])) return null;
    }
  }
  const output: Record<string, unknown> = {};
  for (const path of paths as string[][]) {
    let source: any = content;
    let target: any = output;
    for (let i = 0; i < path.length; i++) {
      const key = path[i];
      if (!source || typeof source !== "object" || Array.isArray(source) ||
          !Object.prototype.hasOwnProperty.call(source, key)) return null;
      if (i === path.length - 1) {
        target[key] = source[key];
      } else {
        if (source[key] === null || typeof source[key] !== "object" || Array.isArray(source[key])) return null;
        if (!target[key]) target[key] = {};
        source = source[key];
        target = target[key];
      }
    }
  }
  return output;
}
