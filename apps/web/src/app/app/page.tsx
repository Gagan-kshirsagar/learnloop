"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Database,
  GraduationCap,
  Key,
  Layers,
  Play,
  ShieldCheck,
  Sparkles,
  UserCheck,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useMyEnrollmentsQuery } from "@/lib/query/learning";
import { useAuthStore } from "@/stores/authStore";

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const tenant = useAuthStore((state) => state.tenant);
  const status = useAuthStore((state) => state.status);

  const { data: enrollments, isLoading: isEnrollmentsLoading } = useMyEnrollmentsQuery();

  const totalEnrolled = enrollments?.length || 0;
  const completedLessonsTotal =
    enrollments?.reduce((acc, e) => acc + (e.completed_lessons || 0), 0) || 0;

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-subtle pb-6"
      >
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            Welcome back, {user?.name || "Learner"}
          </h1>
          <p className="text-muted text-sm mt-1">
            Track your curriculum progress and verified tenant security isolation.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/app/courses">
            <Button className="font-semibold gap-1.5 text-xs shadow-xs rounded-xl">
              <BookOpen className="h-3.5 w-3.5" />
              <span>Browse Catalog</span>
            </Button>
          </Link>
        </div>
      </motion.div>

      {/* Continue Learning Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GraduationCap className="h-4 w-4 text-accent" />
            <h2 className="text-base font-bold tracking-tight text-foreground">
              Continue Learning
            </h2>
          </div>
          {totalEnrolled > 0 && (
            <span className="text-xs font-medium text-muted">
              {totalEnrolled} {totalEnrolled === 1 ? "course enrolled" : "courses enrolled"} · {completedLessonsTotal} lessons completed
            </span>
          )}
        </div>

        {/* Loading Skeletons */}
        {isEnrollmentsLoading && (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-subtle bg-surface p-6 space-y-4 shadow-xs">
              <Skeleton className="h-6 w-3/4 rounded-xl" />
              <Skeleton className="h-3 w-full rounded-full" />
              <div className="flex justify-between">
                <Skeleton className="h-4 w-24 rounded-lg" />
                <Skeleton className="h-8 w-28 rounded-xl" />
              </div>
            </div>
            <div className="rounded-2xl border border-subtle bg-surface p-6 space-y-4 shadow-xs">
              <Skeleton className="h-6 w-3/4 rounded-xl" />
              <Skeleton className="h-3 w-full rounded-full" />
              <div className="flex justify-between">
                <Skeleton className="h-4 w-24 rounded-lg" />
                <Skeleton className="h-8 w-28 rounded-xl" />
              </div>
            </div>
          </div>
        )}

        {/* Active Enrolled Courses */}
        {!isEnrollmentsLoading && enrollments && enrollments.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2">
            {enrollments.map((item) => (
              <Card
                key={item.id}
                className="border-subtle bg-surface shadow-xs transition-all hover:border-strong hover:shadow-md"
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <Badge
                        variant="outline"
                        className="text-[10px] font-medium text-accent border-accent/30 bg-accent-soft mb-1.5"
                      >
                        {item.progress_percentage === 100 ? "Completed" : "In Progress"}
                      </Badge>
                      <CardTitle className="text-base font-bold text-foreground line-clamp-1">
                        {item.course_title}
                      </CardTitle>
                    </div>
                    <span className="font-mono text-xs font-bold text-accent">
                      {item.progress_percentage}%
                    </span>
                  </div>
                  <CardDescription className="text-xs text-muted line-clamp-2 leading-relaxed">
                    {item.course_description || "Curriculum grounded with interactive Socratic AI guidance."}
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-3 pt-0">
                  {/* Progress Bar */}
                  <div className="h-2 w-full overflow-hidden rounded-full bg-surface-2">
                    <div
                      className="h-full rounded-full bg-accent transition-all duration-500"
                      style={{ width: `${item.progress_percentage}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between pt-1 text-xs">
                    <span className="text-muted font-medium text-[11px]">
                      {item.completed_lessons} of {item.total_lessons} lessons completed
                    </span>

                    <Link href={`/app/courses/${item.course_id}`}>
                      <Button size="sm" variant="outline" className="h-7 text-xs font-medium gap-1 rounded-xl">
                        <Play className="h-3 w-3 fill-current" />
                        <span>Resume</span>
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Empty Enrollment State */}
        {!isEnrollmentsLoading && enrollments && enrollments.length === 0 && (
          <Card className="border-dashed border-subtle bg-surface/50 p-8 text-center shadow-xs">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-soft text-accent border border-accent/20">
              <Sparkles className="h-6 w-6" />
            </div>
            <h3 className="text-base font-bold text-foreground">Start your learning journey</h3>
            <p className="mx-auto mt-1 max-w-sm text-xs text-muted leading-relaxed">
              Explore your organization&apos;s courses, complete interactive Python challenges, and get Socratic guidance from the AI tutor.
            </p>
            <div className="mt-4 flex justify-center">
              <Link href="/app/courses">
                <Button size="sm" className="font-semibold gap-1.5 text-xs rounded-xl shadow-xs">
                  <span>Explore Courses</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
          </Card>
        )}
      </div>

      {/* Tenancy & Context Overview Cards */}
      <div className="space-y-4 pt-2">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-accent" />
          <h2 className="text-base font-bold tracking-tight text-foreground">
            Workspace &amp; Tenancy Security
          </h2>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card className="border-subtle bg-surface shadow-xs transition-all hover:border-strong hover:shadow-md">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-muted">Tenant Organization</CardTitle>
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-surface-2 text-muted border border-subtle">
                <Layers className="h-4 w-4" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-xl font-bold tracking-tight text-foreground">{tenant?.name}</div>
              <p className="text-xs text-muted mt-1 font-mono">
                Slug: {tenant?.slug}
              </p>
              <div className="mt-3.5 flex items-center gap-1.5 text-xs text-success font-medium">
                <ShieldCheck className="h-3.5 w-3.5" />
                <span>RLS Context Active</span>
              </div>
            </CardContent>
          </Card>

          <Card className="border-subtle bg-surface shadow-xs transition-all hover:border-strong hover:shadow-md">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-muted">Identity &amp; Role</CardTitle>
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-surface-2 text-muted border border-subtle">
                <UserCheck className="h-4 w-4" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-xl font-bold capitalize text-foreground">{user?.role}</div>
              <p className="text-xs text-muted mt-1 truncate">
                {user?.email}
              </p>
              <div className="mt-3.5 flex items-center gap-1.5 text-xs text-muted font-mono truncate">
                <Key className="h-3.5 w-3.5 text-faint" />
                <span>ID: {user?.id}</span>
              </div>
            </CardContent>
          </Card>

          <Card className="border-subtle bg-surface shadow-xs transition-all hover:border-strong hover:shadow-md sm:col-span-2 lg:col-span-1">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-muted">Tenancy Isolation Status</CardTitle>
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-surface-2 text-muted border border-subtle">
                <Database className="h-4 w-4" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-xl font-bold text-success flex items-center gap-1.5">
                <CheckCircle2 className="h-5 w-5" />
                <span>Enforced</span>
              </div>
              <p className="text-xs text-muted mt-1 font-mono truncate">
                app.tenant_id = {tenant?.id}
              </p>
              <div className="mt-3.5 text-xs text-muted">
                Mode: <span className="font-semibold text-foreground uppercase">{status}</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tenancy Architecture Callout */}
        <Card className="border-subtle bg-surface-2/40 shadow-xs">
          <CardHeader>
            <CardTitle className="text-base font-semibold text-foreground">Multi-Tenant Isolation Foundation</CardTitle>
            <CardDescription className="text-xs text-muted leading-relaxed">
              Every database query executed on behalf of this session is restricted to tenant <code className="font-mono text-foreground font-semibold px-1 py-0.5 rounded bg-surface border border-subtle">{tenant?.id}</code> by Postgres Row-Level Security policies. Cross-tenant data leakage is prevented at the database engine level.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    </div>
  );
}
