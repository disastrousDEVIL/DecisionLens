import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "DecisionLens",
  description: "Benchmark AI decision systems with evidence.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}

