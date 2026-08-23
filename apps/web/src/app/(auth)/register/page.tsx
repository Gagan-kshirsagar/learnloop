"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { ArrowRight, Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { AxiosError } from "axios";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRegisterMutation } from "@/lib/query/auth";
import { useAuthStore } from "@/stores/authStore";

const registerSchema = z.object({
  org_name: z
    .string()
    .min(2, "Organization name must be at least 2 characters")
    .max(100),
  name: z.string().min(2, "Your name must be at least 2 characters").max(100),
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const status = useAuthStore((s) => s.status);
  const [authError, setAuthError] = useState<string | null>(null);

  const registerMutation = useRegisterMutation();

  useEffect(() => {
    if (status === "authenticated" || status === "guest") {
      router.replace("/app");
    }
  }, [status, router]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { org_name: "", name: "", email: "", password: "" },
  });

  const onSubmit = (data: RegisterFormValues) => {
    setAuthError(null);
    registerMutation.mutate(data, {
      onSuccess: () => router.push("/app"),
      onError: (err: AxiosError<{ detail?: string }> | Error) => {
        const axiosErr = err as AxiosError<{ detail?: string }>;
        setAuthError(
          axiosErr?.response?.data?.detail ||
            err.message ||
            "Failed to create organization. Please try again."
        );
      },
    });
  };

  const isLoading = registerMutation.isPending;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="w-full max-w-[400px]"
    >
      <div className="rounded-2xl border border-subtle bg-surface p-7 shadow-lg sm:p-8">
        <div className="mb-6 text-center">
          <h1 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">
            Create your workspace
          </h1>
          <p className="mt-1 text-sm text-muted">
            Set up your organization in under a minute
          </p>
        </div>

        {authError && (
          <div
            role="alert"
            className="mb-4 rounded-lg border border-danger/30 bg-danger-soft px-3 py-2.5 text-sm text-danger"
          >
            {authError}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3.5" noValidate>
          <div className="space-y-1.5">
            <label htmlFor="org_name" className="text-sm font-medium text-foreground">
              Organization name
            </label>
            <Input
              id="org_name"
              type="text"
              placeholder="e.g. Stanford CS Department"
              disabled={isLoading}
              aria-invalid={!!errors.org_name}
              aria-describedby={errors.org_name ? "org-name-error" : undefined}
              className="h-10"
              {...register("org_name")}
            />
            {errors.org_name && (
              <p id="org-name-error" role="alert" className="text-xs text-danger">
                {errors.org_name.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label htmlFor="name" className="text-sm font-medium text-foreground">
              Your name
            </label>
            <Input
              id="name"
              type="text"
              placeholder="e.g. Alex Rivera"
              autoComplete="name"
              disabled={isLoading}
              aria-invalid={!!errors.name}
              aria-describedby={errors.name ? "name-error" : undefined}
              className="h-10"
              {...register("name")}
            />
            {errors.name && (
              <p id="name-error" role="alert" className="text-xs text-danger">
                {errors.name.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label htmlFor="email" className="text-sm font-medium text-foreground">
              Work email
            </label>
            <Input
              id="email"
              type="email"
              placeholder="alex@organization.com"
              autoComplete="email"
              disabled={isLoading}
              aria-invalid={!!errors.email}
              aria-describedby={errors.email ? "email-error" : undefined}
              className="h-10"
              {...register("email")}
            />
            {errors.email && (
              <p id="email-error" role="alert" className="text-xs text-danger">
                {errors.email.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label htmlFor="password" className="text-sm font-medium text-foreground">
              Password
            </label>
            <Input
              id="password"
              type="password"
              placeholder="Minimum 8 characters"
              autoComplete="new-password"
              disabled={isLoading}
              aria-invalid={!!errors.password}
              aria-describedby={errors.password ? "password-error" : undefined}
              className="h-10"
              {...register("password")}
            />
            {errors.password && (
              <p id="password-error" role="alert" className="text-xs text-danger">
                {errors.password.message}
              </p>
            )}
          </div>

          <Button
            type="submit"
            className="!h-10 w-full font-semibold"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating workspace…
              </>
            ) : (
              <>
                Create account
                <ArrowRight className="ml-2 h-4 w-4" />
              </>
            )}
          </Button>
        </form>

        <p className="mt-6 text-center text-xs text-muted">
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-semibold text-accent transition-colors hover:text-accent-hover"
          >
            Sign in
          </Link>
        </p>
      </div>
    </motion.div>
  );
}
