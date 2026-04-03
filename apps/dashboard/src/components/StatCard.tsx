type StatCardProps = {
  label: string;
  value: string | number;
  tone?: "default" | "accent";
};

export function StatCard({ label, value, tone = "default" }: StatCardProps) {
  return (
    <article className={`stat-card ${tone === "accent" ? "is-accent" : ""}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </article>
  );
}
