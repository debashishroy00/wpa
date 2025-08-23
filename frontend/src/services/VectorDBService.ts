/**
 * WealthPath AI - Vector Database Service
 * Handles indexing and searching of financial data embeddings
 */

export interface VectorSearchResult {
    content: string;
    metadata: {
        user_id: number;
        category: string;
        subcategory: string;
        timestamp: string;
        goal_id?: string;
    };
    distance?: number;
}

export interface VectorIndexResult {
    status: string;
    documents_indexed: number;
    user_id: number;
    timestamp: string;
}

export interface VectorStatus {
    user_id: number;
    total_documents: number;
    categories: Record<string, number>;
    is_indexed: boolean;
}

export class VectorDBService {
    private static instance: VectorDBService;
    private baseURL: string;
    
    constructor() {
        this.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    }
    
    static getInstance(): VectorDBService {
        if (!this.instance) {
            this.instance = new VectorDBService();
        }
        return this.instance;
    }
    
    private getAuthHeaders(): Record<string, string> {
        const authTokens = localStorage.getItem('auth_tokens');
        if (!authTokens) {
            throw new Error('Authentication token not found');
        }
        
        try {
            const tokens = JSON.parse(authTokens);
            const token = tokens.access_token;
            
            return {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            };
        } catch (error) {
            throw new Error('Invalid auth tokens format');
        }
    }
    
    /**
     * Index user's financial data into vector database
     */
    async indexUserData(userId: number): Promise<VectorIndexResult> {
        try {
            const response = await fetch(`${this.baseURL}/api/v1/vector/index/${userId}`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to index data');
            }
            
            const result = await response.json();
            console.log('Vector indexing complete:', result);
            return result;
        } catch (error) {
            console.error('Failed to index vector data:', error);
            throw error;
        }
    }
    
    /**
     * Search for relevant financial context
     */
    async searchContext(userId: number, query: string, nResults: number = 5): Promise<VectorSearchResult[]> {
        try {
            const url = new URL(`${this.baseURL}/api/v1/vector/search/${userId}`);
            url.searchParams.append('query', query);
            url.searchParams.append('n_results', nResults.toString());
            
            const response = await fetch(url.toString(), {
                method: 'POST',
                headers: this.getAuthHeaders(),
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Search failed');
            }
            
            const data = await response.json();
            return data.results;
        } catch (error) {
            console.error('Vector search failed:', error);
            throw error;
        }
    }
    
    /**
     * Get formatted context for chat
     */
    async getChatContext(userId: number, message: string): Promise<string> {
        try {
            const url = new URL(`${this.baseURL}/api/v1/vector/chat-context/${userId}`);
            url.searchParams.append('message', message);
            
            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: this.getAuthHeaders(),
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to get context');
            }
            
            const data = await response.json();
            return data.context;
        } catch (error) {
            console.error('Failed to get chat context:', error);
            throw error;
        }
    }
    
    /**
     * Get vector database status for user
     */
    async getVectorStatus(userId: number): Promise<VectorStatus> {
        try {
            const response = await fetch(`${this.baseURL}/api/v1/vector/status/${userId}`, {
                method: 'GET',
                headers: this.getAuthHeaders(),
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to get status');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Failed to get vector status:', error);
            throw error;
        }
    }
    
    /**
     * Clear user's vector data
     */
    async clearUserData(userId: number): Promise<{ status: string; deleted_count: number }> {
        try {
            const response = await fetch(`${this.baseURL}/api/v1/vector/clear/${userId}`, {
                method: 'DELETE',
                headers: this.getAuthHeaders(),
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to clear data');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Failed to clear vector data:', error);
            throw error;
        }
    }
    
    /**
     * Reindex user data (clear and reindex)
     */
    async reindexUserData(userId: number): Promise<VectorIndexResult> {
        try {
            // Clear existing data
            await this.clearUserData(userId);
            
            // Reindex
            const result = await this.indexUserData(userId);
            
            return result;
        } catch (error) {
            console.error('Failed to reindex:', error);
            throw error;
        }
    }
    
    /**
     * Test vector search with sample queries
     */
    async testVectorSearch(userId: number): Promise<Record<string, VectorSearchResult[]>> {
        const testQueries = [
            "What is my net worth?",
            "How much do I have in real estate?", 
            "What are my investment preferences?",
            "Tell me about my retirement goal",
            "What's my tax situation?",
            "How much emergency fund do I have?"
        ];
        
        const results: Record<string, VectorSearchResult[]> = {};
        
        for (const query of testQueries) {
            try {
                results[query] = await this.searchContext(userId, query, 3);
            } catch (error) {
                console.error(`Test query failed: ${query}`, error);
                results[query] = [];
            }
        }
        
        return results;
    }
}

export default VectorDBService.getInstance();