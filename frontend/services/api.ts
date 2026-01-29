import { CompanyInput, CredibilityAnalysis } from "../types";

const API_BASE_URL = "http://localhost:8000/api/v1";

export const analyzeCompany = async (data: CompanyInput): Promise<CredibilityAnalysis> => {
    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || "Analysis failed");
        }

        return await response.json();
    } catch (error) {
        console.error("API Error:", error);
        throw error;
    }
};
