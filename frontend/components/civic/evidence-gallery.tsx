"use client";
/* eslint-disable @next/next/no-img-element -- user evidence is served by the API, not the Next image optimiser */

import Link from "next/link";
import { type Evidence, evidenceFileUrl } from "@/lib/api";
import { Icon, formatDate } from "./ui";

function sourceLabel(item: Evidence) {
  if (item.report_id) return "On a citizen report";
  if (item.comment_id) return "On a comment";
  return "On this project";
}

/**
 * Public citizen evidence: images shown as thumbnails, documents as file tiles.
 * Every item links to its record, which carries the citizen-evidence trust label.
 */
export function EvidenceGallery({ items, showSource = false, compact = false }: { items: Evidence[]; showSource?: boolean; compact?: boolean }) {
  return <ul className={`evidence-gallery ${compact ? "evidence-gallery--compact" : ""}`}>
    {items.map((item) => {
      const isImage = item.mime_type.startsWith("image/");
      return <li key={item.id}>
        <Link href={`/evidence/${item.id}`} className="evidence-tile" aria-label={`Open citizen evidence ${item.original_filename}`}>
          {isImage
            ? <img src={evidenceFileUrl(item.id)} alt={`Citizen-submitted photo ${item.original_filename}`} loading="lazy" decoding="async"/>
            : <span className="evidence-tile__doc"><Icon name="evidence" size={compact ? 18 : 26}/><span>{item.mime_type === "application/pdf" ? "PDF" : "File"}</span></span>}
          {!compact && <span className="evidence-tile__caption"><strong>{showSource ? sourceLabel(item) : formatDate(item.uploaded_at)}</strong>{showSource && <small>{formatDate(item.uploaded_at)}</small>}</span>}
        </Link>
      </li>;
    })}
  </ul>;
}
