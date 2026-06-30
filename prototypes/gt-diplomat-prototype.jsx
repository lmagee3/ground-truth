import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from "recharts";

// ═══════════════════════════════════════════════════════════
// GROUND TRUTH DIPLOMAT — UI/UX Prototype
// "The Palantir for Peace"
// Mock data — no live APIs. Design exploration only.
// ═══════════════════════════════════════════════════════════

const COLORS = {
  bg: "#0a0e17",
  bgCard: "#111827",
  bgPanel: "#0d1321",
  border: "#1e293b",
  borderLight: "#334155",
  text: "#e2e8f0",
  textMuted: "#94a3b8",
  textDim: "#64748b",
  accent: "#10b981",
  accentDim: "#065f46",
  danger: "#ef4444",
  dangerDim: "#7f1d1d",
  warning: "#f59e0b",
  warningDim: "#78350f",
  info: "#3b82f6",
  infoDim: "#1e3a5f",
  trade: "#06b6d4",
  diplomatic: "#a78bfa",
  aid: "#fbbf24",
};

// ── Mock Data ──────────────────────────────────────────────

const COUNTRIES = {
  UKR: {
    name: "Ukraine", iso: "UKR", region: "Eastern Europe",
    temperature: 87, tempLabel: "Critical",
    coords: { lat: 48.3794, lng: 31.1656 },
    population: "43.8M", gdp: "$160.5B", regime: "Semi-Presidential Republic",
    conflictEvents: 14823, displaced: "6.3M internally, 6.2M refugees",
    briefing: "Ongoing armed conflict since February 2022. Russian Federation forces occupy approximately 18% of internationally recognized Ukrainian territory. Multiple rounds of peace negotiations have stalled. Western military aid continues at scale. Energy infrastructure repeatedly targeted.",
    religiousLandscape: "Orthodox Christian majority (split between Kyiv and Moscow patriarchates), growing Ukrainian Orthodox Church of Ukraine (OCU) since autocephaly in 2019",
    politicalSpectrum: "Pro-European, democratic reform trajectory. Martial law since Feb 2022.",
    spoilers: [
      { name: "Wagner Group remnants", capability: "High", negotiate: "None", backers: "Russian Federation" },
      { name: "Donetsk/Luhansk separatists", capability: "Medium", negotiate: "Low", backers: "Russian Federation" },
    ],
    frictionScore: 92,
    tradeDeps: [
      { partner: "EU", volume: "$46.2B", type: "Export: grain, metals" },
      { partner: "China", volume: "$15.3B", type: "Import: electronics, machinery" },
      { partner: "Turkey", volume: "$7.8B", type: "Bilateral: grain corridor" },
    ],
    treaties: ["UN Member", "EU Association Agreement", "NATO Enhanced Opportunity Partner"],
    aidFlows: [
      { donor: "United States", amount: "$75B+", type: "Military + economic" },
      { donor: "European Union", amount: "$50B+", type: "Economic + humanitarian" },
      { donor: "United Kingdom", amount: "$12B+", type: "Military + training" },
    ],
  },
  ETH: {
    name: "Ethiopia", iso: "ETH", region: "East Africa",
    temperature: 68, tempLabel: "Elevated",
    coords: { lat: 9.145, lng: 40.4897 },
    population: "126.5M", gdp: "$126.8B", regime: "Federal Parliamentary Republic",
    conflictEvents: 3241, displaced: "4.6M internally",
    briefing: "Post-Tigray War ceasefire holding since November 2022 (Pretoria Agreement). Ongoing ethnic tensions in Amhara and Oromia regions. Grand Ethiopian Renaissance Dam (GERD) dispute with Egypt and Sudan creates regional friction. Food insecurity affecting 20M+ people.",
    religiousLandscape: "Ethiopian Orthodox Tewahedo (43%), Islam (34%), Protestant (19%). Religious tensions historically low but rising along ethnic fault lines.",
    politicalSpectrum: "Authoritarian-leaning federal system under PM Abiy Ahmed. Nobel Peace Prize 2019, then led Tigray offensive 2020-2022.",
    spoilers: [
      { name: "Fano militia (Amhara)", capability: "Medium", negotiate: "Low", backers: "Domestic" },
      { name: "OLA (Oromo Liberation Army)", capability: "Medium", negotiate: "Medium", backers: "Domestic/diaspora" },
      { name: "TPLF (remnants)", capability: "Low", negotiate: "Medium", backers: "Domestic" },
    ],
    frictionScore: 64,
    tradeDeps: [
      { partner: "China", volume: "$3.8B", type: "Import: machinery, electronics" },
      { partner: "EU", volume: "$1.9B", type: "Export: coffee, textiles" },
      { partner: "Saudi Arabia", volume: "$1.2B", type: "Import: petroleum" },
    ],
    treaties: ["AU Founding Member", "IGAD", "AfCFTA"],
    aidFlows: [
      { donor: "United States", amount: "$1.8B", type: "Humanitarian + development" },
      { donor: "World Bank", amount: "$4.2B portfolio", type: "Development" },
      { donor: "EU", amount: "$1.1B", type: "Humanitarian" },
    ],
  },
  TWN: {
    name: "Taiwan", iso: "TWN", region: "East Asia",
    temperature: 58, tempLabel: "Moderate",
    coords: { lat: 23.6978, lng: 120.9605 },
    population: "23.6M", gdp: "$790.7B", regime: "Semi-Presidential Republic",
    conflictEvents: 0, displaced: "N/A",
    briefing: "Cross-strait tensions elevated since 2022. PRC military exercises around Taiwan increasing in frequency. U.S. arms sales continue under Taiwan Relations Act. Semiconductor dominance (TSMC) gives Taiwan outsized geostrategic leverage. No armed conflict but highest risk of great-power escalation globally.",
    religiousLandscape: "Buddhism/Taoism syncretic majority (80%+), Christianity (~5%). Religion not a significant conflict driver.",
    politicalSpectrum: "Vibrant multi-party democracy. DPP (pro-sovereignty) holds presidency. KMT (pro-engagement with PRC) in opposition.",
    spoilers: [
      { name: "PRC military posturing", capability: "Very High", negotiate: "Low", backers: "State actor (PRC)" },
    ],
    frictionScore: 71,
    tradeDeps: [
      { partner: "China/HK", volume: "$186B", type: "Export: semiconductors" },
      { partner: "United States", volume: "$100B+", type: "Bilateral: tech, defense" },
      { partner: "Japan", volume: "$75B", type: "Bilateral: electronics, machinery" },
    ],
    treaties: ["Unofficial U.S. defense commitment (TRA)", "APEC member", "WTO member"],
    aidFlows: [
      { donor: "Taiwan (outbound)", amount: "$300M+", type: "Development aid to allies" },
    ],
  },
};

const SCENARIOS_UKR = [
  {
    id: 1,
    title: "Ceasefire + Frozen Conflict",
    type: "Diplomatic Channel",
    feasibility: 42,
    timeline: "6-12 months",
    risk: "High",
    confidence: 58,
    description: "Negotiate ceasefire along current contact line. Territory disputes deferred to future negotiations. Model: Korean Peninsula armistice.",
    dependencies: ["Russian willingness to negotiate", "Western security guarantees for Ukraine", "Domestic political support in both nations"],
    risks: ["Legitimizes territorial seizure", "No resolution of sovereignty questions", "Spoiler risk from hardliners on both sides"],
    precedent: "Korean War Armistice (1953) — 70+ year frozen conflict, no peace treaty"
  },
  {
    id: 2,
    title: "Economic Interdependency Bridge",
    type: "Trade Bridge",
    feasibility: 18,
    timeline: "3-5 years",
    risk: "Very High",
    confidence: 31,
    description: "Rebuild economic ties through energy transit agreements and grain export frameworks. Create mutual economic dependencies that raise cost of continued conflict.",
    dependencies: ["Sanctions framework modification", "Energy infrastructure rebuilding", "Third-party guarantors (Turkey, China)"],
    risks: ["Premature normalization without justice", "Sanction fatigue in Western bloc", "Russian non-compliance history"],
    precedent: "Franco-German Coal and Steel Community (1951) → EU"
  },
  {
    id: 3,
    title: "Multilateral Security Framework",
    type: "Security Guarantee",
    feasibility: 28,
    timeline: "2-4 years",
    risk: "High",
    confidence: 44,
    description: "International security guarantees for Ukraine outside NATO framework. Potential guarantors: US, UK, France, Turkey, China. Binding commitments with enforcement mechanisms.",
    dependencies: ["Russian acceptance of framework", "Chinese participation as guarantor", "Defined enforcement triggers"],
    risks: ["Untested framework", "Guarantor credibility questions", "Nuclear escalation risk during negotiations"],
    precedent: "Budapest Memorandum (1994) — failed; new framework must address enforcement gaps"
  },
];

const EARLY_WARNING = [
  { month: "Oct", food: 62, displacement: 45, governance: 38, arms: 71, conflict: 82 },
  { month: "Nov", food: 65, displacement: 48, governance: 36, arms: 74, conflict: 79 },
  { month: "Dec", food: 71, displacement: 52, governance: 34, arms: 78, conflict: 84 },
  { month: "Jan", food: 74, displacement: 58, governance: 32, arms: 80, conflict: 88 },
  { month: "Feb", food: 68, displacement: 61, governance: 31, arms: 76, conflict: 91 },
  { month: "Mar", food: 72, displacement: 64, governance: 29, arms: 82, conflict: 86 },
];

const GLOBE_HOTSPOTS = [
  { name: "Gaza", x: 150, y: 192, temp: 94, color: COLORS.danger },
  { name: "Yemen", x: 289, y: 424, temp: 85, color: COLORS.danger },
  { name: "Sudan", x: 86, y: 400, temp: 82, color: COLORS.danger },
  { name: "Syria", x: 176, y: 164, temp: 78, color: COLORS.danger },
  { name: "Iraq", x: 279, y: 171, temp: 72, color: COLORS.warning },
  { name: "Iran", x: 414, y: 186, temp: 76, color: COLORS.danger },
  { name: "Ethiopia", x: 214, y: 470, temp: 68, color: COLORS.warning },
  { name: "Nagorno-K.", x: 325, y: 74, temp: 48, color: COLORS.warning },
  { name: "Afghanistan", x: 600, y: 164, temp: 79, color: COLORS.danger },
  { name: "Pakistan", x: 629, y: 243, temp: 55, color: COLORS.warning },
  { name: "Hormuz Strait", x: 464, y: 271, temp: 62, color: COLORS.warning },
  { name: "Red Sea", x: 171, y: 329, temp: 70, color: COLORS.warning },
];

