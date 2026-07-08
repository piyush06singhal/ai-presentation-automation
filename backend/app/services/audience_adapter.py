from typing import Dict, Any

AUDIENCE_PROFILES: Dict[str, Dict[str, Any]] = {
    "CEO": {
        "tone_instruction": "Executive, strategic, and high-level. Keep slide descriptions short and punchy. Focus on long-term macro growth.",
        "focus_metrics": ["Revenue", "Profit", "Profit Margin", "Customer Retention"],
        "detail_level": "LOW",
        "recommendation_focus": "Strategic cost adjustments, scaling opportunities, and business alignment."
    },
    "Board Members": {
        "tone_instruction": "Formal, high-level summary, risk-oriented. Highlight quarterly performance highlights and major outliers.",
        "focus_metrics": ["Revenue", "Profit Margin", "Operating Cost", "Active Customers"],
        "detail_level": "LOW",
        "recommendation_focus": "Risk mitigation, revenue expansion, and market positioning."
    },
    "Finance": {
        "tone_instruction": "Quantitative, highly detailed, precise, and analytical. Use correct accounting descriptors.",
        "focus_metrics": ["Revenue", "Operating Cost", "Profit", "Profit Margin"],
        "detail_level": "HIGH",
        "recommendation_focus": "Expense controls, margin optimizations, and cash flow enhancements."
    },
    "Sales Leadership": {
        "tone_instruction": "Engaging, momentum-focused, and competitive. Emphasize top performers and pipeline growth rates.",
        "focus_metrics": ["Revenue", "Sales Quantity", "Order Volume", "Active Customers"],
        "detail_level": "MEDIUM",
        "recommendation_focus": "Territory expansion, product cross-selling, and sales incentive models."
    },
    "Marketing Team": {
        "tone_instruction": "Growth-focused, customer-centric, and creative. Relate metrics to engagement and customer volume shares.",
        "focus_metrics": ["Conversion Rate", "Customer Retention", "Active Customers", "Order Volume"],
        "detail_level": "MEDIUM",
        "recommendation_focus": "Campaign optimization, customer acquisition allocation, and retention programs."
    },
    "Operations Team": {
        "tone_instruction": "Process-oriented, action-driven, and bottleneck-focused. Focus on quantities, volumes, and workflow averages.",
        "focus_metrics": ["Sales Quantity", "Order Volume", "Operating Cost", "Active Customers"],
        "detail_level": "HIGH",
        "recommendation_focus": "Supply chain efficiency, capacity planning, and operational overhead reduction."
    },
    "Clients": {
        "tone_instruction": "Value-oriented, positive, collaborative, and results-focused. Emphasize partnership outcomes and service levels.",
        "focus_metrics": ["Sales Quantity", "Conversion Rate", "Customer Retention"],
        "detail_level": "MEDIUM",
        "recommendation_focus": "Operational collaboration, expanding service models, and mutual value generation."
    },
    "Investors": {
        "tone_instruction": "Financial-growth focused, persuasive, high-conviction, and margin-oriented. Emphasize scaling potential.",
        "focus_metrics": ["Revenue", "Profit", "Profit Margin", "Active Customers"],
        "detail_level": "LOW",
        "recommendation_focus": "Expansion pathways, capital allocation priorities, and addressable segment growth."
    }
}

def get_audience_instructions(audience: str) -> Dict[str, Any]:
    """Retrieves formatting guides and metric focuses for the selected target audience."""
    # Fallback to CEO if the requested audience is invalid or empty
    normalized = str(audience).strip()
    profile = AUDIENCE_PROFILES.get(normalized)
    
    if not profile:
        # Check case-insensitive match
        for key in AUDIENCE_PROFILES:
            if key.lower() == normalized.lower():
                return AUDIENCE_PROFILES[key]
        return AUDIENCE_PROFILES["CEO"]
        
    return profile
