const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface GoogleUser {
    email: string;
    name: string;
    google_id: string;
    avatar_url?: string;
}

export interface AuthResponse {
    user: {
        id: number;
        email: string;
        name?: string;
        avatar_url?: string;
        google_id?: string;
        is_active: boolean;
        created_at: string;
        updated_at: string;
    };
    access_token?: string;
}

class AuthService {
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;
        const config: RequestInit = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Auth service request failed:', error);
            throw error;
        }
    }

    async googleAuth(userData: GoogleUser): Promise<AuthResponse> {
        return this.request<AuthResponse>('/auth/google', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    }

    async register(email: string, username: string, password: string): Promise<AuthResponse> {
        return this.request<AuthResponse>('/register', {
            method: 'POST',
            body: JSON.stringify({
                email,
                username,
                password,
            }),
        });
    }

    async login(email: string, password: string): Promise<AuthResponse> {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);

        return this.request<AuthResponse>('/token', {
            method: 'POST',
            body: formData,
        });
    }
}

export const authService = new AuthService(API_BASE_URL); 