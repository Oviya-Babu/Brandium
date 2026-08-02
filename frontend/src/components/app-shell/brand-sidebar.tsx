"use client";

import { useRouter } from "next/navigation";
import {
  BookOpen,
  ChevronsUpDown,
  GitBranch,
  Layers,
  LayoutDashboard,
  LogOut,
  ScanSearch,
  ScrollText,
  ShieldCheck,
  UploadCloud,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import type { Brand } from "@/lib/api-client";

const NAV_ITEMS = [
  { href: "", label: "Overview", icon: LayoutDashboard },
  { href: "/genome", label: "Brand Genome", icon: GitBranch },
  { href: "/knowledge", label: "Knowledge Repository", icon: BookOpen },
  { href: "/policies", label: "Policies", icon: ScrollText },
  { href: "/analysis", label: "Asset Analysis", icon: ScanSearch },
  { href: "/upload", label: "Upload", icon: UploadCloud },
];

/**
 * The persistent left navigation for a Brand Workspace — replaces the
 * old top-tab-bar pattern (`brands/[brandId]/page.tsx`'s History/
 * Genome/Policy tabs) with a real information architecture: each
 * concern (Genome, Knowledge, Policies, Analysis, Upload) is its own
 * route, matching how every reference enterprise product (Datadog,
 * GitHub Enterprise, Vercel) structures a workspace, rather than
 * collapsing a growing feature set into one page's tab strip.
 */
export function BrandSidebar({
  brandId,
  brand,
  email,
  orgId,
}: {
  brandId: string;
  brand?: Brand;
  email: string | null;
  orgId: string | null;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const base = `/brands/${brandId}`;

  function signOut() {
    localStorage.removeItem("brandium_org_id");
    localStorage.removeItem("brandium_user_id");
    localStorage.removeItem("brandium_user_email");
    router.push("/login");
  }

  const genomeReady = !!brand?.active_genome_version_id;
  const policyReady = !!brand?.active_policy_version_id;

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left hover:bg-sidebar-accent">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <div className="flex min-w-0 flex-1 flex-col">
                <span className="truncate text-sm font-semibold text-sidebar-foreground">
                  {brand?.name ?? "Loading…"}
                </span>
                <span className="truncate text-xs text-muted-foreground">BrandGuard AI</span>
              </div>
              <ChevronsUpDown className="h-4 w-4 shrink-0 text-muted-foreground" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-56">
            <DropdownMenuItem onClick={() => router.push("/dashboard")}>
              <Layers className="h-4 w-4" /> Switch brand
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Workspace</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {NAV_ITEMS.map((item) => {
                const href = `${base}${item.href}`;
                const active = item.href === "" ? pathname === base : pathname.startsWith(href);
                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton asChild isActive={active} tooltip={item.label}>
                      <a href={href}>
                        <item.icon />
                        <span>{item.label}</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Governance status</SidebarGroupLabel>
          <SidebarGroupContent>
            <div className="flex flex-col gap-1.5 px-2 py-1 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Genome</span>
                <span className={cn("font-medium", genomeReady ? "text-aligned" : "text-partial")}>
                  {genomeReady ? "Active" : "Not active"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Policy</span>
                <span className={cn("font-medium", policyReady ? "text-aligned" : "text-partial")}>
                  {policyReady ? "Active" : "Not active"}
                </span>
              </div>
            </div>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left hover:bg-sidebar-accent">
              <Avatar className="h-7 w-7">
                <AvatarFallback className="text-xs">{(email ?? "U").slice(0, 1).toUpperCase()}</AvatarFallback>
              </Avatar>
              <div className="flex min-w-0 flex-1 flex-col">
                <span className="truncate text-xs font-medium text-sidebar-foreground">{email ?? "actor"}</span>
                <span className="truncate text-[11px] text-muted-foreground">org {orgId?.slice(0, 8)}</span>
              </div>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-56">
            <DropdownMenuItem onClick={() => router.push("/dashboard")}>
              <LayoutDashboard className="h-4 w-4" /> Dashboard
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={signOut} variant="destructive">
              <LogOut className="h-4 w-4" /> Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
