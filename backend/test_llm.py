import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_llama_prompts():
    endpoint = os.getenv("AZURE_LLM_ENDPOINT") or os.getenv("AZURE_AI_ENDPOINT")
    if endpoint and not endpoint.endswith("/chat/completions"):
        endpoint = endpoint.rstrip("/") + "/chat/completions"
    api_key = os.getenv("AZURE_AI_API_KEY")

    if not endpoint or not api_key:
        print("⚠️  AZURE_LLM_ENDPOINT / AZURE_AI_ENDPOINT or AZURE_AI_API_KEY missing in .env — skipping live test.")
        print("✅ Sample would call Azure Llama 3.3 with 3 PO prompts.")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    
    invoice_samples = [
        ("2000234706", "Lactech plus Centre Urbain Nord B 5-4 Immeuble Nour City 1082 Tunis Matricule Fiscale :1107543Y/A/M/ Order Date: 2026-07-24 PO: 2000234706 Item: MacBook Pro 16\" M5 18 CPU and 20 GPU, Qty: 1"),
        ("2000237658", "Lactech plus Centre Urbain Nord B 5-4 Immeuble Nour City 1082 Tunis PO: 2000237658 Dell Latitude 5440 Core i7 16GB RAM 512GB SSD Qty 10"),
        ("2000243378", "Lactech plus Centre Urbain Nord B 5-4 Immeuble Nour City 1082 Tunis PO: 2000243378 EPOS Impact 100 MS Stereo USB-C Headset Qty 15")
    ]

    for po_num, sample in invoice_samples:
        prompt = f"""You are an IT inventory specialist analyzing a commercial invoice. Identify the exact equipment, product models, and quantities associated with Purchase Order number {po_num} or listed on the invoice.

RULES:
- Maximum 15 words
- State the exact brand, model, and item description clearly (e.g. "MacBook Pro 16 M5 18 CPU and 20 GPU", "10x Dell Latitude 5440 Laptops", "15x EPOS Impact 100 Headsets")
- DO NOT use generic phrases like "Equipment for PO"
- Return ONLY valid JSON in format: {{"description": "Exact equipment name/model"}}

Invoice Text:
"{sample}"

Response:"""

        payload = {
            "model": "Llama-3.3-70B-Instruct",
            "messages": [
                {"role": "system", "content": "You are an IT inventory assistant. Extract exact equipment models in short JSON format."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.1
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, headers=headers, json=payload) as resp:
                text = await resp.text()
                data = json.loads(text)
                content = data["choices"][0]["message"]["content"]
                print(f"PO {po_num} -> {content}")

if __name__ == "__main__":
    asyncio.run(test_llama_prompts())