const TRADE_ROUTES = [
  { x1: 291, y1: 167, x2: 414, y2: 186 },
  { x1: 325, y1: 290, x2: 434, y2: 294 },
  { x1: 103, y1: 214, x2: 176, y2: 164 },
  { x1: 645, y1: 150, x2: 701, y2: 162 },
  { x1: 414, y1: 186, x2: 464, y2: 271 },
];

// ── Enhanced Map Data (Natural Earth 110m) ─────────────────

const DISTANT_PATHS = [
  "M905.1,-60.2 L894.3,-50.7 L882.4,-49.4 L881.7,-35.0 L873.8,-28.6 L845.4,-33.3 L835.1,-7.7 L827.8,-4.5 L799.5,1.2 L812.4,26.0 L802.6,29.7 L803.7,37.9 L794.9,35.8 L787.7,30.6 L766.5,29.1 L742.9,28.7 L737.7,30.3 L717.3,24.3 L709.2,27.3 L707.0,35.7 L683.5,30.8 L674.1,32.8 L670.9,39.1 L662.7,41.7 L643.9,51.7 L637.6,61.9 L632.3,62.0 L628.4,55.2 L610.2,54.7 L607.3,43.0 L600.3,42.9 L601.4,28.6 L584.3,18.2 L559.8,19.3 L543.0,21.4 L529.4,8.5 L517.7,3.1 L495.6,-7.1 L492.9,-8.4 L456.1,0.1 L456.7,52.7 L449.4,53.4 L439.4,42.2 L429.7,38.2 L413.5,41.2 L407.2,46.0 L406.4,42.5 L409.9,36.5 L407.2,31.5 L390.6,26.7 L384.2,13.8 L376.3,10.2 L375.8,5.6 L389.7,6.9 L390.2,-3.5 L402.4,-5.8 L414.9,-3.7 L417.4,-17.6 L414.9,-26.5 L400.6,-25.8 L388.5,-29.3 L371.9,-23.0 L358.6,-20.0 L351.3,-22.3 L352.8,-29.7 L343.7,-39.2 L333.1,-38.8 L320.9,-48.5 L329.2,-59.3 L325.0,-62.2 L336.4,-77.9 L351.1,-69.6 L352.9,-80.1 L382.4,-95.6 L404.7,-96.0 L436.2,-86.1 L453.1,-80.3 L468.3,-86.3 L490.9,-86.6 L509.2,-79.2 L513.3,-83.5 L533.4,-82.8 L537.0,-89.6 L513.8,-99.4 L527.5,-106.4 L524.9,-110.3 L538.6,-114.0 L528.3,-123.8 L534.8,-128.7 L588.3,-133.6 L595.2,-137.2 L631.0,-142.4 L643.8,-148.4 L669.5,-145.3 L674.0,-130.5 L688.9,-134.0 L707.3,-129.1 L706.1,-121.3 L719.8,-122.1 L755.6,-135.6 L750.4,-131.1 L768.6,-120.1 L800.5,-83.8 L808.1,-91.3 L827.8,-83.0 L848.3,-86.7 L856.2,-84.1 L863.1,-75.9 L873.1,-73.1 L879.2,-67.0 L897.6,-69.0 L905.1,-60.2 Z",
  "M456.7,52.7 L456.1,0.1 L492.9,-8.4 L495.6,-7.1 L517.7,3.1 L529.4,8.5 L543.0,21.4 L559.8,19.3 L584.3,18.2 L601.4,28.6 L600.3,42.9 L607.3,43.0 L610.2,54.7 L628.4,55.2 L632.3,62.0 L637.6,61.9 L643.9,51.7 L662.7,41.7 L670.9,39.1 L675.1,40.5 L663.1,49.7 L673.7,55.1 L683.9,51.5 L700.8,59.1 L682.5,69.3 L671.6,67.9 L665.7,68.3 L663.7,64.3 L666.7,57.7 L647.6,61.0 L643.0,70.2 L636.2,78.1 L624.3,77.4 L620.6,83.7 L631.1,87.1 L634.2,97.8 L626.1,112.2 L615.4,109.2 L607.4,109.1 L607.8,100.4 L588.8,94.2 L573.9,87.3 L564.5,80.5 L548.2,70.7 L541.2,55.9 L536.4,53.3 L520.9,54.0 L515.5,51.1 L513.9,39.7 L494.7,32.1 L482.7,40.4 L470.5,45.3 L472.8,52.5 L456.7,52.7 Z",
  "M251.2,666.9 L242.8,655.1 L242.6,603.1 L255.1,586.9 L259.0,582.4 L268.1,582.1 L280.9,572.0 L299.5,571.4 L339.8,528.5 L349.8,516.6 L356.3,507.8 L356.3,500.4 L356.3,486.0 L356.3,480.1 L356.4,479.8 L356.4,479.8 L361.0,479.6 L367.6,477.4 L375.1,476.0 L381.9,471.1 L387.3,471.1 L387.6,475.0 L386.3,483.3 L386.4,490.8 L383.3,496.0 L379.3,511.4 L372.4,527.4 L363.6,545.6 L351.4,566.6 L339.2,582.6 L322.4,602.1 L308.1,613.6 L286.7,627.8 L273.4,638.7 L257.7,656.0 L254.4,663.5 L251.2,666.9 Z",
  "M8.1,525.3 L-2.8,519.1 L-7.7,514.9 L-8.6,510.5 L-6.3,504.6 L-6.4,498.7 L-14.6,489.8 L-16.2,483.7 L-16.1,480.2 L-21.3,476.0 L-21.5,467.7 L-24.5,462.2 L-29.5,463.0 L-28.0,457.8 L-24.3,451.8 L-26.0,445.9 L-21.3,441.5 L-24.2,438.2 L-20.5,429.4 L-13.9,418.8 L-1.6,419.8 L-2.3,363.1 L-2.1,357.1 L14.3,357.1 L14.3,328.6 L71.7,328.6 L127.1,328.6 L183.8,328.6 L188.4,342.6 L185.3,345.2 L187.4,359.9 L192.6,376.9 L198.0,380.5 L205.9,385.7 L198.6,393.9 L188.1,396.2 L183.6,400.6 L182.2,410.1 L176.0,431.1 L177.6,436.8 L175.3,449.1 L169.5,463.2 L160.9,470.2 L154.7,481.2 L153.3,487.0 L146.5,491.0 L142.3,505.9 L142.5,518.8 L142.3,507.7 L140.4,507.4 L140.6,500.3 L138.9,495.4 L131.5,489.7 L129.8,479.4 L131.5,468.9 L124.9,467.9 L123.9,471.1 L115.3,471.8 L118.8,476.0 L120.0,484.6 L112.2,492.4 L105.0,502.7 L97.7,504.2 L85.7,495.8 L80.3,498.8 L78.8,503.0 L71.4,505.7 L71.0,508.6 L56.7,508.6 L54.8,505.7 L44.5,505.2 L39.3,507.6 L35.4,506.4 L28.0,498.1 L25.6,494.1 L15.3,496.1 L11.4,502.7 L7.7,515.5 L2.8,518.2 L-1.6,519.7 L8.1,525.3 Z",
  "M-2.3,363.1 L-1.6,419.8 L-13.9,418.8 L-20.5,429.4 L-24.2,438.2 L-21.3,441.5 L-26.0,445.9 L-24.3,451.8 L-28.0,457.8 L-29.5,463.0 L-24.5,462.2 L-21.5,467.7 L-21.3,476.0 L-16.1,480.2 L-16.2,483.7 L-25.3,486.1 L-32.5,491.9 L-42.8,507.5 L-56.3,514.1 L-70.1,513.2 L-74.1,514.5 L-72.7,519.6 L-80.1,524.6 L-86.2,530.1 L-104.2,535.6 L-107.8,532.4 L-110.1,532.1 L-112.8,535.8 L-124.6,536.8 L-122.3,533.0 L-126.8,523.1 L-128.9,517.2 L-135.1,514.8 L-143.5,506.4 L-140.4,499.7 L-133.9,501.1 L-129.9,500.1 L-121.9,500.3 L-129.7,487.3 L-129.1,477.8 L-130.1,468.3 L-135.8,459.2 L-134.3,452.4 L-143.5,452.1 L-143.5,442.9 L-149.4,437.6 L-143.3,418.8 L-125.0,405.3 L-124.3,386.7 L-118.8,357.8 L-115.7,351.6 L-121.6,346.7 L-121.8,342.2 L-127.2,338.4 L-130.7,316.2 L-116.3,308.4 L-59.3,335.8 L-2.3,363.1 Z",
  "M167.4,175.6 L164.9,180.1 L159.8,178.1 L156.8,187.6 L160.4,189.2 L156.7,191.2 L156.1,195.0 L162.8,193.0 L163.2,198.6 L156.0,221.4 L154.6,217.7 L146.6,196.9 L146.6,196.9 L146.6,196.9 L150.8,192.2 L149.8,191.3 L153.6,184.7 L156.5,173.9 L158.5,170.3 L158.9,170.1 L163.7,170.2 L165.0,167.7 L168.9,167.5 L169.1,173.3 L167.2,175.5 L167.4,175.6 Z",
  "M168.9,167.5 L165.0,167.7 L163.7,170.2 L158.9,170.1 L164.0,158.5 L171.1,148.4 L171.4,147.9 L177.8,148.7 L180.2,154.3 L172.4,159.6 L168.9,167.5 Z",
  "M164.9,180.1 L167.4,175.6 L183.3,181.2 L211.3,166.0 L217.1,183.4 L214.4,185.6 L185.7,192.7 L200.0,207.0 L195.3,209.4 L192.9,214.2 L182.0,216.2 L178.6,221.4 L172.4,225.8 L156.5,223.5 L156.0,221.4 L163.2,198.6 L162.8,193.0 L164.9,188.8 L164.9,180.1 Z",
  "M626.1,112.2 L634.2,97.8 L631.1,87.1 L620.6,83.7 L624.3,77.4 L636.2,78.1 L643.0,70.2 L647.6,61.0 L666.7,57.7 L663.7,64.3 L665.7,68.3 L671.6,67.9 L666.4,72.3 L650.9,70.0 L649.5,78.2 L665.0,77.1 L682.6,81.7 L709.6,79.6 L713.3,92.8 L718.0,91.3 L726.6,94.6 L726.1,100.1 L728.3,108.3 L713.6,108.3 L703.7,107.2 L694.8,113.6 L688.5,115.0 L683.5,118.0 L677.8,113.3 L679.2,101.3 L674.8,100.7 L676.4,96.3 L668.7,93.1 L662.5,98.0 L661.0,103.8 L658.8,105.9 L650.3,105.6 L645.7,112.1 L640.8,109.4 L630.5,114.0 L626.1,112.2 Z",
  "M670.9,39.1 L674.1,32.8 L683.5,30.8 L707.0,35.7 L709.2,27.3 L717.3,24.3 L737.7,30.3 L742.9,28.7 L766.5,29.1 L787.7,30.6 L794.9,35.8 L803.7,37.9 L801.7,41.1 L779.2,48.8 L774.1,54.5 L755.8,56.2 L750.4,65.3 L735.3,63.4 L725.4,66.2 L711.7,72.9 L713.7,76.3 L709.6,79.6 L682.6,81.7 L665.0,77.1 L649.5,78.2 L650.9,70.0 L666.4,72.3 L671.6,67.9 L682.5,69.3 L700.8,59.1 L683.9,51.5 L673.7,55.1 L663.1,49.7 L675.1,40.5 L670.9,39.1 Z",
  "M167.4,175.6 L167.2,175.5 L169.1,173.3 L168.9,167.5 L172.4,159.6 L180.2,154.3 L177.8,148.7 L171.4,147.9 L170.1,137.0 L173.6,131.1 L177.4,128.0 L181.2,124.9 L182.0,116.9 L186.7,119.7 L202.4,115.7 L210.0,118.4 L221.8,118.3 L238.2,113.0 L245.9,113.2 L262.1,111.0 L254.8,119.9 L247.0,123.4 L248.3,133.9 L242.9,151.2 L211.3,166.0 L183.3,181.2 L167.4,175.6 Z",
  "M-19.2,10.9 L-15.1,16.8 L-9.5,15.8 L1.4,18.0 L22.4,18.7 L29.5,15.1 L46.3,11.8 L56.7,17.0 L65.1,18.5 L57.7,24.4 L52.5,34.6 L57.1,42.8 L44.8,40.8 L30.2,45.3 L30.1,52.4 L17.1,53.8 L7.0,48.8 L-4.4,52.7 L-15.0,52.3 L-16.0,42.9 L-23.1,38.3 L-20.8,36.3 L-22.3,34.6 L-19.9,30.0 L-14.5,25.6 L-21.4,19.4 L-22.7,14.2 L-19.2,10.9 Z",
  "M32.7,138.6 L30.9,142.8 L10.4,144.0 L10.5,141.6 L-6.9,138.9 L-4.3,132.8 L3.5,137.6 L14.6,136.8 L25.3,137.8 L24.9,140.3 L32.7,138.6 Z M-15.0,52.3 L-4.4,52.7 L7.0,48.8 L17.1,53.8 L30.1,52.4 L30.2,45.3 L37.2,49.1 L32.8,58.1 L29.4,59.7 L20.7,59.2 L13.2,57.9 L-4.1,61.6 L5.8,69.6 L-1.4,72.0 L-9.4,72.0 L-16.9,64.6 L-19.6,67.8 L-16.4,76.3 L-9.3,83.0 L-14.7,86.1 L-6.7,92.7 L0.4,96.9 L0.6,104.9 L-12.6,101.1 L-8.4,108.4 L-17.5,109.9 L-12.1,122.5 L-21.6,122.7 L-33.3,116.5 L-38.6,105.1 L-41.1,95.6 L-46.7,89.0 L-54.0,80.9 L-55.0,76.8 L-48.4,69.9 L-47.5,65.2 L-42.9,63.1 L-42.6,59.4 L-33.2,58.1 L-27.8,55.0 L-20.0,55.3 L-17.7,52.8 L-15.0,52.3 Z",
  "M227.9,22.4 L229.7,20.7 L241.7,23.1 L262.8,25.4 L282.2,32.3 L284.7,34.9 L293.4,32.7 L306.7,35.7 L311.1,41.5 L320.1,44.8 L316.4,46.8 L323.4,54.5 L321.5,56.2 L313.8,55.4 L303.1,51.3 L299.6,53.6 L279.8,55.8 L266.0,48.8 L250.8,49.5 L252.9,43.4 L249.3,33.6 L241.1,28.4 L233.2,26.7 L227.9,22.4 Z",
  "M177.6,436.8 L176.0,431.1 L182.2,410.1 L183.6,400.6 L188.1,396.2 L198.6,393.9 L205.9,385.7 L214.2,402.3 L218.1,415.4 L225.9,422.3 L245.4,435.8 L253.4,444.0 L261.1,452.2 L265.6,457.1 L272.6,461.4 L268.3,464.9 L262.2,463.7 L257.3,459.1 L251.4,450.7 L245.1,446.1 L241.4,441.2 L228.9,435.4 L219.2,435.3 L215.7,432.3 L207.3,435.6 L198.7,429.2 L194.2,439.8 L177.6,436.8 Z",
  "M400.0,371.4 L411.2,395.0 L415.8,405.0 L405.5,408.8 L402.7,415.2 L402.4,420.0 L388.2,426.1 L365.4,432.7 L352.6,442.8 L346.3,443.6 L342.0,442.8 L333.6,448.7 L324.5,451.4 L312.5,452.2 L308.9,453.0 L305.8,456.8 L302.1,457.8 L299.9,461.4 L292.8,461.1 L288.2,463.1 L278.3,462.3 L274.6,454.0 L275.0,446.2 L272.7,442.0 L269.9,431.4 L265.8,425.5 L268.6,424.8 L267.2,418.3 L268.9,415.5 L268.3,409.3 L274.5,404.8 L273.1,398.7 L276.9,391.7 L282.7,395.4 L286.6,394.1 L303.1,393.8 L305.7,395.2 L319.5,396.7 L325.0,396.0 L328.6,400.7 L335.2,398.3 L345.5,383.3 L358.8,376.9 L400.0,371.4 Z",
  "M124.7,140.9 L127.4,141.6 L131.3,140.4 L134.1,140.5 L135.1,141.4 L135.4,142.9 L136.1,142.3 L138.2,142.6 L140.9,141.5 L142.5,142.0 L142.9,143.2 L128.3,149.0 L121.3,147.1 L118.0,141.4 L124.7,140.9 Z",
  "M183.8,328.6 L127.1,328.6 L71.7,328.6 L14.3,328.6 L14.3,276.0 L14.3,225.2 L10.0,213.7 L13.7,204.8 L11.5,198.7 L16.6,191.9 L35.6,191.6 L49.4,195.4 L63.6,199.6 L70.2,201.9 L81.2,197.3 L87.1,193.2 L99.7,192.1 L109.8,193.9 L113.7,200.9 L117.0,196.3 L128.5,199.7 L139.6,200.5 L146.6,196.9 L146.6,196.9 L154.6,217.7 L156.0,221.4 L152.0,227.2 L149.0,237.9 L145.1,245.4 L141.7,247.9 L137.0,243.3 L130.5,236.9 L120.3,216.4 L118.9,217.7 L124.8,232.8 L133.6,247.1 L144.4,269.4 L149.6,277.2 L154.2,285.2 L167.0,301.0 L164.2,303.5 L164.7,312.8 L181.3,325.6 L183.8,328.6 Z",
  "M14.3,328.6 L14.3,357.1 L-2.1,357.1 L-2.3,363.1 L-59.3,335.8 L-116.3,308.4 L-130.7,316.2 L-140.8,321.6 L-148.8,313.7 L-171.4,307.5 L-177.7,298.6 L-189.0,292.0 L-195.7,294.6 L-200.7,286.6 L-201.3,280.5 L-209.7,270.1 L-204.1,264.1 L-205.3,255.1 L-203.5,247.3 L-204.5,240.8 L-202.0,229.1 L-202.8,222.5 L-207.4,209.9 L-200.4,206.6 L-199.2,200.5 L-200.7,194.6 L-190.9,189.1 L-186.5,184.5 L-179.5,180.4 L-178.7,169.5 L-162.0,174.4 L-156.0,173.2 L-144.0,175.5 L-125.1,181.9 L-118.4,194.6 L-105.5,197.4 L-85.4,203.4 L-70.2,210.5 L-63.2,206.8 L-56.4,200.2 L-59.7,189.3 L-55.2,182.3 L-44.9,175.6 L-35.1,173.7 L-15.8,176.6 L-10.9,183.0 L-5.6,183.0 L-1.0,185.5 L13.2,187.2 L16.6,191.9 L11.5,198.7 L13.7,204.8 L10.0,213.7 L14.3,225.2 L14.3,276.0 L14.3,328.6 Z",
  "M339.8,528.5 L299.5,571.4 L280.9,572.0 L268.1,582.1 L259.0,582.4 L255.1,586.9 L245.3,586.9 L239.5,582.0 L226.5,588.0 L222.3,594.0 L212.8,592.8 L209.6,591.2 L206.2,591.6 L201.7,591.4 L183.6,579.3 L173.7,579.3 L168.8,574.6 L168.8,566.6 L161.4,564.2 L153.0,548.7 L146.4,545.3 L143.9,539.6 L136.7,532.7 L127.9,531.6 L132.8,523.5 L140.4,523.2 L142.5,518.8 L142.3,505.9 L146.5,491.0 L153.3,487.0 L154.7,481.2 L160.9,470.2 L169.5,463.2 L175.3,449.1 L177.6,436.8 L194.2,439.8 L198.7,429.2 L207.3,435.6 L215.7,432.3 L219.2,435.3 L228.9,435.4 L241.4,441.2 L245.1,446.1 L251.4,450.7 L257.3,459.1 L262.2,463.7 L257.1,470.0 L252.3,476.7 L253.4,480.6 L253.7,485.0 L261.6,485.2 L265.1,484.2 L268.2,486.8 L265.1,491.8 L270.4,499.7 L275.7,506.6 L281.1,511.7 L327.8,528.6 L339.8,528.5 Z",
  "M262.2,463.7 L268.3,464.9 L272.6,461.4 L276.0,465.9 L275.5,471.8 L267.4,475.2 L273.5,479.1 L268.2,486.8 L265.1,484.2 L261.6,485.2 L253.7,485.0 L253.4,480.6 L252.3,476.7 L257.1,470.0 L262.2,463.7 Z",
];

