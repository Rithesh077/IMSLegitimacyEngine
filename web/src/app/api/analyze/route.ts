import { NextResponse } from "next/server";

export async function POST(request: Request) {
    try {
        const body = await request.json();

        // Proxy to Python Backend
        // Assuming python_service is running on port 8000
        const res = await fetch("http://127.0.0.1:8000/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(body),
        });

        if (!res.ok) {
            const errorText = await res.text();
            return NextResponse.json({ error: "Backend Analysis Failed", details: errorText }, { status: res.status });
        }

        const data = await res.json();
        return NextResponse.json(data);

    } catch (error) {
        console.error("Proxy Error:", error);
        return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
    }
}
