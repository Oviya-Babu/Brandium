"use client";

import { usePathname, useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { LayoutDashboard, LogOut, Moon, ShieldCheck, Sun } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

function ThemeToggle() {
  const { setTheme } = useTheme();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <Sun className="h-4 w-4 scale-100 dark:scale-0" />
          <Moon className="absolute h-4 w-4 scale-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => setTheme("light")}>Light</DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("dark")}>Dark</DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("system")}>System</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

/**
 * Thin top navigation for the org-level Dashboard only. Every other
 * authenticated surface has its own shell now: the marketing Landing
 * page and the Login/Signup pages are full-bleed with no nav chrome,
 * and every Brand Workspace route (`/brands/[brandId]/*`) gets the
 * persistent sidebar shell (`components/app-shell/*`) instead of a top
 * bar — a real information architecture change, not a leftover from
 * the pre-redesign single-nav layout.
 */
export function NavShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [orgId, setOrgId] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    setOrgId(localStorage.getItem("brandium_org_id"));
    setEmail(localStorage.getItem("brandium_user_email"));
  }, [pathname]);

  const isChromeless = pathname === "/" || pathname === "/login" || pathname === "/signup" || pathname.startsWith("/brands/");
  if (isChromeless) return <>{children}</>;

  function signOut() {
    localStorage.removeItem("brandium_org_id");
    localStorage.removeItem("brandium_user_id");
    localStorage.removeItem("brandium_user_email");
    router.push("/login");
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-20 border-b border-border bg-background/90 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <a href="/dashboard" className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <ShieldCheck className="h-4 w-4 text-primary" />
            BrandGuard AI
          </a>
          <nav className="flex items-center gap-4">
            <a
              href="/dashboard"
              className={cn(
                "flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground",
                pathname === "/dashboard" && "text-foreground",
              )}
            >
              <LayoutDashboard className="h-3.5 w-3.5" />
              Dashboard
            </a>
            {orgId && (
              <span className="hidden text-xs text-muted-foreground sm:inline">
                {email ?? "actor"} · org {orgId.slice(0, 8)}
              </span>
            )}
            {orgId && (
              <button
                onClick={signOut}
                className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
              >
                <LogOut className="h-3.5 w-3.5" />
                Reset
              </button>
            )}
            <ThemeToggle />
          </nav>
        </div>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}