const NEIGHBOR_PATHS = [
  "M217.1,183.4 L211.3,166.0 L242.9,151.2 L248.3,133.9 L247.0,123.4 L254.8,119.9 L262.1,111.0 L268.3,108.8 L284.9,110.6 L289.9,114.3 L296.8,111.9 L306.0,128.9 L315.4,133.2 L316.5,141.5 L309.3,146.5 L306.0,157.6 L315.8,171.2 L333.4,179.0 L340.7,189.9 L338.4,200.2 L342.9,200.2 L343.1,207.8 L351.0,215.3 L342.5,214.6 L332.9,213.4 L322.4,227.2 L295.8,226.0 L255.6,197.3 L234.3,187.3 L217.1,183.4 Z",
  "M296.8,111.9 L289.9,114.3 L284.9,110.6 L268.3,108.8 L262.1,111.0 L245.9,113.2 L238.2,113.0 L221.8,118.3 L210.0,118.4 L202.4,115.7 L186.7,119.7 L182.0,116.9 L181.2,124.9 L177.4,128.0 L173.6,131.1 L168.3,124.6 L173.7,119.3 L165.0,120.5 L153.1,117.2 L143.2,125.4 L121.6,127.0 L110.0,119.4 L94.6,118.9 L91.3,124.8 L81.4,126.5 L67.6,118.9 L52.0,119.2 L43.6,105.0 L33.1,97.0 L40.1,85.9 L31.0,79.1 L46.9,65.4 L68.9,64.9 L74.9,54.0 L102.1,55.9 L119.3,46.6 L135.9,42.6 L159.5,42.3 L184.5,52.4 L205.0,57.9 L221.6,55.7 L233.9,56.9 L250.8,49.5 L266.0,48.8 L279.8,55.8 L282.2,60.9 L280.8,67.8 L291.4,71.4 L297.1,75.5 L287.3,79.6 L291.7,96.0 L288.9,100.4 L296.8,111.9 L296.8,111.9 Z M30.2,45.3 L44.8,40.8 L57.1,42.8 L58.8,48.2 L71.3,52.9 L68.7,56.4 L51.7,57.1 L45.6,61.6 L33.7,69.3 L29.2,62.6 L29.4,59.7 L32.8,58.1 L37.2,49.1 L30.2,45.3 Z",
  "M607.4,109.1 L615.4,109.2 L626.1,112.2 L630.5,114.0 L640.8,109.4 L645.7,112.1 L650.3,105.6 L658.8,105.9 L661.0,103.8 L662.5,98.0 L668.7,93.1 L676.4,96.3 L674.8,100.7 L679.2,101.3 L677.8,113.3 L683.5,118.0 L688.5,115.0 L694.8,113.6 L703.7,107.2 L713.6,108.3 L728.3,108.3 L730.8,112.4 L722.5,114.0 L715.3,116.6 L698.9,118.3 L683.5,121.3 L675.2,127.5 L678.6,133.6 L680.2,140.7 L673.1,146.7 L673.7,152.2 L669.7,157.3 L656.2,156.9 L661.8,166.3 L652.7,169.9 L646.6,178.5 L647.4,187.1 L641.8,191.1 L636.5,189.8 L625.6,191.7 L624.0,195.7 L613.4,195.6 L605.4,203.7 L604.9,215.9 L586.4,221.8 L576.4,220.6 L573.5,223.7 L565.0,221.9 L550.7,224.0 L526.8,216.7 L539.7,203.8 L538.6,194.6 L527.7,192.2 L526.6,183.1 L521.9,171.7 L528.1,163.9 L521.8,161.8 L525.8,151.4 L531.6,133.6 L546.2,139.0 L556.9,137.1 L559.9,130.6 L571.2,128.5 L579.2,124.1 L582.1,112.7 L594.1,109.9 L596.4,104.8 L603.1,108.7 L607.4,109.1 Z",
  "M769.1,135.8 L755.3,147.8 L739.4,149.9 L717.7,146.4 L710.7,152.6 L715.8,165.1 L720.7,174.8 L732.3,181.8 L720.1,190.1 L720.3,200.3 L706.4,214.6 L697.5,229.1 L682.5,244.1 L665.9,243.0 L650.2,258.0 L659.6,264.4 L661.2,275.4 L669.2,282.6 L672.0,294.9 L640.6,294.9 L631.1,304.4 L620.6,300.8 L616.4,290.5 L605.3,279.6 L579.0,282.3 L555.8,282.6 L535.7,284.6 L541.1,268.0 L561.7,260.6 L560.5,254.0 L553.6,251.7 L553.3,239.1 L539.6,232.9 L533.8,224.2 L526.8,216.7 L550.7,224.0 L565.0,221.9 L573.5,223.7 L576.4,220.6 L586.4,221.8 L604.9,215.9 L605.4,203.7 L613.4,195.6 L624.0,195.7 L625.6,191.7 L636.5,189.8 L641.8,191.1 L647.4,187.1 L646.6,178.5 L652.7,169.9 L661.8,166.3 L656.2,156.9 L669.7,157.3 L673.7,152.2 L673.1,146.7 L680.2,140.7 L678.6,133.6 L675.2,127.5 L683.5,121.3 L698.9,118.3 L715.3,116.6 L722.5,114.0 L730.8,112.4 L741.4,119.0 L745.6,130.0 L769.1,135.8 Z",
  "M407.2,46.0 L413.5,41.2 L429.7,38.2 L439.4,42.2 L449.4,53.4 L456.7,52.7 L472.8,52.5 L470.5,45.3 L482.7,40.4 L494.7,32.1 L513.9,39.7 L515.5,51.1 L520.9,54.0 L536.4,53.3 L541.2,55.9 L548.2,70.7 L564.5,80.5 L573.9,87.3 L588.8,94.2 L607.8,100.4 L607.4,109.1 L603.1,108.7 L596.4,104.8 L594.1,109.9 L582.1,112.7 L579.2,124.1 L571.2,128.5 L559.9,130.6 L556.9,137.1 L546.2,139.0 L531.6,133.6 L530.3,121.5 L519.7,121.0 L503.4,108.4 L491.9,106.8 L476.1,99.6 L466.0,98.3 L459.7,100.9 L450.2,100.5 L440.0,108.7 L427.5,111.4 L424.8,101.3 L426.9,86.4 L415.7,81.6 L419.4,71.8 L409.9,70.9 L413.1,58.9 L426.5,62.4 L439.1,57.8 L428.7,49.3 L424.6,41.1 L413.1,44.7 L411.6,55.2 L407.2,46.0 Z",
  "M320.1,44.8 L324.1,45.3 L333.9,54.0 L340.2,55.0 L342.7,51.3 L351.2,45.6 L358.7,53.1 L366.0,63.2 L372.6,63.9 L377.0,67.8 L365.3,68.9 L362.8,80.0 L360.3,85.0 L355.1,88.4 L355.5,95.4 L351.9,96.1 L343.0,88.7 L347.9,81.6 L343.7,77.4 L338.4,78.5 L321.5,89.0 L321.2,79.1 L314.8,76.7 L308.7,72.9 L312.7,68.3 L305.1,63.4 L308.0,59.8 L302.6,57.4 L299.6,53.6 L303.1,51.3 L313.8,55.4 L321.5,56.2 L323.4,54.5 L316.4,46.8 L320.1,44.8 Z M316.3,89.4 L306.5,87.5 L299.3,80.9 L297.1,75.5 L300.0,75.1 L304.3,79.0 L310.6,78.9 L310.5,81.1 L316.3,89.4 Z",
  "M321.5,89.0 L316.3,89.4 L310.5,81.1 L310.6,78.9 L304.3,79.0 L300.0,75.1 L297.1,75.5 L291.4,71.4 L280.8,67.8 L282.2,60.9 L279.8,55.8 L299.6,53.6 L302.6,57.4 L308.0,59.8 L305.1,63.4 L312.7,68.3 L308.7,72.9 L314.8,76.7 L321.2,79.1 L321.5,89.0 Z",
  "M342.5,214.6 L345.5,220.9 L344.2,224.2 L348.8,235.0 L338.7,235.3 L335.1,228.5 L322.4,227.2 L332.9,213.4 L342.5,214.6 Z",
  "M156.5,223.5 L172.4,225.8 L178.6,221.4 L182.0,216.2 L192.9,214.2 L195.3,209.4 L200.0,207.0 L185.7,192.7 L214.4,185.6 L217.1,183.4 L234.3,187.3 L255.6,197.3 L295.8,226.0 L322.4,227.2 L335.1,228.5 L338.7,235.3 L348.8,235.0 L354.4,247.3 L361.4,250.6 L363.9,255.6 L373.6,261.6 L374.5,267.5 L373.0,272.2 L374.9,277.0 L379.0,281.0 L380.9,285.7 L383.0,289.2 L387.3,292.1 L391.3,291.0 L394.0,296.5 L394.5,299.8 L400.0,314.3 L443.0,321.5 L445.8,318.5 L452.4,328.6 L442.9,357.1 L400.0,371.4 L358.8,376.9 L345.5,383.3 L335.2,398.3 L328.6,400.7 L325.0,396.0 L319.5,396.7 L305.7,395.2 L303.1,393.8 L286.6,394.1 L282.7,395.4 L276.9,391.7 L273.1,398.7 L274.5,404.8 L268.3,409.3 L266.4,403.2 L262.1,398.9 L261.0,393.2 L253.6,388.1 L246.0,376.1 L242.0,364.5 L232.1,354.6 L225.7,352.3 L216.3,338.7 L214.6,328.8 L215.2,320.3 L207.0,304.5 L200.3,298.9 L192.6,295.9 L187.9,287.7 L188.7,284.5 L184.7,277.1 L180.6,273.9 L175.0,263.3 L166.3,251.8 L159.0,242.0 L151.9,242.0 L154.1,234.2 L154.7,229.2 L156.5,223.5 Z",
  "M394.0,296.5 L396.5,295.8 L397.1,299.7 L408.2,297.5 L420.1,297.8 L428.7,298.3 L438.5,288.6 L449.1,279.4 L458.2,270.6 L460.9,275.5 L462.8,286.8 L455.5,286.8 L454.3,296.1 L456.9,298.1 L450.4,300.9 L450.4,306.8 L446.2,312.7 L445.8,318.5 L443.0,321.5 L400.0,314.3 L394.5,299.8 L394.0,296.5 Z",
  "M383.0,289.2 L382.1,278.8 L385.9,271.3 L389.8,269.8 L394.1,274.3 L394.4,282.6 L391.3,291.0 L387.3,292.1 L383.0,289.2 Z",
  "M445.8,318.5 L446.2,312.7 L450.4,306.8 L450.4,300.9 L456.9,298.1 L454.3,296.1 L455.5,286.8 L462.8,286.8 L469.2,296.5 L477.2,301.7 L487.7,303.6 L496.1,306.2 L502.6,314.4 L506.4,319.1 L511.5,320.9 L511.5,324.1 L506.3,332.6 L504.0,336.7 L498.0,341.2 L492.7,351.0 L486.2,350.3 L483.2,353.7 L480.9,360.9 L482.7,370.5 L481.3,372.2 L474.8,372.2 L465.9,377.5 L464.5,384.5 L461.2,387.5 L452.3,387.4 L446.7,391.0 L446.8,396.7 L439.9,400.7 L432.0,399.4 L422.4,404.2 L415.8,405.0 L411.2,395.0 L400.0,371.4 L442.9,357.1 L452.4,328.6 L445.8,318.5 Z M460.9,275.5 L458.2,270.6 L462.3,265.8 L464.1,267.0 L462.7,272.9 L460.9,275.5 Z",
];

