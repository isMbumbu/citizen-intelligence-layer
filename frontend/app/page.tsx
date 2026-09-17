import { ApiError, fetchHealth } from "@/lib/api";
import Header from "@/components/landing/header";
import Hero from "@/components/landing/hero";
import Problem from "@/components/landing/problem";
import HowItWorks from "@/components/landing/how-it-works";
import Features from "@/components/landing/features";
import Principles from "@/components/landing/principles";
import Footer from "@/components/landing/footer";

export const dynamic = "force-dynamic";

export default async function Home() {
  let apiStatus = "unreachable";
  try {
    const health = await fetchHealth();
    apiStatus = health.status;
  } catch (error) {
    apiStatus =
      error instanceof ApiError && error.status === 0 ? "unreachable" : "error";
  }

  return (
    <div className="flex flex-1 flex-col">
      <Header />
      <Hero apiStatus={apiStatus} />
      <Problem />
      <HowItWorks />
      <Features />
      <Principles />
      <Footer />
    </div>
  );
}