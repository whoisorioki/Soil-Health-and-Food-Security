# Observable Notebook Setup Guide for Zindi Submission

## Step 1: Create Observable Account and Notebook

1. **Go to Observable**: https://observablehq.com/
2. **Create free account** (if you don't have one)
3. **Fork the template**: https://observablehq.com/d/41ca4f33b9a5a2ff
4. **Keep notebook UNLISTED** during development (as recommended by Zindi)

## Step 2: Upload Your Data Files

Upload these files to your Observable notebook's file attachments:
- `risk_assessment_complete.csv`
- `country_summary.csv` 
- `risk_hotspots.csv`
- `soil_health_indicators.csv`
- `dataset_metadata.json`
- `dashboard_stats.json`

## Step 3: Build the Notebook Following This Structure

Copy and paste the cells below into your Observable notebook:

---

## CELL 1: Title and Introduction (Markdown)
```markdown
# Vulnerable Ground: Climate Risk and Soil Health in Sub-Saharan Africa
## A Data-Driven Call to Action for Climate Adaptation

This is the story of **213 million people** in Sub-Saharan Africa standing on vulnerable ground—literally and figuratively—as climate change threatens the very soil beneath their feet.

Our analysis transforms complex geospatial data into a human-centered call for urgent, targeted action, revealing where climate adaptation resources can have maximum impact.

### Our 4-Part Narrative Arc

1. **The Vulnerable Ground** - Current soil health and social vulnerability baseline
2. **The Coming Storm** - Future climate projections overlaid on vulnerability  
3. **The Human Cost** - Quantified population and economic exposure
4. **The Path Forward** - Evidence-based investment strategy with clear ROI

---

**Key Finding**: A targeted investment of $1B can protect $23.74B in agricultural value through strategic allocation across 1,037 high-risk areas.
```

## CELL 2: Data Loading (JavaScript)
```javascript
// Load the datasets
riskData = FileAttachment("risk_assessment_complete.csv").csv({typed: true})
countryData = FileAttachment("country_summary.csv").csv({typed: true})
hotspotsData = FileAttachment("risk_hotspots.csv").csv({typed: true})
soilData = FileAttachment("soil_health_indicators.csv").csv({typed: true})
metadata = FileAttachment("dataset_metadata.json").json()
```

## CELL 3: Key Metrics Display (JavaScript)
```javascript
// Calculate key metrics
keyMetrics = {
  totalAreas: riskData.length,
  countries: new Set(riskData.map(d => d.country)).size,
  highRiskAreas: riskData.filter(d => d.risk_category === "Very High").length,
  peopleAtRisk: d3.sum(riskData.filter(d => d.risk_category === "Very High"), d => d.population),
  agriculturalValue: d3.sum(riskData.filter(d => d.risk_category === "Very High"), d => d.vop_crops_usd),
  roiMultiplier: 23.74
}
```

## CELL 4: Metrics Dashboard (HTML)
```javascript
html`<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0;">
  <div style="background: #f0fdf4; padding: 20px; border-radius: 8px; border-left: 4px solid #16a34a;">
    <h3 style="color: #166534; margin: 0; font-size: 1.8em;">${keyMetrics.totalAreas.toLocaleString()}</h3>
    <p style="margin: 5px 0 0 0; color: #666;">Sub-regions analyzed across ${keyMetrics.countries} countries</p>
  </div>
  <div style="background: #fef3c7; padding: 20px; border-radius: 8px; border-left: 4px solid #f59e0b;">
    <h3 style="color: #92400e; margin: 0; font-size: 1.8em;">${(keyMetrics.peopleAtRisk / 1000000).toFixed(0)}M+</h3>
    <p style="margin: 5px 0 0 0; color: #666;">People in high-risk areas</p>
  </div>
  <div style="background: #fee2e2; padding: 20px; border-radius: 8px; border-left: 4px solid #ef4444;">
    <h3 style="color: #dc2626; margin: 0; font-size: 1.8em;">$${(keyMetrics.agriculturalValue / 1000000000).toFixed(1)}B</h3>
    <p style="margin: 5px 0 0 0; color: #666;">Agricultural value at risk</p>
  </div>
  <div style="background: #ecfdf5; padding: 20px; border-radius: 8px; border-left: 4px solid #10b981;">
    <h3 style="color: #047857; margin: 0; font-size: 1.8em;">${keyMetrics.roiMultiplier}x</h3>
    <p style="margin: 5px 0 0 0; color: #666;">Return on investment</p>
  </div>
</div>`
```

## CELL 5: Part 1 - The Vulnerable Ground (Markdown)
```markdown
# Part 1: The Vulnerable Ground

Our story begins with the foundation: the soil itself and the communities that depend on it. We analyzed environmental and social vulnerability across Sub-Saharan Africa to establish the baseline conditions.

## Environmental Vulnerability: Where the Soil is Fragile

Using SoilGrids data, we mapped key soil constraints:
- **Low organic carbon** content (poor fertility)
- **Soil acidity** (pH constraints)  
- **High erosion risk** (structural degradation)

## Social Vulnerability: Where People Have Least Capacity to Adapt

Using Adaptation Atlas poverty data, we identified communities with:
- **High poverty rates** (limited economic resilience)
- **Low adaptive capacity** (insufficient resources for climate adaptation)
- **Limited infrastructure** (poor access to markets and services)

**Key Insight**: Environmental degradation and poverty cluster together—this isn't coincidence, it's environmental injustice that data can help address.
```

## CELL 6: Vulnerability Visualization (JavaScript)
```javascript
Plot.plot({
  title: "Combined Vulnerability Distribution",
  subtitle: "Environmental and social vulnerability across Sub-Saharan Africa",
  width: 800,
  height: 400,
  color: {
    type: "threshold",
    scheme: "YlOrRd",
    domain: [0.2, 0.4, 0.6, 0.8],
    label: "Combined Vulnerability Score"
  },
  marks: [
    Plot.rectY(riskData, Plot.binX({y: "count"}, {
      x: "combined_vulnerability_score",
      fill: "combined_vulnerability_score",
      thresholds: 20
    })),
    Plot.ruleY([0])
  ]
})
```

## Continue with similar structure for Parts 2, 3, and 4...

## Final Export Instructions

Once your notebook is complete:

1. **Install Notebook Kit**:
   ```bash
   npm add @observablehq/notebook-kit
   ```

2. **Export to HTML**:
   ```bash
   notebook-kit download "https://observablehq.com/d/YOUR-NOTEBOOK-ID" > yourusername_track_3.html
   ```

3. **Submit the HTML file** to Zindi platform

## Zindi Scoring Criteria

**Phase 1 (25% each)**:
- ✅ Format and layout: Following template structure
- ✅ Graphs and visualizations: Complete and accurate charts
- ✅ Completeness: Answering all critical questions
- ✅ Narrative arc: Telling a compelling story

**Phase 2 (Top 10 only)**:
- ✅ Relevance (40%): Addressing questions effectively
- ✅ Usability (20%): Easy for stakeholders to use
- ✅ Creativity (20%): Creative thought process and storytelling
- ✅ Aesthetics (20%): Successful visualizations and coherent story