import { CategoriesPage } from "@/components/civic/categories";
import { SiteShell } from "@/components/civic/site-shell";

export const dynamic = "force-dynamic";
export default function Categories() { return <SiteShell><CategoriesPage/></SiteShell>; }
