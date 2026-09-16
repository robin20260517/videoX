import type { ReactNode } from "react";
export function Field({ children }: { children: ReactNode }) {
  return <div className="field">{children}</div>;
}
export function SectionTitle({
  number,
  title,
  detail,
}: {
  number: string;
  title: string;
  detail: string;
}) {
  return (
    <div className="section-title">
      <span className="section-number">{number}</span>
      <div>
        <h2>{title}</h2>
        <p>{detail}</p>
      </div>
    </div>
  );
}
