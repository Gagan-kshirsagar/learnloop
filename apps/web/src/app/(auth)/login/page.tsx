"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { ArrowRight, Loader2, Play } from "lucide-react";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { AxiosError } from "axios";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useGuestMutation, useLoginMutation } from "@/lib/query/auth";
import { useAuthStore } from "@/stores/authStore";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const status = useAuthStore((s) => s.status);
  const [authError, setAuthError] = useState<string | null>(null);

  const loginMutation = useLoginMutation();
  const guestMutation = useGuestMutation();

  useEffect(() => {
    if (status === "authenticated" || status === "guest") {
      router.replace("/app");
    }
  }, [status, router]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = (data: LoginFormValues) => {
    setAuthError(null);
    loginMutation.mutate(data, {
      onSuccess: () => router.push("/app"),
      onError: (err: AxiosError<{ detail?: string }> | Error) => {
        const axiosErr = err as AxiosError<{ detail?: string }>;
        setAuthError(
          axiosErr?.response?.data?.detail ||
            err.message ||
            "Invalid email or password. Please try again."
        );
      },
    });
  };

  const handleGuestLogin = () => {
    setAuthError(null);
    guestMutation.mutate(undefined, {
      onSuccess: () => router.push("/app"),
      onError: (err: AxiosError<{ detail?: string }> | Error) => {
        const axiosErr = err as AxiosError<{ detail?: string }>;
        setAuthError(
          axiosErr?.response?.data?.detail ||
            err.message ||
            "Failed to create demo sandbox. Please try again."
        );
      },
    });
  };

  const isLoading = loginMutation.isPending || guestMutation.isPending;

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
            Welcome back
          </h1>
          <p className="mt-1 text-sm text-muted">
            Sign in to your LearnLoop workspace
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
            <label htmlFor="email" className="text-sm font-medium text-foreground">
              Email
            </label>
            <Input
              id="email"
              type="email"
              placeholder="you@organization.com"
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
              placeholder="Enter your password"
              autoComplete="current-password"
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
            {loginMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Signing in…
              </>
            ) : (
              <>
                Sign in
                <ArrowRight className="ml-2 h-4 w-4" />
              </>
            )}
          </Button>
        </form>

        <div className="relative my-5">
          <div className="absolute inset-0 flex items-center" aria-hidden="true">
            <div className="w-full border-t border-subtle" />
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="bg-surface px-3 text-faint">or</span>
          </div>
        </div>

        <Button
          type="button"
          variant="outline"
          className="!h-10 w-full font-medium"
          onClick={handleGuestLogin}
          disabled={isLoading}
        >
          {guestMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Setting up demo…
            </>
          ) : (
            <>
              <Play className="mr-2 h-3.5 w-3.5" />
              Try demo without account
            </>
          )}
        </Button>

        <p className="mt-6 text-center text-xs text-muted">
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            className="font-semibold text-accent transition-colors hover:text-accent-hover"
          >
            Create organization
          </Link>
        </p>
      </div>
    </motion.div>
  );
}
