const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface LoginCredentials {
    username: string;
    password: string;
}

export interface RegisterData {
    email: string;
    username: string;
    password: string;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
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

    async login(credentials: LoginCredentials): Promise<AuthResponse> {
        const formData = new FormData();
        formData.append('username', credentials.username);
        formData.append('password', credentials.password);

        return this.request<AuthResponse>('/token', {
            method: 'POST',
            body: formData,
        });
    }

    async register(userData: RegisterData): Promise<any> {
        return this.request('/register', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    }

    async getCurrentUser(token: string): Promise<any> {
        return this.request('/users/me', {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });
    }
}

export const authService = new AuthService(API_BASE_URL); 