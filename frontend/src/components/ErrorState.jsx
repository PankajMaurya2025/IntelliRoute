import { AlertTriangle, RotateCw } from "lucide-react";

export default function ErrorState({ message = "Something went wrong.", onRetry }) {
  return (
    <div className="state-block error-block">
      <AlertTriangle size={26} />
      <h4>Couldn't load this</h4>
      <p>{message}</p>
      {onRetry && (
        <button className="btn btn-outline btn-sm" onClick={onRetry}>
          <RotateCw size={14} /> Try again
        </button>
      )}
    </div>
  );
}
