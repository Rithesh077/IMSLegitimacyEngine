"use client";

import { useState } from "react";
import { ArrowRight, Shield, CheckCircle, AlertTriangle, XCircle, Loader2 } from "lucide-react";

export default function Home() {
    const [formData, setFormData] = useState({
        name: "",
        govt_id: "",
        website: "",
    });
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setResult(null);

        try {
            const res = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });
            const data = await res.json();
            setResult(data);
        } catch (err) {
            console.error(err);
            alert("Analysis failed. Ensure Python backend is running.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-4">
            <div className="w-full max-w-2xl">
                <div className="mb-10 text-center">
                    <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
                        Company Legitimacy Check
                    </h1>
                    <p className="text-slate-400 mt-2">
                        Enter company details to run the automated scraping & sentiment pipeline.
                    </p>
                </div>

                <div className="grid gap-8 lg:grid-cols-[1fr,1.2fr]">
                    {/* Form Section */}
                    <div className="bg-slate-900/50 p-6 rounded-2xl border border-slate-800 backdrop-blur-sm">
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">
                                    Company Name
                                </label>
                                <input
                                    required
                                    type="text"
                                    placeholder="e.g. Acme Corp"
                                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">
                                    Govt Registration ID <span className="text-xs text-slate-500">(CIN/EIN)</span>
                                </label>
                                <input
                                    type="text"
                                    placeholder="Optional"
                                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                                    value={formData.govt_id}
                                    onChange={(e) => setFormData({ ...formData, govt_id: e.target.value })}
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">
                                    Website URL
                                </label>
                                <input
                                    type="url"
                                    placeholder="https://example.com"
                                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                                    value={formData.website}
                                    onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2.5 rounded-lg flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? <Loader2 className="animate-spin w-4 h-4" /> : <Shield className="w-4 h-4" />}
                                {loading ? "Analyzing..." : "Verify Legitimacy"}
                            </button>
                        </form>
                    </div>

                    {/* Results Section */}
                    <div className="min-h-[300px] flex flex-col">
                        {result ? (
                            <div className="bg-slate-900/80 p-6 rounded-2xl border border-slate-800 text-slate-200 h-full animate-in fade-in slide-in-from-bottom-4">
                                <div className="flex justify-between items-start mb-6">
                                    <div>
                                        <h3 className="text-sm text-slate-400 uppercase tracking-widest font-semibold">Trust Score</h3>
                                        <div className="text-5xl font-bold mt-1 tabular-nums">{result.trust_score}<span className="text-xl text-slate-500">/100</span></div>
                                    </div>
                                    <TrustBadge tier={result.trust_tier} />
                                </div>

                                <div className="space-y-4">
                                    <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex justify-between items-center">
                                        <span className="text-sm text-slate-400">Reviews Analyzed</span>
                                        <span className="font-mono">{result.review_count}</span>
                                    </div>
                                    <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                                        <span className="text-sm text-slate-400 block mb-2">Sources Found</span>
                                        <div className="flex flex-wrap gap-2">
                                            {result.sources?.map((s: string, i: number) => (
                                                <a key={i} href={s} target="_blank" className="text-xs text-blue-400 hover:underline truncate max-w-[200px] block">{new URL(s).hostname}</a>
                                            ))}
                                            {(!result.sources || result.sources.length === 0) && <span className="text-xs text-slate-500">None</span>}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="h-full border-2 border-dashed border-slate-800 rounded-2xl flex flex-col items-center justify-center text-slate-600 p-8 text-center group">
                                <Shield className="w-12 h-12 mb-4 opacity-20 group-hover:opacity-30 transition-opacity" />
                                <p>Enter details and hit Verify to see the analysis report.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </main>
    );
}

function TrustBadge({ tier }: { tier: string }) {
    if (tier === "HIGH") return <div className="px-4 py-1.5 rounded-full bg-green-500/20 text-green-400 border border-green-500/50 flex items-center gap-2 text-sm font-bold"><CheckCircle className="w-4 h-4" /> HIGH TRUST</div>;
    if (tier === "MEDIUM") return <div className="px-4 py-1.5 rounded-full bg-yellow-500/20 text-yellow-400 border border-yellow-500/50 flex items-center gap-2 text-sm font-bold"><AlertTriangle className="w-4 h-4" /> REVIEW NEEDED</div>;
    return <div className="px-4 py-1.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/50 flex items-center gap-2 text-sm font-bold"><XCircle className="w-4 h-4" /> LOW TRUST</div>;
}