const FOCUS_PATH = "M351.0,215.3 L343.1,207.8 L342.9,200.2 L338.4,200.2 L340.7,189.9 L333.4,179.0 L315.8,171.2 L306.0,157.6 L309.3,146.5 L316.5,141.5 L315.4,133.2 L306.0,128.9 L296.8,111.9 L296.8,111.9 L288.9,100.4 L291.7,96.0 L287.3,79.6 L297.1,75.5 L299.3,80.9 L306.5,87.5 L316.3,89.4 L321.5,89.0 L338.4,78.5 L343.7,77.4 L347.9,81.6 L343.0,88.7 L351.9,96.1 L355.5,95.4 L360.0,106.0 L373.5,108.9 L383.5,116.1 L403.8,118.6 L426.1,114.8 L427.5,111.4 L440.0,108.7 L450.2,100.5 L459.7,100.9 L466.0,98.3 L476.1,99.6 L491.9,106.8 L503.4,108.4 L519.7,121.0 L530.3,121.5 L531.6,133.6 L525.8,151.4 L521.8,161.8 L528.1,163.9 L521.9,171.7 L526.6,183.1 L527.7,192.2 L538.6,194.6 L539.7,203.8 L526.8,216.7 L533.8,224.2 L539.6,232.9 L553.3,239.1 L553.6,251.7 L560.5,254.0 L561.7,260.6 L541.1,268.0 L535.7,284.6 L508.8,280.3 L493.2,277.0 L477.1,275.1 L471.0,257.6 L464.2,255.1 L453.2,257.6 L438.8,264.6 L421.3,259.8 L406.9,248.8 L393.2,244.8 L383.6,231.2 L373.1,212.2 L365.4,214.5 L356.3,209.8 L351.0,215.3 Z";


