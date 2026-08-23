"use client";

import { motion } from "framer-motion";
import { CheckCircle2, Database, Key, Layers, ShieldCheck, UserCheck } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/stores/authStore";

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const tenant = useAuthStore((state) => state.tenant);
  const status = useAuthStore((state) => state.status);

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
          Welcome back, {user?.name || "Learner"}
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Active tenant session with verified Postgres Row-Level Security isolation.
        </p>
      </motion.div>

      {/* Tenancy & Context Overview Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card className="border-border/60">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium">Tenant Organization</CardTitle>
            <Layers className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold tracking-tight">{tenant?.name}</div>
            <p className="text-xs text-muted-foreground mt-1 font-mono">
              Slug: {tenant?.slug}
            </p>
            <div className="mt-3 flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>RLS Context Active</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium">Identity & Role</CardTitle>
            <UserCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold capitalize">{user?.role}</div>
            <p className="text-xs text-muted-foreground mt-1 truncate">
              {user?.email}
            </p>
            <div className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground font-mono truncate">
              <Key className="h-3.5 w-3.5" />
              <span>ID: {user?.id}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60 sm:col-span-2 lg:col-span-1">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium">Tenancy Isolation Status</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
              <CheckCircle2 className="h-5 w-5" />
              <span>Enforced</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1 font-mono truncate">
              app.tenant_id = {tenant?.id}
            </p>
            <div className="mt-3 text-xs text-muted-foreground">
              Mode: <span className="font-semibold text-foreground uppercase">{status}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tenancy Architecture Callout */}
      <Card className="border-border/60 bg-muted/20">
        <CardHeader>
          <CardTitle className="text-base font-semibold">Multi-Tenant Isolation Foundation</CardTitle>
          <CardDescription className="text-xs">
            Every database query executed on behalf of this session is restricted to tenant <code className="font-mono text-foreground font-semibold">{tenant?.id}</code> by Postgres Row-Level Security policies. Cross-tenant data leakage is prevented at the database engine level.
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
