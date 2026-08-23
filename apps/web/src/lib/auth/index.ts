import { firebaseAuthProvider } from "./firebaseProvider";
import { jwtAuthProvider } from "./jwtProvider";
import { AuthProviderClient } from "./types";

export * from "./types";
export { firebaseAuthProvider } from "./firebaseProvider";
export { jwtAuthProvider } from "./jwtProvider";

const providerName = process.env.NEXT_PUBLIC_AUTH_PROVIDER?.toLowerCase() || "jwt";

export const authProvider: AuthProviderClient =
  providerName === "firebase" ? firebaseAuthProvider : jwtAuthProvider;
