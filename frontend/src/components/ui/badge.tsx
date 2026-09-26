import type * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "outline" | "destructive";
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variantStyles = {
    default: "bg-indigo-600 text-white hover:bg-indigo-500",
    secondary: "bg-slate-800 text-slate-200 hover:bg-slate-700",
    outline: "border border-slate-700 text-slate-300",
    destructive: "bg-rose-600 text-white hover:bg-rose-500",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-md px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2",
        variantStyles[variant],
        className,
      )}
      {...props}
    />
  );
}

export { Badge };
