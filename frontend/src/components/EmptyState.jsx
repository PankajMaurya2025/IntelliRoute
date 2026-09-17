import { Inbox } from "lucide-react";

export default function EmptyState({ icon: Icon = Inbox, title = "Nothing here yet", message, action }) {
  return (
    <div className="state-block">
      <Icon size={26} color="var(--ink-faint)" />
      <h4>{title}</h4>
      {message && <p>{message}</p>}
      {action}
    </div>
  );
}