// ── Components ─────────────────────────────────────────────

function TemperatureGauge({ score, label, size = "lg" }) {
  const getColor = (s) => s >= 75 ? COLORS.danger : s >= 50 ? COLORS.warning : s >= 25 ? COLORS.info : COLORS.accent;
  const color = getColor(score);
  const radius = size === "lg" ? 54 : 32;
  const stroke = size === "lg" ? 7 : 5;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (score / 100) * circ;
  const fontSize = size === "lg" ? "24px" : "14px";
  const labelSize = size === "lg" ? "10px" : "8px";
  const svgSize = size === "lg" ? 130 : 80;

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
      <svg width={svgSize} height={svgSize} viewBox={`0 0 ${svgSize} ${svgSize}`}>
        <circle cx={svgSize/2} cy={svgSize/2} r={radius} fill="none" stroke={COLORS.border} strokeWidth={stroke} />
        <circle cx={svgSize/2} cy={svgSize/2} r={radius} fill="none" stroke={color} strokeWidth={stroke}
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          transform={`rotate(-90 ${svgSize/2} ${svgSize/2})`}
          style={{ transition: "stroke-dashoffset 1s ease" }} />
        <text x={svgSize/2} y={svgSize/2 - 4} textAnchor="middle" fill={color} fontSize={fontSize} fontWeight="700" fontFamily="monospace">{score}</text>
        <text x={svgSize/2} y={svgSize/2 + 14} textAnchor="middle" fill={COLORS.textMuted} fontSize={labelSize} fontFamily="sans-serif">{label}</text>
      </svg>
    </div>
  );
}

