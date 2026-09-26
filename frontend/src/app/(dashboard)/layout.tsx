"use client";

import type { ReactNode } from "react";

/**
 * Dashboard layout — legacy chat interface removed.
 * This layout now simply renders its children (which redirect to /career-advisor).
 */
export default function DashboardLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <>{children}</>;
}
