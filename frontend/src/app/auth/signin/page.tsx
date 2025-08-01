'use client';

import { signIn, getSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { FcGoogle } from "react-icons/fc";
import Link from "next/link";
import { useToast } from "@/components/providers/ToastProvider";

export default function SignIn() {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);
    const { showToast } = useToast();

    useEffect(() => {
        // Check if user is already signed in
        getSession().then((session) => {
            if (session) {
                router.push("/");
            }
        });
    }, [router]);

    const handleGoogleSignIn = async () => {
        setIsLoading(true);
        try {
            await signIn("google", { callbackUrl: "/" });
        } catch (error) {
            showToast("Failed to sign in. Please try again.", "error");
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-amber-50 to-yellow-100 flex items-center justify-center px-4">
            <div className="max-w-md w-full space-y-8">
                <div className="text-center">
                    <h1 className="text-4xl font-bold text-amber-600 mb-2">Bkmrk&apos;d</h1>
                    <p className="text-gray-600">Sign in to your digital bookshelf</p>
                </div>

                <div className="bg-white rounded-2xl shadow-xl p-8 space-y-6">
                    <div className="text-center">
                        <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                            Welcome Back
                        </h2>
                        <p className="text-gray-500">
                            Access your personalized reading experience
                        </p>
                    </div>

                    <button
                        onClick={handleGoogleSignIn}
                        disabled={isLoading}
                        className="w-full flex items-center justify-center gap-3 bg-white border-2 border-gray-300 rounded-xl px-6 py-4 text-gray-700 font-medium hover:bg-gray-50 hover:border-amber-300 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <FcGoogle className="w-6 h-6" />
                        {isLoading ? "Signing in..." : "Continue with Google"}
                    </button>

                    <div className="text-center">
                        <p className="text-sm text-gray-500">
                            By signing in, you agree to our{" "}
                            <a href="#" className="text-amber-600 hover:underline">
                                Terms of Service
                            </a>{" "}
                            and{" "}
                            <a href="#" className="text-amber-600 hover:underline">
                                Privacy Policy
                            </a>
                        </p>
                    </div>
                </div>

                <div className="text-center">
                    <Link
                        href="/"
                        className="text-amber-600 hover:text-amber-700 font-medium"
                    >
                        ← Back to Home
                    </Link>
                </div>
            </div>
        </div>
    );
} 