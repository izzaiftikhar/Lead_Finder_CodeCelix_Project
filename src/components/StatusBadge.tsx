import type { Status } from "@/lib/types";

const STYLE: Record<Status, string> = {
  yes: "badge badge-yes",
  no: "badge badge-no",
  unknown: "badge badge-muted",
  unreachable: "badge badge-muted",
};

export default function StatusBadge({ value, label }: { value: Status; label?: string }) {
  return <span className={STYLE[value]}>{label ?? value}</span>;
}
