"use client";

import { use, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getBrand } from "@/lib/api-client";
import { BrandSidebar } from "@/components/app-shell/brand-sidebar";
import { WorkspaceTopbar } from "@/components/app-shell/workspace-topbar";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";

const SECTION_LABEL: Record<string, string> = {
  genome: "Brand Genome",
  knowledge: "Knowledge Repository",
  policies: "Policies",
  analysis: "Asset Analysis",
  upload: "Upload",
};

export default function BrandWorkspaceLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ brandId: string }>;
}) {
  const { brandId } = use(params);
  const pathname = usePathname();
  const [email, setEmail] = useState<string | null>(null);
  const [orgId, setOrgId] = useState<string | null>(null);

  useEffect(() => {
    setEmail(localStorage.getItem("brandium_user_email"));
    setOrgId(localStorage.getItem("brandium_org_id"));
  }, []);

  const { data: brand } = useQuery({
    queryKey: ["brand", brandId],
    queryFn: () => getBrand(brandId),
  });

  const segments = pathname.replace(`/brands/${brandId}`, "").split("/").filter(Boolean);
  const section = segments[0] ? SECTION_LABEL[segments[0]] : undefined;
  const detail = segments[1];

  return (
    <SidebarProvider>
      <div className="print:hidden">
        <BrandSidebar brandId={brandId} brand={brand} email={email} orgId={orgId} />
      </div>
      <SidebarInset>
        <div className="print:hidden">
          <WorkspaceTopbar brandName={brand?.name} section={section} detail={detail} />
        </div>
        <div className="flex-1 bg-muted/30 print:bg-white">{children}</div>
      </SidebarInset>
    </SidebarProvider>
  );
}
