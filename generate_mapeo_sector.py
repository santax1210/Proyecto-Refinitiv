import re

with open('tmp_industries.txt', 'r', encoding='utf-8') as f:
    industries = [line.strip() for line in f if line.strip() and line.strip() != 'nan']

# Sectores esperados
# 'Communication Services', 'Consumer Cyclical', 'Consumer Discretionary', 'Consumer Durables', 'Consumer Non Cyclical', 'Consumer Staples', 'Energy', 'Financials', 'Government', 'Health Care', 'Industrials', 'Information Technology', 'Main Consumer Goods', 'Materials', 'Otros', 'Real Estate', 'Utilities'

mapping_rules = [
    (r'(?i)\b(health|medical|biotech|pharma|hospital|life science|healthcare)\b', 'Health Care'),
    (r'(?i)\b(bank|financ|broker|insurance|invest|credit|mortgage|mbs|cmo|clo|abs|cdx|equity|bonds|treasury|loan|sovereign|supra|municipal|repo|cash|fund|derivative|swap|future|forward|liquid|deposit|commercial paper|tier 1|tier 2|coco|asset backed)\b', 'Financials_or_Gov'), 
    # Will refine Financials/Gov/Otros below
    (r'(?i)\b(tech|software|hardware|semiconductor|it|computer|electronic|data center|internet)\b', 'Information Technology'),
    (r'(?i)\b(telecom|communication|media|broadcasting|cable|entertainment|interactive|wireless|wireline|publish)\b', 'Communication Services'),
    (r'(?i)\b(real estate|reit|property|apartment|office|residential|homebuilder)\b', 'Real Estate'),
    (r'(?i)\b(energy|oil|gas|pipeline|renewable|solar|petroleum)\b', 'Energy'),
    (r'(?i)\b(utilit|water|electric|power)\b', 'Utilities'),
    (r'(?i)\b(material|chemical|metal|mining|gold|silver|paper|packaging|forest|plastic)\b', 'Materials'),
    (r'(?i)\b(auto|transport|air|rail|toll|airport|machinery|equipment|capital goods|construction|building|engineer|industrial|manufactur|commercial service|logistic)\b', 'Industrials'),
    (r'(?i)\b(staple|food|beverage|drink|tobacco|cosmetic|personal care|non-cyclical|non cyclical)\b', 'Consumer Staples'),
    (r'(?i)\b(retail|apparel|luxury|leisure|hotel|gaming|restaurant|consumer discretionary|consumer cyclical|cyclical|durables)\b', 'Consumer Cyclical'),
    (r'(?i)\b(consumer)\b', 'Consumer Discretionary'), # fallback for consumer
    (r'(?i)\b(government|treasur|sovereign|municipal|supra|agenc|public|authorit|tax|state|fed)\b', 'Government'),
    (r'(?i)\b(cash|fund|derivative|swap|future|forward|unclassified|unidentified|other|repo|deposit|liquid)\b', 'Otros')
]

# Gov overlaps with Fin, let's fix order
mapping_rules_ordered = [
    (r'(?i)\b(health|medical|biotech|pharma|hospital|life science|healthcare)\b', 'Health Care'),
    (r'(?i)\b(tech|software|hardware|semiconductor|it|computer|electronic|data center|internet)\b', 'Information Technology'),
    (r'(?i)\b(telecom|communication|media|broadcasting|cable|entertainment|interactive|wireless|wireline|publish)\b', 'Communication Services'),
    (r'(?i)\b(real estate|reit|property|apartment|office|residential|homebuilder)\b', 'Real Estate'),
    (r'(?i)\b(energy|oil|gas|pipeline|renewable|solar|petroleum)\b', 'Energy'),
    (r'(?i)\b(utilit|water|electric|power)\b', 'Utilities'),
    (r'(?i)\b(material|chemical|metal|mining|gold|silver|paper|packaging|forest|plastic)\b', 'Materials'),
    (r'(?i)\b(government|treasur|sovereign|municipal|supra|agenc|public|authorit|tax|fed|local|country|state)\b', 'Government'), # Govt first
    (r'(?i)\b(auto|transport|air|rail|toll|airport|machinery|equipment|capital goods|construction|building|engineer|industrial|manufactur|commercial service|logistic|security product)\b', 'Industrials'),
    (r'(?i)\b(staple|food|beverage|drink|tobacco|cosmetic|personal care|non-cyclical|non cyclical|education|academic)\b', 'Consumer Staples'),
    (r'(?i)\b(retail|apparel|luxury|leisure|hotel|gaming|restaurant|consumer discretionary|consumer cyclical|cyclical|durables|sport|travel)\b', 'Consumer Discretionary'),
    (r'(?i)\b(cash|fund|derivative|swap|future|forward|unclassified|unidentified|other|repo|deposit|liquid|note|sec|abs|mbs|cmo|clo|cdx|collateralized|pass through|asset backed)\b', 'Otros'),
    (r'(?i)\b(bank|financ|broker|insurance|invest|credit|mortgage|equity|bond|loan|commercial paper|tier 1|tier 2|coco|corporate|non corporate|debt)\b', 'Financials'), 
    (r'(?i)\b(consumer)\b', 'Main Consumer Goods'),
]

final_mapping = {}

for ind in industries:
    mapped = 'Otros'
    for pattern, category in mapping_rules_ordered:
        if re.search(pattern, ind):
            mapped = category
            break
    final_mapping[ind] = mapped

# Export to a python file
with open(r'c:\Users\Santiago\Documents\allocations_validation\src\logic\sector\mapeo_sectores.py', 'w', encoding='utf-8') as f:
    f.write('MAPEO_SECTORES_INDUSTRY = {\n')
    for k, v in final_mapping.items():
        # Escape quotes
        k_escaped = k.replace("'", "\\'")
        f.write(f"    '{k_escaped}': '{v}',\n")
    f.write('}\n')

print("Mapping generated in src/logic/sector/mapeo_sectores.py")