function GlobeView({ onSelectCountry }) {
  const [hovered, setHovered] = useState(null);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%", minHeight: 500 }}>
      <svg viewBox="0 0 800 500" style={{ width: "100%", height: "100%", background: "#080d14" }}>
        <defs>
          <radialGradient id="waterGrad" cx="60%" cy="40%">
            <stop offset="0%" stopColor="#0b1320" />
            <stop offset="100%" stopColor="#060a10" />
          </radialGradient>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        <rect width="800" height="500" fill="url(#waterGrad)" />

        {/* Graticule grid */}
        <g opacity={0.25}>
          {[14.3, 85.7, 157.1, 228.6, 300, 371.4, 442.9, 514.3, 585.7, 657.1, 728.6].map(x => (
            <line key={`vg${x}`} x1={x} y1={0} x2={x} y2={500} stroke="#0f1923" strokeWidth={0.5} />
          ))}
          {[71.4, 142.9, 214.3, 285.7, 357.1, 428.6, 500].map(y => (
            <line key={`hg${y}`} x1={0} y1={y} x2={800} y2={y} stroke="#0f1923" strokeWidth={0.5} />
          ))}
        </g>

        {/* Coordinate labels */}
        <g fill="#1e3348" fontFamily="monospace" fontSize={8} opacity={0.5}>
          <text x={85.7} y={496}>30°E</text>
          <text x={228.6} y={496}>40°E</text>
          <text x={371.4} y={496}>50°E</text>
          <text x={514.3} y={496}>60°E</text>
          <text x={657.1} y={496}>70°E</text>
          <text x={4} y={431.6}>15°N</text>
          <text x={4} y={360.1}>20°N</text>
          <text x={4} y={288.7}>25°N</text>
          <text x={4} y={217.3}>30°N</text>
          <text x={4} y={145.9}>35°N</text>
          <text x={4} y={74.4}>40°N</text>
        </g>

        {/* Distant country boundaries */}
        {DISTANT_PATHS.map((d, i) => (
          <path key={`dist${i}`} d={d} fill="#0d1520" stroke="#1e3348" strokeWidth={0.5} opacity={0.7} />
        ))}

        {/* Neighbor country boundaries */}
        {NEIGHBOR_PATHS.map((d, i) => (
          <path key={`nb${i}`} d={d} fill="#111d2a" stroke="#1e3348" strokeWidth={0.7} />
        ))}

        {/* Iran (focus country) */}
        <path d={FOCUS_PATH} fill="#1a2d3d" stroke="#2a5a7a" strokeWidth={1.2} filter="url(#glow)" />

        {/* Shipping lanes */}
        <path d="M457.1,264.3 L464.3,271.4 L471.4,278.6" fill="none" stroke="#c0392b" strokeWidth={1.5} strokeDasharray="8,4" opacity={0.5} />
        <path d="M350,228.6 L378.6,250 L400,264.3 L428.6,271.4 L457.1,264.3" fill="none" stroke="#c0392b" strokeWidth={1.5} strokeDasharray="8,4" opacity={0.5} />
        <path d="M264.3,457.1 L278.6,464.3 L285.7,471.4" fill="none" stroke="#c0392b" strokeWidth={1.5} strokeDasharray="8,4" opacity={0.5} />
        <path d="M121.4,214.3 L142.9,242.9 L171.4,300 L214.3,385.7 L264.3,457.1" fill="none" stroke="#c0392b" strokeWidth={1.5} strokeDasharray="8,4" opacity={0.5} />
        <path d="M471.4,278.6 L514.3,314.3 L585.7,357.1 L657.1,385.7" fill="none" stroke="#c0392b" strokeWidth={1.5} strokeDasharray="8,4" opacity={0.5} />
        <text x={464.3} y={282.9} fill="#c0392b" fontFamily="monospace" fontSize={7} opacity={0.7}>STRAIT OF HORMUZ</text>
        <text x={357.1} y={242.9} fill="#c0392b" fontFamily="monospace" fontSize={6} opacity={0.5}>GULF SHIPPING LANE</text>
        <text x={171.4} y={328.6} fill="#c0392b" fontFamily="monospace" fontSize={6} opacity={0.5}>RED SEA ROUTE</text>
        <text x={271.4} y={478.6} fill="#c0392b" fontFamily="monospace" fontSize={6} opacity={0.5}>BAB EL-MANDEB</text>

        {/* Military installations */}
        {[
          { cx: 379.7, cy: 268.1, label: "US 5th Fleet" },
          { cx: 461, cy: 254.6, label: "Bandar Abbas" },
          { cx: 390.1, cy: 284, label: "Al Udeid" },
          { cx: 163.3, cy: 114.3, label: "Incirlik" },
        ].map((b, i) => (
          <g key={`mil${i}`}>
            <circle cx={b.cx} cy={b.cy} r={5} fill="none" stroke="#f39c12" strokeWidth={1} opacity={0.4}>
              <animate attributeName="r" from="3" to="8" dur="3s" repeatCount="indefinite" />
              <animate attributeName="opacity" from="0.5" to="0" dur="3s" repeatCount="indefinite" />
            </circle>
            <rect x={b.cx - 2.5} y={b.cy - 2.5} width={5} height={5} fill="#f39c12" opacity={0.8} transform={`rotate(45 ${b.cx} ${b.cy})`} />
          </g>
        ))}

        {/* City markers */}
        {[
          { x: 391.3, y: 133, name: "TEHRAN", r: 5, fs: 10, critical: true },
          { x: 291, y: 167, name: "BAGHDAD", r: 3.5, fs: 8, critical: true },
          { x: 324.6, y: 290.1, name: "RIYADH", r: 3, fs: 8 },
          { x: 433.9, y: 293.6, name: "ABU DHABI", r: 2, fs: 7 },
          { x: 393.3, y: 281.6, name: "DOHA", r: 2, fs: 7 },
          { x: 342.6, y: 223.3, name: "KUWAIT CITY", r: 2, fs: 7 },
          { x: 126.6, y: 72.4, name: "ANKARA", r: 3, fs: 8 },
          { x: 103.4, y: 213.7, name: "CAIRO", r: 3, fs: 8 },
          { x: 170.4, y: 186.4, name: "AMMAN", r: 2, fs: 7 },
          { x: 175.6, y: 164.1, name: "DAMASCUS", r: 2, fs: 7 },
          { x: 288.7, y: 423.6, name: "SANAA", r: 2, fs: 7 },
          { x: 494.1, y: 305.9, name: "MUSCAT", r: 2, fs: 7 },
          { x: 645.3, y: 149.6, name: "KABUL", r: 3, fs: 8, critical: true },
          { x: 700.6, y: 161.6, name: "ISLAMABAD", r: 2, fs: 7 },
          { x: 297.6, y: 46.9, name: "TBILISI", r: 2, fs: 7 },
          { x: 369.6, y: 65.6, name: "BAKU", r: 2, fs: 7 },
          { x: 293.1, y: 68.9, name: "YEREVAN", r: 2, fs: 7 },
        ].map((c, i) => (
          <g key={`city${i}`} fontFamily="monospace">
            {c.critical && (
              <circle cx={c.x} cy={c.y} r={c.r} fill="none" stroke="#e74c3c" strokeWidth={0.8} opacity={0.3}>
                <animate attributeName="r" from={c.r} to={c.r * 2.5} dur="2s" repeatCount="indefinite" />
                <animate attributeName="opacity" from="0.4" to="0" dur="2s" repeatCount="indefinite" />
              </circle>
            )}
            <circle cx={c.x} cy={c.y} r={c.r} fill={c.critical ? "#e74c3c" : "#f39c12"} opacity={0.9} filter="url(#glow)" />
            <text x={c.x + c.r + 3} y={c.y + 3} fill="#94a3b8" fontSize={c.fs} letterSpacing={0.5}>{c.name}</text>
          </g>
        ))}

        {/* Country labels */}
        <g fontFamily="monospace" letterSpacing={2}>
          <text x={414.3} y={185.7} fill="#5a8aaa" fontSize={14} textAnchor="middle">IRAN</text>
          <text x={278.6} y={171.4} fill="#3a5068" fontSize={10} textAnchor="middle">IRAQ</text>
          <text x={300} y={307.1} fill="#3a5068" fontSize={10} textAnchor="middle">SAUDI ARABIA</text>
          <text x={157.1} y={85.7} fill="#3a5068" fontSize={9} textAnchor="middle">TURKEY</text>
          <text x={85.7} y={257.1} fill="#3a5068" fontSize={9} textAnchor="middle">EGYPT</text>
          <text x={600} y={164.3} fill="#3a5068" fontSize={8} textAnchor="middle">AFGHANISTAN</text>
          <text x={628.6} y={242.9} fill="#3a5068" fontSize={9} textAnchor="middle">PAKISTAN</text>
          <text x={328.6} y={421.4} fill="#3a5068" fontSize={8} textAnchor="middle">YEMEN</text>
          <text x={471.4} y={342.9} fill="#3a5068" fontSize={8} textAnchor="middle">OMAN</text>
          <text x={200} y={142.9} fill="#3a5068" fontSize={7} textAnchor="middle">SYRIA</text>
          <text x={178.6} y={200} fill="#3a5068" fontSize={7} textAnchor="middle">JORDAN</text>
          <text x={442.9} y={300} fill="#3a5068" fontSize={7} textAnchor="middle">UAE</text>
          <text x={335.7} y={217.1} fill="#3a5068" fontSize={6} textAnchor="middle">KUWAIT</text>
          <text x={485.7} y={71.4} fill="#3a5068" fontSize={8} textAnchor="middle">TURKMENISTAN</text>
          <text x={85.7} y={400} fill="#3a5068" fontSize={9} textAnchor="middle">SUDAN</text>
          <text x={214.3} y={485.7} fill="#3a5068" fontSize={8} textAnchor="middle">ETHIOPIA</text>
        </g>

        {/* Water body labels */}
        <g fontFamily="monospace" fill="#162a3d" fontStyle="italic" letterSpacing={1}>
          <text x={385.7} y={257.1} fontSize={8} textAnchor="middle">PERSIAN GULF</text>
          <text x={542.9} y={400} fontSize={9} textAnchor="middle">ARABIAN SEA</text>
          <text x={200} y={357.1} fontSize={8} textAnchor="middle">RED SEA</text>
          <text x={500} y={292.9} fontSize={7} textAnchor="middle">GULF OF OMAN</text>
          <text x={385.7} y={71.4} fontSize={7} textAnchor="middle">CASPIAN SEA</text>
          <text x={85.7} y={157.1} fontSize={7} textAnchor="middle">MEDITERRANEAN</text>
          <text x={328.6} y={471.4} fontSize={7} textAnchor="middle">GULF OF ADEN</text>
          <text x={157.1} y={28.6} fontSize={7} textAnchor="middle">BLACK SEA</text>
        </g>

        {/* Trade corridor overlays */}
        {TRADE_ROUTES.map((r, i) => (
          <line key={`trade${i}`} x1={r.x1} y1={r.y1} x2={r.x2} y2={r.y2}
            stroke={COLORS.trade} strokeWidth={1} opacity={0.25} strokeDasharray="6,3" />
        ))}

        {/* Interactive friction hotspots */}
        {GLOBE_HOTSPOTS.map((h, i) => (
          <g key={`hs${i}`} style={{ cursor: "pointer" }}
            onMouseEnter={() => setHovered(h.name)}
            onMouseLeave={() => setHovered(null)}
            onClick={() => {
              const key = Object.keys(COUNTRIES).find(k => COUNTRIES[k].name === h.name);
              if (key) onSelectCountry(key);
            }}>
            <circle cx={h.x} cy={h.y} r={h.temp > 75 ? 12 : 9} fill="none" stroke={h.color} strokeWidth={1} opacity={0.3}>
              <animate attributeName="r" from={h.temp > 75 ? 8 : 6} to={h.temp > 75 ? 18 : 14} dur="2s" repeatCount="indefinite" />
              <animate attributeName="opacity" from="0.4" to="0" dur="2s" repeatCount="indefinite" />
            </circle>
            <circle cx={h.x} cy={h.y} r={5} fill={h.color} filter="url(#glow)" />
            {hovered === h.name && (
              <g>
                <rect x={h.x + 10} y={h.y - 24} width={h.name.length * 9 + 40} height={38} rx={4}
                  fill={COLORS.bgCard} stroke={COLORS.borderLight} strokeWidth={0.8} opacity={0.95} />
                <text x={h.x + 18} y={h.y - 7} fill={COLORS.text} fontSize={13} fontFamily="monospace" fontWeight="600">{h.name}</text>
                <text x={h.x + 18} y={h.y + 8} fill={h.color} fontSize={11} fontFamily="monospace">{h.temp}° friction</text>
              </g>
            )}
          </g>
        ))}

        {/* Map legend */}
        <g transform="translate(530, 465)" fontFamily="monospace" fontSize={8}>
          <circle cx={5} cy={5} r={4} fill="#e74c3c" opacity={0.8} />
          <text x={14} y={8} fill="#64748b">CRITICAL</text>
          <circle cx={80} cy={5} r={3} fill="#f39c12" opacity={0.8} />
          <text x={88} y={8} fill="#64748b">ACTIVE</text>
          <rect x={135} y={2.5} width={5} height={5} fill="#f39c12" opacity={0.8} transform="rotate(45 137.5 5)" />
          <text x={146} y={8} fill="#64748b">MIL. BASE</text>
          <line x1={205} y1={5} x2={230} y2={5} stroke="#c0392b" strokeWidth={1.5} strokeDasharray="6,3" opacity={0.5} />
          <text x={236} y={8} fill="#64748b">SHIPPING</text>
        </g>

        {/* Title overlay */}
        <text x={400} y={18} textAnchor="middle" fill={COLORS.text} fontSize={16} fontWeight="700" fontFamily="sans-serif" letterSpacing={1}>GROUND TRUTH DIPLOMAT</text>
        <text x={400} y={34} textAnchor="middle" fill={COLORS.textDim} fontSize={10} fontFamily="monospace">Regional Diplomatic Friction Index — Live Monitor</text>
      </svg>
    </div>
  );
}

