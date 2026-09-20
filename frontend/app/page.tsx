import { CivicHome } from "@/components/civic/discovery";
import { SiteShell } from "@/components/civic/site-shell";

export const dynamic = "force-dynamic";

export default function Home() {
  return (
    <SiteShell>
      <CivicHome />
    </SiteShell>
  );
}
