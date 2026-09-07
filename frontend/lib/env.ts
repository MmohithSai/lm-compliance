function need(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`${name} is not set. Copy .env.example to frontend/.env.local and fill it in.`);
  return v;
}

export const env = {
  get url() {
    return need("NEXT_PUBLIC_SUPABASE_URL");
  },
  get anonKey() {
    return need("NEXT_PUBLIC_SUPABASE_ANON_KEY");
  },
};
