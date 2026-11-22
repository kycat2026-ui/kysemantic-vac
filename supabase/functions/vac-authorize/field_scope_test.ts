import { decodePointer, selectAuthorizedFields } from "./field_scope.ts";
import { assertEquals } from "https://deno.land/std@0.224.0/assert/mod.ts";

Deno.test("selects only explicitly authorized nested fields", () => {
  assertEquals(
    selectAuthorizedFields({ profile: { name: "A", email: "secret" }, notes: "private" }, ["/profile/name"]),
    { profile: { name: "A" } },
  );
});

Deno.test("supports JSON Pointer escaping", () => {
  assertEquals(decodePointer("/profile/a~1b"), ["profile", "a/b"]);
  assertEquals(decodePointer("/profile/a~0b"), ["profile", "a~b"]);
});

Deno.test("rejects root, malformed escapes, and prototype paths", () => {
  assertEquals(decodePointer("/"), null);
  assertEquals(decodePointer("/a~2b"), null);
  assertEquals(decodePointer("/__proto__/polluted"), null);
});

Deno.test("denies missing fields and invalid resource shapes", () => {
  assertEquals(selectAuthorizedFields({ profile: {} }, ["/profile/email"]), null);
  assertEquals(selectAuthorizedFields(["not", "an", "object"], ["/0"]), null);
});

Deno.test("rejects overlapping paths", () => {
  assertEquals(selectAuthorizedFields({ profile: { name: "A" } }, ["/profile", "/profile/name"]), null);
});

Deno.test("returns array leaf only when the array leaf itself is granted", () => {
  assertEquals(
    selectAuthorizedFields({ tags: ["one", "two"], other: "hidden" }, ["/tags"]),
    { tags: ["one", "two"] },
  );
});
