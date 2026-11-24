-- GodSeal AI: owner-scoped creation access
-- Staged only. Review and apply to a non-production database before production.
-- The Edge Function must still authenticate JWTs and derive user_id from auth.getUser(token).
-- Service-role requests bypass RLS, so this migration alone does NOT fix the API.

DROP POLICY IF EXISTS "owner read own private creations" ON public.creations;
CREATE POLICY "owner read own private creations"
  ON public.creations
  FOR SELECT
  TO authenticated
  USING (user_id = (SELECT auth.uid()));

DROP POLICY IF EXISTS "owner insert private creations" ON public.creations;
CREATE POLICY "owner insert private creations"
  ON public.creations
  FOR INSERT
  TO authenticated
  WITH CHECK (
    user_id = (SELECT auth.uid())
    AND visibility = 'private'
  );

-- Keep the existing "public read public creations" policy unchanged.
-- Do not add an UPDATE/DELETE policy until the product exposes owner-only operations.
