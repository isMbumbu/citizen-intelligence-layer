import { ReportDetailPage } from "@/components/civic/report-detail";
import { SiteShell } from "@/components/civic/site-shell";

export const dynamic = "force-dynamic";
export default async function ReportPage({ params }: PageProps<"/reports/[id]">) { const { id } = await params; return <SiteShell><ReportDetailPage id={id}/></SiteShell>; }
