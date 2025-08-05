import GoogleProvider from "next-auth/providers/google";

export const authOptions = {
    providers: [
        GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID || '',
            clientSecret: process.env.GOOGLE_CLIENT_SECRET || '',
        }),
    ],
    pages: {
        signIn: "/auth/signin",
        error: "/auth/signin",
    },
    session: {
        strategy: "jwt",
        maxAge: 30 * 24 * 60 * 60, // 30 days
    },
    callbacks: {
        async jwt({ token, user, account }: any) {
            if (account && user) {
                token.accessToken = account.access_token;
                token.userId = user.id;
            }
            return token;
        },
        async session({ session, token }: any) {
            if (token) {
                session.user.id = token.userId as string;
                session.accessToken = token.accessToken as string;
            }
            return session;
        },
    },
    secret: process.env.NEXTAUTH_SECRET,
}; 