function CountryDashboard({ countryCode, onBack }) {
  const c = COUNTRIES[countryCode];
  if (!c) return null;
  const [activeTab, setActiveTab] = useState("overview");

  const radarData = [
    { axis: "Conflict", value: Math.min(c.conflictEvents / 200, 100) },
    { axis: "Displacement", value: c.frictionScore },
    { axis: "Governance", value: 100 - c.frictionScore * 0.6 },
    { axis: "Economic", value: c.tradeDeps.length * 25 },
    { axis: "Diplomatic", value: c.treaties.length * 20 },
    { axis: "Spoiler Risk", value: c.spoilers.length * 30 },
  ];

  return (
    <div style={{ padding: 20 }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
        <button onClick={onBack} style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, color: COLORS.textMuted, padding: "8px 16px", cursor: "pointer", borderRadius: 4, fontSize: 13, fontFamily: "monospace" }}>
          ← Globe
        </button>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 24, color: COLORS.text, fontWeight: 700 }}>{c.name}</h2>
          <span style={{ color: COLORS.textDim, fontSize: 13, fontFamily: "monospace" }}>{c.region} · {c.iso} · Pop: {c.population} · GDP: {c.gdp}</span>
        </div>
        <TemperatureGauge score={c.temperature} label={c.tempLabel} />
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 0, marginBottom: 20, borderBottom: `1px solid ${COLORS.border}` }}>
        {["overview", "trade & aid", "scenarios", "early warning"].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            style={{
              background: activeTab === tab ? COLORS.bgCard : "transparent",
              border: "none", borderBottom: activeTab === tab ? `2px solid ${COLORS.accent}` : "2px solid transparent",
              color: activeTab === tab ? COLORS.text : COLORS.textDim,
              padding: "10px 20px", cursor: "pointer", fontSize: 13, fontFamily: "monospace",
              textTransform: "uppercase", letterSpacing: "0.05em"
            }}>
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {/* Context Briefing */}
          <div style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: 20 }}>
            <h3 style={{ margin: "0 0 12px", fontSize: 14, color: COLORS.accent, fontFamily: "monospace", textTransform: "uppercase", letterSpacing: "0.05em" }}>Context Briefing</h3>
            <p style={{ color: COLORS.textMuted, fontSize: 14, lineHeight: 1.7, margin: 0 }}>{c.briefing}</p>
            <div style={{ marginTop: 16, padding: "12px 16px", background: COLORS.bgPanel, borderRadius: 4, borderLeft: `3px solid ${COLORS.info}` }}>
              <span style={{ color: COLORS.textDim, fontSize: 11, fontFamily: "monospace" }}>SOURCE: Ground Truth synthesis — World Bank, CIA Factbook, ACLED, GDELT, SIPRI</span>
            </div>
          </div>

          {/* Risk Profile Radar */}
          <div style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: 20 }}>
            <h3 style={{ margin: "0 0 12px", fontSize: 14, color: COLORS.accent, fontFamily: "monospace", textTransform: "uppercase", letterSpacing: "0.05em" }}>Risk Profile</h3>
            <ResponsiveContainer width="100%" height={220}>
              <RadarChart data={radarData}>
                <PolarGrid stroke={COLORS.border} />
                <PolarAngleAxis dataKey="axis" tick={{ fill: COLORS.textDim, fontSize: 10 }} />
                <PolarRadiusAxis tick={false} axisLine={false} domain={[0, 100]} />
                <Radar dataKey="value" stroke={COLORS.danger} fill={COLORS.danger} fillOpacity={0.15} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Regional Temperature Breakdown */}
          <div style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: 20 }}>
            <h3 style={{ margin: "0 0 16px", fontSize: 14, color: COLORS.accent, fontFamily: "monospace", textTransform: "uppercase", letterSpacing: "0.05em" }}>Regional Temperature</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <TempBar label="Diplomatic Friction" value={c.frictionScore} />
              <TempBar label="Spoiler Risk" value={c.spoilers.length * 30} />
              <TempBar label="Religious Tension" value={c.temperature * 0.4} />
              <TempBar label="Political Instability" value={c.temperature * 0.7} />
            </div>
            <div style={{ marginTop: 16 }}>
              <h4 style={{ color: COLORS.textMuted, fontSize: 12, margin: "0 0 8px", fontFamily: "monospace" }}>Religious Landscape</h4>
              <p style={{ color: COLORS.textDim, fontSize: 12, margin: "0 0 12px", lineHeight: 1.6 }}>{c.religiousLandscape}</p>
              <h4 style={{ color: COLORS.textMuted, fontSize: 12, margin: "0 0 8px", fontFamily: "monospace" }}>Political Spectrum</h4>
              <p style={{ color: COLORS.textDim, fontSize: 12, margin: 0, lineHeight: 1.6 }}>{c.politicalSpectrum}</p>
            </div>
          </div>

          {/* Spoiler Actors */}
          <div style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: 20 }}>
            <h3 style={{ margin: "0 0 16px", fontSize: 14, color: COLORS.danger, fontFamily: "monospace", textTransform: "uppercase", letterSpacing: "0.05em" }}>Spoiler Actors</h3>
            {c.spoilers.map((s, i) => (
              <div key={i} style={{ padding: "12px 16px", background: COLORS.bgPanel, borderRadius: 4, marginBottom: 10, borderLeft: `3px solid ${s.capability === "Very High" || s.capability === "High" ? COLORS.danger : COLORS.warning}` }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ color: COLORS.text, fontSize: 14, fontWeight: 600 }}>{s.name}</span>
                  <span style={{ color: COLORS.textDim, fontSize: 11, fontFamily: "monospace" }}>Backers: {s.backers}</span>
                </div>
                <div style={{ display: "flex", gap: 16, marginTop: 8 }}>
                  <StatusPill label={`CAP: ${s.capability}`} color={s.capability === "Very High" || s.capability === "High" ? COLORS.danger : COLORS.warning} />
                  <StatusPill label={`NEGOTIATE: ${s.negotiate}`} color={s.negotiate === "None" ? COLORS.danger : s.negotiate === "Low" ? COLORS.warning : COLORS.accent} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "trade & aid" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {/* Trade Dependencies */}
          <div style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: 20 }}>
            <h3 style={{ margin: "0 0 16px", fontSize: 14, color: COLORS.trade, fontFamily: "monospace", textTransform: "uppercase", letterSpacing: "0.05em" }}>Trade Dependencies</h3>
            {c.tradeDeps.map((t, i) => (
              <div key={i} style={{ padding: "12px 16px", background: COLORS.bgPanel, borderRadius: 4, marginBottom: 10, borderLeft: `3px solid ${COLORS.trade}` }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: COLORS.text, fontWeight: 600, fontSize: 14 }}>{t.partner}</span>
                  <span style={{ color: COLORS.trade, fontFamily: "monospace", fontSize: 14 }}>{t.volume}</span>
                </div>
                <span style={{ color: COLORS.textDim, fontSize: 12 }}>{t.type}</span>
              </div>
            ))}
          </div>

          {/* Aid Flows */}
          <div style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: 20 }}>
            <h3 style={{ margin: "0 0 16px", fontSize: 14, color: COLORS.aid, fontFamily: "monospace", textTransform: "uppercase", letterSpacing: "0.05em" }}>Aid Flows</h3>
            {c.aidFlows.map((a, i) => (
              <div key={i} style={{ padding: "12px 16px", background: COLORS.bgPanel, borderRadius: 4, marginBottom: 10, borderLeft: `3px solid ${COLORS.aid}` }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: COLORS.text, fontWeight: 600, fontSize: 14 }}>{a.donor}</span>
                  <span style={{ color: COLORS.aid, fontFamily: "monospace", fontSize: 14 }}>{a.amount}</span>
                </div>
                <span style={{ color: COLORS.textDim, fontSize: 12 }}>{a.type}</span>
              </div>
            ))}
          </div>

          {/* Treaties & Agreements */}
          <div style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: 20, gridColumn: "1 / -1" }}>
            <h3 style={{ margin: "0 0 16px", fontSize: 14, color: COLORS.diplomatic, fontFamily: "monospace", textTransform: "uppercase", letterSpacing: "0.05em" }}>Treaties & Diplomatic Channels</h3>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {c.treaties.map((t, i) => (
                <span key={i} style={{ padding: "6px 14px", background: COLORS.bgPanel, border: `1px solid ${COLORS.diplomatic}33`, borderRadius: 20, color: COLORS.diplomatic, fontSize: 12, fontFamily: "monospace" }}>{t}</span>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === "scenarios" && (
        <div>
          <div style={{ marginBottom: 16, padding: "12px 20px", background: COLORS.bgPanel, borderRadius: 4, borderLeft: `3px solid ${COLORS.accent}` }}>
            <span style={{ color: COLORS.textMuted, fontSize: 12, fontFamily: "monospace" }}>
              AI-GENERATED SCENARIOS — System presents options with transparent reasoning. Human always decides. Every score shows its inputs.
            </span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
            {SCENARIOS_UKR.map(s => (
              <ScenarioCard key={s.id} scenario={s} />
            ))}
          </div>
        </div>
      )}

      {activeTab === "early warning" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 16 }}>
          <div style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: 20 }}>
            <h3 style={{ margin: "0 0 4px", fontSize: 14, color: COLORS.warning, fontFamily: "monospace", textTransform: "uppercase", letterSpacing: "0.05em" }}>Convergence Detection — {c.name}</h3>
            <span style={{ color: COLORS.textDim, fontSize: 11, fontFamily: "monospace" }}>When multiple indicators spike simultaneously → automated alert</span>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={EARLY_WARNING} margin={{ top: 20, right: 20, bottom: 5, left: 0 }}>
                <XAxis dataKey="month" tick={{ fill: COLORS.textDim, fontSize: 11 }} axisLine={{ stroke: COLORS.border }} />
                <YAxis tick={{ fill: COLORS.textDim, fontSize: 11 }} axisLine={{ stroke: COLORS.border }} domain={[0, 100]} />
                <Tooltip contentStyle={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, borderRadius: 4, fontSize: 12 }} />
                <Line type="monotone" dataKey="conflict" stroke={COLORS.danger} strokeWidth={2} dot={{ r: 3 }} name="Conflict Events" />
                <Line type="monotone" dataKey="arms" stroke={COLORS.warning} strokeWidth={2} dot={{ r: 3 }} name="Arms Imports" />
                <Line type="monotone" dataKey="food" stroke="#f97316" strokeWidth={2} dot={{ r: 3 }} name="Food Prices" />
                <Line type="monotone" dataKey="displacement" stroke={COLORS.info} strokeWidth={2} dot={{ r: 3 }} name="Displacement" />
                <Line type="monotone" dataKey="governance" stroke={COLORS.accent} strokeWidth={2} dot={{ r: 3 }} name="Governance" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Alert Box */}
          <div style={{ background: COLORS.dangerDim, border: `1px solid ${COLORS.danger}44`, borderRadius: 6, padding: 20 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
              <span style={{ color: COLORS.danger, fontSize: 18 }}>⚠</span>
              <h3 style={{ margin: 0, fontSize: 14, color: COLORS.danger, fontFamily: "monospace" }}>CONVERGENCE ALERT — {c.name.toUpperCase()}</h3>
            </div>
            <p style={{ color: COLORS.textMuted, fontSize: 13, lineHeight: 1.6, margin: 0 }}>
              4 of 5 indicators trending upward simultaneously over the past 6 months. Historical pattern match: 78% correlation with escalation events within 90 days.
              Recommend review of diplomatic channels and aid allocation within current window.
            </p>
            <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
              <StatusPill label="CONFLICT ↑12%" color={COLORS.danger} />
              <StatusPill label="ARMS ↑15%" color={COLORS.warning} />
              <StatusPill label="FOOD ↑16%" color="#f97316" />
              <StatusPill label="GOVERNANCE ↓24%" color={COLORS.accent} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ScenarioCard({ scenario: s }) {
  const feasColor = s.feasibility >= 40 ? COLORS.accent : s.feasibility >= 25 ? COLORS.warning : COLORS.danger;
  const [expanded, setExpanded] = useState(false);

  return (
    <div style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: 20, display: "flex", flexDirection: "column", cursor: "pointer" }}
      onClick={() => setExpanded(!expanded)}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
        <StatusPill label={s.type} color={s.type === "Diplomatic Channel" ? COLORS.diplomatic : s.type === "Trade Bridge" ? COLORS.trade : COLORS.info} />
        <span style={{ color: COLORS.textDim, fontSize: 11, fontFamily: "monospace" }}>{s.timeline}</span>
      </div>
      <h3 style={{ margin: "0 0 10px", fontSize: 16, color: COLORS.text, fontWeight: 600 }}>{s.title}</h3>
      <p style={{ color: COLORS.textMuted, fontSize: 13, lineHeight: 1.6, margin: "0 0 16px", flex: 1 }}>{s.description}</p>

      {/* Scores */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: expanded ? 16 : 0 }}>
        <MiniStat label="Feasibility" value={`${s.feasibility}%`} color={feasColor} />
        <MiniStat label="Risk" value={s.risk} color={s.risk === "Very High" ? COLORS.danger : COLORS.warning} />
        <MiniStat label="Confidence" value={`${s.confidence}%`} color={COLORS.info} />
        <MiniStat label="Data Quality" value="High" color={COLORS.accent} />
      </div>

      {expanded && (
        <div style={{ borderTop: `1px solid ${COLORS.border}`, paddingTop: 16, marginTop: 8 }}>
          <h4 style={{ color: COLORS.textMuted, fontSize: 11, fontFamily: "monospace", margin: "0 0 8px", textTransform: "uppercase" }}>Dependencies</h4>
          {s.dependencies.map((d, i) => (
            <div key={i} style={{ color: COLORS.textDim, fontSize: 12, padding: "4px 0", paddingLeft: 12, borderLeft: `2px solid ${COLORS.border}` }}>{d}</div>
          ))}
          <h4 style={{ color: COLORS.textMuted, fontSize: 11, fontFamily: "monospace", margin: "12px 0 8px", textTransform: "uppercase" }}>Risk Factors</h4>
          {s.risks.map((r, i) => (
            <div key={i} style={{ color: COLORS.textDim, fontSize: 12, padding: "4px 0", paddingLeft: 12, borderLeft: `2px solid ${COLORS.danger}44` }}>{r}</div>
          ))}
          <h4 style={{ color: COLORS.textMuted, fontSize: 11, fontFamily: "monospace", margin: "12px 0 8px", textTransform: "uppercase" }}>Historical Precedent</h4>
          <div style={{ color: COLORS.textDim, fontSize: 12, padding: "8px 12px", background: COLORS.bgPanel, borderRadius: 4 }}>{s.precedent}</div>
        </div>
      )}

      <div style={{ marginTop: 12, textAlign: "center" }}>
        <span style={{ color: COLORS.textDim, fontSize: 10, fontFamily: "monospace" }}>{expanded ? "▲ COLLAPSE" : "▼ EXPAND DETAILS"}</span>
      </div>
    </div>
  );
}

