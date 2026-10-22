import { redirect } from "next/navigation";

// The taxonomy page is now "Categories"; keep old links working.
export default function Taxonomy() { redirect("/categories"); }
