import axios from 'axios';
import type { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api/v1';

class ApiService {
    private api: AxiosInstance;

    constructor() {
        this.api = axios.create({
            baseURL: API_BASE_URL,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        this.setupInterceptors();
    }

    private setupInterceptors() {
        // Request interceptor
        this.api.interceptors.request.use(
            (config) => {
                // Add any auth tokens here if needed
                return config;
            },
            (error) => Promise.reject(error)
        );

        // Response interceptor
        this.api.interceptors.response.use(
            (response) => response,
            (error) => {
                // Handle errors globally
                if (error.response) {
                    // Server responded with error
                    console.error('API Error:', error.response.data);
                } else if (error.request) {
                    // Request made but no response
                    console.error('Network Error:', error.message);
                }
                return Promise.reject(error);
            }
        );
    }

    public getInstance(): AxiosInstance {
        return this.api;
    }
}

export const apiService = new ApiService();
export const api = apiService.getInstance();
