/**
 * Neutral public wording for review and processing states. Internal moderation
 * reasons and reviewer notes are never shown; see /community-safety.
 */

export type PublicTone = "neutral" | "review" | "limited" | "removed";

export function evidenceReviewLabel(moderationState: string): { label: string; tone: PublicTone } {
  switch (moderationState) {
    case "FLAGGED":
      return { label: "Under review", tone: "review" };
    case "HIDDEN":
      return { label: "Limited while reviewed", tone: "limited" };
    case "REMOVED":
      return { label: "Removed for safety or privacy", tone: "removed" };
    default:
      return { label: "Not yet reviewed", tone: "neutral" };
  }
}

export function commentStateLabel(moderationState: string): { label: string; tone: PublicTone } {
  switch (moderationState) {
    case "FLAGGED":
    case "UNDER_REVIEW":
      return { label: "Under review", tone: "review" };
    case "HIDDEN":
      return { label: "Limited while reviewed", tone: "limited" };
    case "REMOVED":
      return { label: "Removed for safety or privacy", tone: "removed" };
    default:
      return { label: "Visible", tone: "neutral" };
  }
}

export function processingLabel(processingState: string): string {
  switch (processingState) {
    case "RAW":
      return "Received";
    case "VALIDATION_PASSED":
      return "File checks passed";
    case "EXTRACTED":
    case "INDEXED":
      return "Processed";
    case "FAILED":
      return "Could not be processed";
    case "HIDDEN":
      return "Limited while reviewed";
    default:
      return "Unavailable";
  }
}

export function evidenceKindLabel(mimeType: string): string {
  return mimeType.startsWith("image/") ? "Photo submitted by a citizen" : "Document submitted by a citizen";
}

export function attachedToLabel(attachedTo: "project" | "report" | "comment"): string {
  return attachedTo === "report" ? "Shared on a citizen report" : attachedTo === "comment" ? "Shared on a comment" : "Shared on the project";
}

const fieldLabels: Record<string, string> = {
  allocated_amount: "Allocated budget",
  committed_amount: "Committed funding",
  contracted_amount: "Contract amount",
  spent_amount: "Amount spent",
  reported_amount: "Reported expenditure",
  reported_progress_percentage: "Reported project progress",
  verification_status: "Verification status",
  contractor: "Contractor",
};

const claimKindLabels: Record<string, string> = {
  FINANCIAL: "Finance",
  PROGRESS: "Progress",
  CONTRACTOR: "Contract",
  VERIFICATION: "Verification",
};

/** Citizen-language name for a project fact; falls back to a tidied field name. */
export function fieldLabel(fieldName: string): string {
  return fieldLabels[fieldName] ?? fieldName.replaceAll("_", " ").replace(/^\w/, (letter) => letter.toUpperCase());
}

export function claimKindLabel(claimKind: string): string {
  return claimKindLabels[claimKind] ?? claimKind.replaceAll("_", " ").toLowerCase().replace(/^\w/, (letter) => letter.toUpperCase());
}
