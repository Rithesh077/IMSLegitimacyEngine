export interface CompanyInput {
    name: string;
    cin?: string;
    website?: string;
}

export interface VerificationResult {
    is_registered: boolean;
    cin?: string;
    registration_date?: string;
    status: string;
    confidence_score: number;
    verification_source: string;
    red_flags: string[];
}

export interface CredibilityAnalysis {
    trust_score: number;
    trust_tier: "HIGH" | "MEDIUM" | "LOW";
    verification_status: string;
    review_count: number;
    sentiment_summary: string;
    red_flags: string[];
    scraped_sources: string[];
    details?: any;
}