function TempBar({ label, value }) {
  const clamped = Math.min(Math.max(value, 0), 100);
  const color = clamped >= 75 ? COLORS.danger : clamped >= 50 ? COLORS.warning : clamped >= 25 ? COLORS.info : COLORS.accent;
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ color: COLORS.textMuted, fontSize: 12, fontFamily: "monospace" }}>{label}</span>
        <span style={{ color, fontSize: 12, fontFamily: "monospace", fontWeight: 600 }}>{Math.round(clamped)}</span>
      </div>
      <div style={{ height: 6, background: COLORS.bgPanel, borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${clamped}%`, height: "100%", background: color, borderRadius: 3, transition: "width 0.8s ease" }} />
      </div>
    </div>
  );
}

function StatusPill({ label, color }) {
  return (
    <span style={{ padding: "3px 10px", background: `${color}18`, border: `1px solid ${color}44`, borderRadius: 12, color, fontSize: 10, fontFamily: "monospace", fontWeight: 600, letterSpacing: "0.03em" }}>
      {label}
    </span>
  );
}

function MiniStat({ label, value, color }) {
  return (
    <div style={{ padding: "8px 12px", background: COLORS.bgPanel, borderRadius: 4 }}>
      <div style={{ color: COLORS.textDim, fontSize: 10, fontFamily: "monospace", marginBottom: 2 }}>{label}</div>
      <div style={{ color, fontSize: 16, fontWeight: 700, fontFamily: "monospace" }}>{value}</div>
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────

export default function GroundTruthDiplomat() {
  const [view, setView] = useState("globe");
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [clock, setClock] = useState(new Date().toISOString().slice(0, 19).replace("T", " "));

  useEffect(() => {
    const t = setInterval(() => setClock(new Date().toISOString().slice(0, 19).replace("T", " ")), 1000);
    return () => clearInterval(t);
  }, []);

  return (
    <div style={{ background: COLORS.bg, color: COLORS.text, minHeight: "100vh", fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" }}>
      {/* Top Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 20px", borderBottom: `1px solid ${COLORS.border}`, background: COLORS.bgPanel }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 18, fontWeight: 800, color: COLORS.accent, fontFamily: "monospace", letterSpacing: "0.1em" }}>GT</span>
          <span style={{ color: COLORS.textDim, fontSize: 12 }}>|</span>
          <span style={{ color: COLORS.textMuted, fontSize: 13, fontWeight: 500 }}>DIPLOMAT</span>
          <span style={{ color: COLORS.textDim, fontSize: 12 }}>|</span>
          <span style={{ color: COLORS.textDim, fontSize: 11, fontFamily: "monospace" }}>Malleus Prendere LLC</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ color: COLORS.textDim, fontSize: 11, fontFamily: "monospace" }}>{clock} UTC</span>
          <div style={{ display: "flex", gap: 0 }}>
            {["globe", "dashboard", "compare"].map(v => (
              <button key={v} onClick={() => { setView(v); if (v === "globe") setSelectedCountry(null); }}
                style={{
                  background: view === v ? COLORS.accent + "22" : "transparent",
                  border: `1px solid ${view === v ? COLORS.accent : COLORS.border}`,
                  color: view === v ? COLORS.accent : COLORS.textDim,
                  padding: "5px 14px", cursor: "pointer", fontSize: 11, fontFamily: "monospace", textTransform: "uppercase"
                }}>
                {v}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div style={{ display: "flex", gap: 24, padding: "8px 20px", borderBottom: `1px solid ${COLORS.border}`, background: COLORS.bgCard }}>
        <StatusItem label="Active Hotspots" value="12" color={COLORS.danger} />
        <StatusItem label="Critical (>75°)" value="5" color={COLORS.danger} />
        <StatusItem label="Elevated (50-75°)" value="5" color={COLORS.warning} />
        <StatusItem label="Stable (<50°)" value="2" color={COLORS.accent} />
        <StatusItem label="Data Sources" value="9 active" color={COLORS.info} />
        <StatusItem label="Last Sync" value="2 min ago" color={COLORS.textDim} />
      </div>

      {/* Content */}
      {view === "globe" && !selectedCountry && (
        <GlobeView onSelectCountry={(code) => { setSelectedCountry(code); setView("dashboard"); }} />
      )}
      {(view === "dashboard" && selectedCountry) && (
        <CountryDashboard countryCode={selectedCountry} onBack={() => { setView("globe"); setSelectedCountry(null); }} />
      )}
      {view === "dashboard" && !selectedCountry && (
        <div style={{ padding: 40, textAlign: "center" }}>
          <p style={{ color: COLORS.textMuted, fontSize: 16 }}>Select a country from the globe view or choose below:</p>
          <div style={{ display: "flex", gap: 12, justifyContent: "center", marginTop: 20 }}>
            {Object.keys(COUNTRIES).map(code => (
              <button key={code} onClick={() => setSelectedCountry(code)}
                style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, color: COLORS.text, padding: "12px 24px", cursor: "pointer", borderRadius: 6, fontSize: 14 }}>
                {COUNTRIES[code].name}
                <div style={{ fontSize: 11, color: COUNTRIES[code].temperature >= 75 ? COLORS.danger : COLORS.warning, fontFamily: "monospace", marginTop: 4 }}>
                  {COUNTRIES[code].temperature}° {COUNTRIES[code].tempLabel}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
      {view === "compare" && (
        <div style={{ padding: 20 }}>
          <h2 style={{ color: COLORS.text, fontSize: 20, marginBottom: 16 }}>Scenario Comparison — Ukraine</h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
            {SCENARIOS_UKR.map(s => (
              <div key={s.id} style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: 20 }}>
                <h3 style={{ color: COLORS.text, fontSize: 15, margin: "0 0 12px" }}>{s.title}</h3>
                <CompareRow label="Type" value={s.type} />
                <CompareRow label="Feasibility" value={`${s.feasibility}%`} color={s.feasibility >= 40 ? COLORS.accent : s.feasibility >= 25 ? COLORS.warning : COLORS.danger} />
                <CompareRow label="Risk" value={s.risk} color={s.risk === "Very High" ? COLORS.danger : COLORS.warning} />
                <CompareRow label="Confidence" value={`${s.confidence}%`} color={COLORS.info} />
                <CompareRow label="Timeline" value={s.timeline} />
                <CompareRow label="Precedent" value={s.precedent.split("—")[0].trim()} />
              </div>
            ))}
          </div>
          <div style={{ marginTop: 20, padding: "12px 20px", background: COLORS.bgPanel, borderRadius: 4, borderLeft: `3px solid ${COLORS.accent}` }}>
            <span style={{ color: COLORS.textMuted, fontSize: 12, fontFamily: "monospace" }}>
              SYSTEM NOTE: Ground Truth presents ranked scenarios with transparent reasoning and source citations. The system never picks sides. Human always decides.
            </span>
          </div>
        </div>
      )}
      {view === "globe" && selectedCountry && (
        <CountryDashboard countryCode={selectedCountry} onBack={() => setSelectedCountry(null)} />
      )}

      {/* Footer */}
      <div style={{ padding: "12px 20px", borderTop: `1px solid ${COLORS.border}`, display: "flex", justifyContent: "space-between" }}>
        <span style={{ color: COLORS.textDim, fontSize: 10, fontFamily: "monospace" }}>GROUND TRUTH DIPLOMAT v2.0-prototype · Malleus Prendere LLC · SDVOSB</span>
        <span style={{ color: COLORS.textDim, fontSize: 10, fontFamily: "monospace" }}>MOCK DATA — API integration pending (NARA, UN Comtrade, WTO, OECD DAC, UNHCR)</span>
      </div>
    </div>
  );
}

function StatusItem({ label, value, color }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <span style={{ color: COLORS.textDim, fontSize: 11, fontFamily: "monospace" }}>{label}:</span>
      <span style={{ color: color || COLORS.text, fontSize: 11, fontFamily: "monospace", fontWeight: 600 }}>{value}</span>
    </div>
  );
}

function CompareRow({ label, value, color }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: `1px solid ${COLORS.border}22` }}>
      <span style={{ color: COLORS.textDim, fontSize: 12, fontFamily: "monospace" }}>{label}</span>
      <span style={{ color: color || COLORS.textMuted, fontSize: 12, fontFamily: "monospace", fontWeight: 500 }}>{value}</span>
    </div>
  );
}
