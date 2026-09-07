// Next.js inlines NEXT_PUBLIC_* into the browser bundle only where it is written out in full.
// `process.env[name]` with a computed key is never replaced, so the client would get undefined.
// Keep these references literal.
function need(name: string, value: string | undefined): string {
  if (!value) throw new Error(`${name} is not set. Copy .env.example to frontend/.env.local and fill it in.`);
  return value;
}

export const env = {
  get url() {
    return need("NEXT_PUBLIC_SUPABASE_URL", process.env.NEXT_PUBLIC_SUPABASE_URL);
  },
  get anonKey() {
    return need("NEXT_PUBLIC_SUPABASE_ANON_KEY", process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);
  },
};
